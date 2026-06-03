#!/usr/bin/env python3
"""
Claude Code CO2 & Cost Tracker
Shows weekly carbon footprint and cost at session start.
Session-level tracking via Stop hook for the status bar.
Reads user preferences from ~/.claude/co2-tracker-config.json.
"""

import json
import os
import glob
import re
import sys
import random
import hashlib
from datetime import datetime, timedelta, timezone

# ─── Pricing (USD per 1M tokens) ────────────────────────────────────────────
# Per-model pricing (USD per 1M tokens) — extracted from Claude Code binary
MODEL_PRICING = {
    "claude-opus-4-6": {
        "input": 5.0,
        "output": 25.0,
        "cache_write": 6.25,
        "cache_read": 0.50,
    },
    "claude-opus-4-5-20251101": {
        "input": 5.0,
        "output": 25.0,
        "cache_write": 6.25,
        "cache_read": 0.50,
    },
    "claude-opus-4-1-20250805": {
        "input": 15.0,
        "output": 75.0,
        "cache_write": 18.75,
        "cache_read": 1.50,
    },
    "claude-opus-4-20250514": {
        "input": 15.0,
        "output": 75.0,
        "cache_write": 18.75,
        "cache_read": 1.50,
    },
    "claude-sonnet-4-6": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.30,
    },
    "claude-sonnet-4-5-20250929": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.30,
    },
    "claude-sonnet-4-20250514": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.30,
    },
    "claude-3-7-sonnet-20250219": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.30,
    },
    "claude-3-5-sonnet-20241022": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.30,
    },
    "claude-haiku-4-5-20251001": {
        "input": 1.0,
        "output": 5.0,
        "cache_write": 1.25,
        "cache_read": 0.10,
    },
    "claude-3-5-haiku-20241022": {
        "input": 0.80,
        "output": 4.0,
        "cache_write": 1.00,
        "cache_read": 0.08,
    },
}

# Tier-level fallback pricing (for unknown models)
TIER_PRICING = {
    "opus": {"input": 5.0, "output": 25.0, "cache_write": 6.25, "cache_read": 0.50},
    "sonnet": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
    "haiku": {"input": 1.0, "output": 5.0, "cache_write": 1.25, "cache_read": 0.10},
}

# ─── CO2 Constants ───────────────────────────────────────────────────────────
WH_PER_1K_TOKENS = 3.0
CACHE_READ_COMPUTE_FACTOR = 0.10
CACHE_WRITE_COMPUTE_FACTOR = 1.25
CARBON_INTENSITY = 0.390
LIFECYCLE_MULTIPLIER = 1.5

# ─── Equivalences (gCO2 per unit) ────────────────────────────────────────────
EQUIVALENCES = [
    ("km driven", 120.0, "🚗"),
    ("phone charges", 8.22, "📱"),
    ("Google searches", 0.2, "🔍"),
    ("hours of Netflix", 36.0, "📺"),
    ("cups of coffee (production)", 21.0, "☕"),
    ("hours of LED bulb", 10.0, "💡"),
    ("slices of bread baked", 5.0, "🍞"),
    ("minutes of hot shower", 10.0, "🚿"),
    ("bananas grown", 8.0, "🍌"),
]

FUN_FACTS = [
    "Fun fact: prompt caching saved you {cache_pct}% of compute. Nice.",
    "Your AI carbon footprint this week is roughly {bananas} banana{s} worth of CO2. Yes, bananas have a carbon footprint.",
    "Plot twist: the energy to power this week could also toast {toast:.1f} slices of bread.",
    "Cache hits are the recycling of the AI world — same result, way less energy.",
    "That's about {searches:.0f} Google searches worth of CO2. You probably Googled more than that today.",
    "If Claude ran on hamster wheels, this week would need {hamsters:.0f} hamster-hours. (We looked it up.)",
    "The cache saved you ~{cache_saved_kg:.0f}kgCO2e this week. Not bad for doing literally nothing.",
    "Your weekly AI footprint: {co2_kg:.0f}kgCO2e. A single email with an attachment? ~50g. You're fine.",
    "Caching is basically your AI carpooling. {cache_pct}% of tokens hitched a ride this week.",
    "This is equivalent to driving {km:.3f} km. You probably walked further to get coffee.",
]

TIER_LABELS = {"opus": "Opus", "sonnet": "Sonnet", "haiku": "Haiku"}


MODEL_ICONS = {"opus": "🏭", "sonnet": "⚙️", "haiku": "🌱"}


def format_model_name(model: str) -> str:
    """Format a model ID into a short human-readable label, e.g. '⚙️ Sonnet 4.6'."""
    m = model.lower()
    if "opus" in m:
        tier, icon = "Opus", MODEL_ICONS["opus"]
    elif "haiku" in m:
        tier, icon = "Haiku", MODEL_ICONS["haiku"]
    else:
        tier, icon = "Sonnet", MODEL_ICONS["sonnet"]

    # New format with major.minor: claude-{tier}-{major}-{minor} or ...-{minor}-{date}
    match = re.search(r"claude-(?:opus|sonnet|haiku)-(\d+)-(\d{1,2})(?:-\d+)?$", model)
    if match:
        return f"{icon} {tier} {match.group(1)}.{match.group(2)}"

    # New format major only: claude-{tier}-{major}-{date8}
    match = re.search(r"claude-(?:opus|sonnet|haiku)-(\d+)-\d{8}$", model)
    if match:
        return f"{icon} {tier} {match.group(1)}"

    # Legacy format: claude-{major}-{minor}-{tier}-{date}
    match = re.search(r"claude-(\d+)-(\d+)-(?:opus|sonnet|haiku)", model)
    if match:
        return f"{icon} {tier} {match.group(1)}.{match.group(2)}"

    return f"{icon} {tier}"

# ─── Config ──────────────────────────────────────────────────────────────────

CONFIG_PATH = os.path.expanduser("~/.claude/co2-tracker-config.json")

DEFAULT_CONFIG = {
    "show": "both",
    "display": "both",
    "frequency": "session",
    "vibe": "fun",
    "monthly_budget": None,
    "efficiency_targets": None,
}

DEFAULT_EFFICIENCY_TARGETS = {
    "haiku": {"threshold": 70, "operator": ">="},
    "sonnet": {"threshold": 25, "operator": "<="},
    "opus": {"threshold": 5, "operator": "<="},
}


def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                user_config = json.load(f)
            config.update(user_config)
        except (json.JSONDecodeError, IOError):
            pass
    return config


def should_show_welcome(config: dict) -> bool:
    freq = config.get("frequency", "session")
    if freq == "session":
        return True

    last_shown_file = os.path.expanduser("~/.claude/co2-tracker-last-shown.json")
    now = datetime.now(timezone.utc)

    try:
        with open(last_shown_file) as f:
            last = json.load(f)
        last_time = datetime.fromisoformat(last["timestamp"])
        age = now - last_time.replace(tzinfo=timezone.utc)

        if freq == "daily" and age < timedelta(hours=24):
            return False
        if freq == "weekly" and age < timedelta(days=7):
            return False
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
        pass

    try:
        with open(last_shown_file, "w") as f:
            json.dump({"timestamp": now.isoformat()}, f)
    except IOError:
        pass

    return True


# ─── Core computation ────────────────────────────────────────────────────────


def get_tier(model: str) -> str:
    m = model.lower()
    if "opus" in m:
        return "opus"
    if "sonnet" in m:
        return "sonnet"
    if "haiku" in m:
        return "haiku"
    return "sonnet"


def get_pricing(model: str) -> dict:
    """Get pricing for a model. Checks exact model ID first, then tier fallback."""
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    return TIER_PRICING.get(get_tier(model), TIER_PRICING["sonnet"])


def get_tier_pricing(tier: str) -> dict:
    """Get pricing for a tier (for 'what if' comparisons)."""
    return TIER_PRICING.get(tier, TIER_PRICING["sonnet"])


def compute_model_stats(usage: dict, model: str) -> dict:
    pricing = get_pricing(model)

    input_tok = usage.get("input_tokens", 0)
    output_tok = usage.get("output_tokens", 0)
    cache_write = usage.get("cache_creation_input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)

    cost = (
        input_tok * pricing["input"] / 1_000_000
        + output_tok * pricing["output"] / 1_000_000
        + cache_write * pricing["cache_write"] / 1_000_000
        + cache_read * pricing["cache_read"] / 1_000_000
    )

    effective = (
        input_tok * 1.0
        + output_tok * 1.0
        + cache_read * CACHE_READ_COMPUTE_FACTOR
        + cache_write * CACHE_WRITE_COMPUTE_FACTOR
    )

    raw = input_tok + output_tok + cache_read + cache_write

    return {
        "cost": cost,
        "effective_tokens": effective,
        "raw_tokens": raw,
        "input": input_tok,
        "output": output_tok,
        "cache_read": cache_read,
        "cache_write": cache_write,
    }


def tokens_to_co2(effective_tokens: float) -> dict:
    energy_wh = (effective_tokens / 1000) * WH_PER_1K_TOKENS
    co2_inference = energy_wh * CARBON_INTENSITY
    co2_total = co2_inference * LIFECYCLE_MULTIPLIER
    return {"energy_wh": energy_wh, "co2_g": co2_total}


def format_tokens(n: float) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


def make_progress_bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    filled = max(0, min(width, filled))
    return "▓" * filled + "░" * (width - filled)


def pick_equivalences(co2_g: float) -> list:
    results = []
    for name, per_unit, emoji in EQUIVALENCES:
        units = co2_g / per_unit
        if 0.001 <= units <= 10000:
            results.append((emoji, units, name))
    random.shuffle(results)
    return results[:3]


def pick_fun_fact(co2_g: float, cache_pct: float, effective: float, raw: float) -> str:
    cache_saved_kg = (tokens_to_co2(raw)["co2_g"] - co2_g) / 1000
    bananas = co2_g / 8.0
    toast = co2_g / 5.0
    searches = co2_g / 0.2
    hamsters = (effective / 1000 * WH_PER_1K_TOKENS) / 0.5
    km = co2_g / 120.0

    return random.choice(FUN_FACTS).format(
        cache_pct=f"{cache_pct:.0f}",
        bananas=f"{bananas:.1f}",
        s="" if round(bananas, 1) == 1.0 else "s",
        toast=toast,
        searches=searches,
        hamsters=hamsters,
        cache_saved_kg=cache_saved_kg,
        co2_kg=co2_g / 1000,
        km=km,
    )


def pick_status_equivalence(co2_g: float) -> str:
    good = []
    for name, per_unit, emoji in EQUIVALENCES:
        units = co2_g / per_unit
        if 0.01 <= units <= 1000:
            if units < 1:
                good.append(f"{emoji} ~{units:.2f} {name}")
            elif units < 10:
                good.append(f"{emoji} ~{units:.1f} {name}")
            else:
                good.append(f"{emoji} ~{units:.0f} {name}")
    return random.choice(good) if good else ""


def get_grade(objectives_met: int) -> str:
    return {3: "A", 2: "B", 1: "C", 0: "D"}.get(objectives_met, "D")


# ─── Cache ───────────────────────────────────────────────────────────────────

CACHE_PATH = os.path.expanduser("~/.claude/co2-tracker-cache.json")


def get_files_fingerprint(files: list) -> str:
    parts = []
    for f in sorted(files):
        try:
            parts.append(f"{f}:{os.path.getmtime(f):.0f}")
        except OSError:
            parts.append(f)
    return hashlib.md5("\n".join(parts).encode()).hexdigest()


def load_cache(files: list) -> dict | None:
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH) as f:
            cache = json.load(f)
        cache_time = datetime.fromisoformat(cache["timestamp"])
        age = datetime.now(timezone.utc) - cache_time.replace(tzinfo=timezone.utc)
        if age < timedelta(hours=1) and cache.get(
            "fingerprint"
        ) == get_files_fingerprint(files):
            return cache["data"]
    except (json.JSONDecodeError, IOError, KeyError, ValueError):
        pass
    return None


def save_cache(data: dict, files: list):
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "fingerprint": get_files_fingerprint(files),
                    "data": data,
                },
                f,
            )
    except IOError:
        pass


def load_weekly_cache() -> dict | None:
    """Load weekly cache without validation — just for reading the total."""
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH) as f:
            cache = json.load(f)
        return cache.get("data")
    except (json.JSONDecodeError, IOError):
        return None


# ─── Session tracking ────────────────────────────────────────────────────────

SESSION_CACHE_PATH = os.path.expanduser("~/.claude/co2-session-current.json")


def scan_session(transcript_path: str) -> dict:
    """Scan a single session transcript. Deduplicates by message ID."""
    seen_msg_ids = set()
    last_model = ""
    total = {
        "cost": 0,
        "effective": 0,
        "raw": 0,
        "calls": 0,
        "input": 0,
        "output": 0,
        "cache_read": 0,
        "cache_write": 0,
    }

    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get("type") != "assistant":
                    continue
                msg = d.get("message", {})

                # Deduplicate: each API response is split into multiple JSONL
                # entries (one per content block), all sharing the same message ID.
                msg_id = msg.get("id", "")
                if msg_id:
                    if msg_id in seen_msg_ids:
                        continue
                    seen_msg_ids.add(msg_id)

                model = msg.get("model", "")
                if model in ("", "<synthetic>", "unknown"):
                    continue
                usage = msg.get("usage", {})
                if not usage:
                    continue

                stats = compute_model_stats(usage, model)
                for k in (
                    "cost",
                    "effective",
                    "raw",
                    "input",
                    "output",
                    "cache_read",
                    "cache_write",
                ):
                    total[k] += stats.get(k, stats.get(k + "_tokens", 0))
                total["calls"] += 1
                last_model = model
    except (OSError, IOError):
        pass

    return total, last_model


def handle_stop_hook():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        return

    transcript_path = hook_input.get("transcript_path", "")
    session_id = hook_input.get("session_id", "")
    if not transcript_path:
        return

    total, last_model = scan_session(transcript_path)
    co2 = tokens_to_co2(total["effective"])

    try:
        with open(SESSION_CACHE_PATH, "w") as f:
            json.dump(
                {
                    "session_id": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "total": total,
                    "co2_g": co2["co2_g"],
                    "energy_wh": co2["energy_wh"],
                    "dominant_model": last_model,
                },
                f,
            )
    except IOError:
        pass


def load_session_stats() -> dict | None:
    if not os.path.exists(SESSION_CACHE_PATH):
        return None
    try:
        with open(SESSION_CACHE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


# ─── Scan (weekly) ───────────────────────────────────────────────────────────


def _scan_jsonl_files(cutoff: datetime, jsonl_files: list) -> dict:
    """Scan JSONL files since cutoff. Deduplicates by message ID."""
    seen_msg_ids = set()
    models = {}
    total = {
        "cost": 0,
        "effective": 0,
        "raw": 0,
        "calls": 0,
        "input": 0,
        "output": 0,
        "cache_read": 0,
        "cache_write": 0,
    }

    for fpath in jsonl_files:
        try:
            with open(fpath, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if d.get("type") != "assistant":
                        continue
                    ts_str = d.get("timestamp", "")
                    if not ts_str:
                        continue
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if ts < cutoff:
                        continue

                    msg = d.get("message", {})

                    # Deduplicate: each API response is split into multiple JSONL
                    # entries (one per content block), all sharing the same message ID.
                    # Sub-agent messages also appear in both parent and child JSONLs.
                    msg_id = msg.get("id", "")
                    if msg_id:
                        if msg_id in seen_msg_ids:
                            continue
                        seen_msg_ids.add(msg_id)
                    model = msg.get("model", "")
                    if model in ("", "<synthetic>", "unknown"):
                        continue
                    usage = msg.get("usage", {})
                    if not usage:
                        continue

                    stats = compute_model_stats(usage, model)
                    tier = get_tier(model)

                    if model not in models:
                        models[model] = {
                            "cost": 0,
                            "effective": 0,
                            "raw": 0,
                            "calls": 0,
                            "tier": tier,
                            "input": 0,
                            "output": 0,
                            "cache_read": 0,
                            "cache_write": 0,
                        }
                    m = models[model]
                    for k in (
                        "cost",
                        "effective",
                        "raw",
                        "input",
                        "output",
                        "cache_read",
                        "cache_write",
                    ):
                        m[k] += stats.get(k, stats.get(k + "_tokens", 0))
                    m["calls"] += 1

                    for k in (
                        "cost",
                        "effective",
                        "raw",
                        "input",
                        "output",
                        "cache_read",
                        "cache_write",
                    ):
                        total[k] += stats.get(k, stats.get(k + "_tokens", 0))
                    total["calls"] += 1
        except (OSError, IOError):
            continue

    return {"models": models, "total": total}


def scan_weekly_usage() -> dict:
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    projects_dir = os.path.expanduser("~/.claude/projects")
    jsonl_files = glob.glob(f"{projects_dir}/**/*.jsonl", recursive=True)

    cached = load_cache(jsonl_files)
    if cached:
        return cached

    result = _scan_jsonl_files(seven_days_ago, jsonl_files)
    save_cache(result, jsonl_files)
    return result


MONTHLY_CACHE_PATH = os.path.expanduser("~/.claude/co2-monthly-cache.json")


def scan_monthly_cost() -> float:
    """Scan JSONL files for the past 30 days. Returns total cost only (deduplicated)."""
    if os.path.exists(MONTHLY_CACHE_PATH):
        try:
            with open(MONTHLY_CACHE_PATH) as f:
                cache = json.load(f)
            cache_time = datetime.fromisoformat(cache["timestamp"])
            age = datetime.now(timezone.utc) - cache_time.replace(tzinfo=timezone.utc)
            if age < timedelta(hours=1):
                return cache.get("monthly_cost", 0)
        except (json.JSONDecodeError, IOError, KeyError, ValueError):
            pass

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    projects_dir = os.path.expanduser("~/.claude/projects")
    jsonl_files = glob.glob(f"{projects_dir}/**/*.jsonl", recursive=True)

    result = _scan_jsonl_files(thirty_days_ago, jsonl_files)
    total_cost = result["total"]["cost"]

    try:
        with open(MONTHLY_CACHE_PATH, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "monthly_cost": total_cost,
                },
                f,
            )
    except IOError:
        pass

    return total_cost


def load_monthly_cache() -> float:
    """Load monthly cost from cache without recomputing."""
    if os.path.exists(MONTHLY_CACHE_PATH):
        try:
            with open(MONTHLY_CACHE_PATH) as f:
                return json.load(f).get("monthly_cost", 0)
        except (json.JSONDecodeError, IOError):
            pass
    return 0


# ─── Formatting (config-aware) ───────────────────────────────────────────────


def format_welcome(data: dict, config: dict) -> str:
    total = data["total"]
    models = data["models"]
    show = config.get("show", "both")
    vibe = config.get("vibe", "fun")
    monthly_budget = config.get("monthly_budget")
    efficiency_targets = config.get("efficiency_targets")

    if not models:
        return "No Claude usage data found for the past 7 days."

    co2 = tokens_to_co2(total["effective"])
    co2_g = co2["co2_g"]
    energy_wh = co2["energy_wh"]
    cost = total["cost"]
    effective = total["effective"]
    raw = total["raw"]
    cache_pct = (total["cache_read"] / raw * 100) if raw > 0 else 0

    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("  Weekly Claude Report (past 7 days)")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    # Main stats
    if show in ("cost", "both"):
        lines.append(f"  💰 Cost:      ${cost:.2f}")
    if show in ("co2", "both"):
        lines.append(f"  ⚡ Energy:    {energy_wh / 1000:.0f} kWh")
        lines.append(f"  🌍 CO2:       {co2_g / 1000:.0f} kgCO2e")
    lines.append(
        f"  🔄 Tokens:    {format_tokens(effective)} effective ({format_tokens(raw)} raw)"
    )
    lines.append(
        f"  💾 Cache hit:  {cache_pct:.0f}% of tokens (saving ~{100 - (effective / raw * 100) if raw else 0:.0f}% compute)"
    )
    lines.append("")

    # Monthly budget bar (optional)
    if monthly_budget and show in ("cost", "both"):
        monthly_cost = scan_monthly_cost()
        budget_pct = (monthly_cost / monthly_budget * 100) if monthly_budget > 0 else 0
        bar = make_progress_bar(min(budget_pct, 100))
        status = "over budget!" if budget_pct > 100 else f"{budget_pct:.0f}%"
        lines.append(
            f"  📊 Your budget:    ${monthly_cost:.0f} / ${monthly_budget:.0f}/mo  [{bar}]  {status}"
        )
        lines.append("")

    # Equivalences
    if show in ("co2", "both") and vibe == "fun":
        equivs = pick_equivalences(co2_g)
        if equivs:
            lines.append("  That's about:")
            for emoji, units, name in equivs:
                if units < 0.01:
                    lines.append(f"    {emoji} {units:.4f} {name}")
                elif units < 1:
                    lines.append(f"    {emoji} {units:.2f} {name}")
                else:
                    lines.append(f"    {emoji} {units:.1f} {name}")
            lines.append("")

    # Model breakdown by tier
    tier_agg = {}
    for model, m in models.items():
        t = m["tier"]
        if t not in tier_agg:
            tier_agg[t] = {"cost": 0, "effective": 0, "calls": 0}
        tier_agg[t]["cost"] += m["cost"]
        tier_agg[t]["effective"] += m["effective"]
        tier_agg[t]["calls"] += m["calls"]

    sorted_tiers = sorted(tier_agg.items(), key=lambda x: x[1]["cost"], reverse=True)
    lines.append("  By model tier:")
    for tier, agg in sorted_tiers:
        pct = (agg["cost"] / cost * 100) if cost > 0 else 0
        label = TIER_LABELS.get(tier, tier)
        tier_co2 = tokens_to_co2(agg["effective"])["co2_g"]
        if show == "co2":
            lines.append(
                f"    {label:<10} ~{tier_co2 / 1000:.0f} kgCO2e  [{agg['calls']} calls]"
            )
        elif show == "cost":
            lines.append(
                f"    {label:<10} ${agg['cost']:>7.2f} ({pct:4.1f}%)  [{agg['calls']} calls]"
            )
        else:
            lines.append(
                f"    {label:<10} ${agg['cost']:>7.2f} ({pct:4.1f}%)  ~{tier_co2 / 1000:.0f} kgCO2e  [{agg['calls']} calls]"
            )
    lines.append("")

    # Efficiency grading (optional)
    if efficiency_targets and show in ("cost", "both"):
        objectives_met = 0
        grade_lines = []
        for tier in ["haiku", "sonnet", "opus"]:
            target = efficiency_targets.get(tier)
            if not target:
                continue
            tier_cost = tier_agg.get(tier, {}).get("cost", 0)
            pct = (tier_cost / cost * 100) if cost > 0 else 0
            threshold = target["threshold"]
            operator = target["operator"]

            if operator == ">=":
                meets = pct >= threshold
                bar_pct = (pct / threshold * 100) if threshold > 0 else 0
            else:
                meets = pct <= threshold
                bar_pct = (pct / threshold * 100) if threshold > 0 else 0

            if meets:
                objectives_met += 1

            bar = make_progress_bar(min(bar_pct, 100))
            status = "✓" if meets else "✗"
            label = TIER_LABELS.get(tier, tier)
            grade_lines.append(
                f"    {label:<10} {bar} {pct:5.1f}% (target {operator}{threshold}%) {status}"
            )

        grade = get_grade(objectives_met)
        lines.append(f"  Model efficiency: {grade}")
        lines.extend(grade_lines)
        lines.append("")

    # "What if" model comparison
    lines.append("  What if you used a different model?")
    for alt_tier in ["opus", "sonnet", "haiku"]:
        alt_pricing = get_tier_pricing(alt_tier)
        alt_cost = (
            total["input"] * alt_pricing["input"] / 1_000_000
            + total["output"] * alt_pricing["output"] / 1_000_000
            + total["cache_write"] * alt_pricing["cache_write"] / 1_000_000
            + total["cache_read"] * alt_pricing["cache_read"] / 1_000_000
        )
        alt_label = TIER_LABELS[alt_tier]
        cost_diff = alt_cost - cost
        cost_arrow = "+" if cost_diff > 0 else ""
        if abs(cost_diff) < 0.01:
            lines.append(f"    {alt_label:<10} ${alt_cost:>7.2f}  (current)")
        else:
            pct_diff = (cost_diff / cost * 100) if cost > 0 else 0
            lines.append(
                f"    {alt_label:<10} ${alt_cost:>7.2f}  ({cost_arrow}{pct_diff:.0f}%)"
            )
    lines.append("")

    # Fun fact
    if vibe == "fun":
        lines.append(f"  💬 {pick_fun_fact(co2_g, cache_pct, effective, raw)}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(lines)


def format_status_line(config: dict) -> str:
    """Status bar: session stats + optional weekly budget."""
    show = config.get("show", "both")
    vibe = config.get("vibe", "fun")
    monthly_budget = config.get("monthly_budget")

    session = load_session_stats()
    if not session:
        return "No session data yet"

    co2_g = session.get("co2_g", 0)
    cost = session.get("total", {}).get("cost", 0)
    calls = session.get("total", {}).get("calls", 0)

    dominant_model = session.get("dominant_model", "")

    parts = []
    if dominant_model:
        parts.append(format_model_name(dominant_model))
    if show in ("co2", "both"):
        parts.append(f"🌍 {co2_g / 1000:.0f} kgCO2e")
    if show in ("cost", "both"):
        parts.append(f"💰 ${cost:.2f}")
    parts.append(f"[{calls} turns]")

    # Monthly budget from cached monthly data
    if monthly_budget and show in ("cost", "both"):
        monthly_cost = load_monthly_cache()
        if monthly_cost > 0:
            budget_pct = (
                (monthly_cost / monthly_budget * 100) if monthly_budget > 0 else 0
            )
            parts.append(f"📊 {budget_pct:.0f}% of ${monthly_budget:.0f}/mo")

    if vibe == "fun" and show in ("co2", "both") and co2_g > 0:
        equiv = pick_status_equivalence(co2_g)
        if equiv:
            parts.append(equiv)

    return " | ".join(parts)


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    if "--stop-hook" in sys.argv:
        handle_stop_hook()
        return

    config = load_config()

    if "--status-line" in sys.argv:
        if config.get("display") in ("statusbar", "both"):
            print(format_status_line(config))
        else:
            print("")
    else:
        if not should_show_welcome(config):
            print(json.dumps({"systemMessage": ""}))
            return
        data = scan_weekly_usage()
        msg = format_welcome(data, config)
        print(json.dumps({"systemMessage": msg}))


if __name__ == "__main__":
    main()
