# Claude Code Usage Tracker

Track your personal Claude Code carbon footprint and model efficiency — from your Claude session.

## Motivation


A coding agent is a genuinely useful tool, but has a cost that today's tooling does not surface: carbon emissions.

The AI industry as a whole remains largely opaque about the environmental footprint of a single inference call, so there's no authoritative number to just look up.

This tool provides carbon emissions estimations directly in your terminal, allowing for a deliberate carbon-aware usage.

The numbers aren't precise measurements. They're the best approximation we could build from public research, and the hypothesis we did to bridge the gaps. We documented the hypothesis so they can be checked and improved. See [METHODOLOGY.md](METHODOLOGY.md).

## Features

- **Weekly report** at session start: cost, energy, CO2, token counts, and cache efficiency
- **Live status bar** updated after every response with session-level stats
- **"What if" model comparison** — shows how your cost and CO2 would change with a different model tier
- **Monthly budget tracking** with a progress bar
- **Model efficiency grading** (A–D) against configurable Haiku/Sonnet/Opus targets
- **Fun mode**: real-world CO2 comparisons (coffee cups, Google searches, km driven) and a rotating fun fact each session

## Requirements

- [Claude Code](https://claude.ai/code) installed
- Python 3 (standard library only — no `pip install` needed)

## Installation

```bash
claude plugins marketplace add backmarket-oss/ai-usage-tracking
claude plugins install usage-tracking@ai-usage-tracking
```

Then run `/usage-tracking` in any Claude Code session to follow the interactive onboarding (~2 minutes).

To update your preferences at any time, run `/usage-tracking` again.

## Configuration options

The onboarding walks you through these settings:

| Option | Choices | Default |
|---|---|---|
| What to track | CO2 only, Cost only, Both | Both |
| Where to show | Welcome message, Status bar, Both | Both |
| Frequency | Every session, Daily, Weekly | Every session |
| Vibe | Fun (comparisons + facts), Minimal | Fun |
| Monthly budget | Any USD amount | None |
| Model efficiency goals | Default / Balanced / Power user / Custom | None |

Settings are saved to `~/.claude/co2-tracker-config.json`.

## Sample output

**Welcome message (full weekly report):**

```
  Weekly Claude Report (past 7 days)
  ────────────────────────────────────────────

  💰 Cost:      $15.30
  ⚡ Energy:    12 kWh
  🌍 CO2:       7 kgCO2e
  🔄 Tokens:    4.1M effective (15.5M raw)
  💾 Cache hit:  86% of tokens (saving ~74% compute)

  🏦 Your budget:   $48 / $200/mo  [████░░░░░░░░░░░░░░░░]  24%

  That's about:
    🚿 715.1 minutes of hot shower
    🍞 1430.2 slices of bread baked
    💡 715.1 hours of LED bulb

  By model tier:
    Sonnet     $  13.49 (88.2%)  ~6 kgCO2e  [285 calls]
    Opus       $   1.56 (10.2%)  ~0 kgCO2e  [10 calls]
    Haiku      $   0.24 ( 1.6%)  ~0 kgCO2e  [21 calls]

  Model efficiency: D

  What if you used a different model?
    Opus       $  25.27  (+65%)
    Sonnet     $  15.16   (-1%)
    Haiku      $   5.05  (-67%)

  💬 Plot twist: the energy to power this week could also toast 1430.2 slices of bread.
```

**Status bar (live session stats):**

```
🌍 2.9kg CO2 | 💰 $77.74 | [305 turns] | 🍞 ~400 slices of bread
```

## Methodology

All estimates are computed locally from your Claude Code transcript files (`~/.claude/projects/**/*.jsonl`). No data is sent anywhere.

The full derivation — effective tokens, energy, CO2, and cost — along with the research and hypotheses behind each constant, lives in [METHODOLOGY.md](METHODOLOGY.md). Some of those constants are the author's own reasoned estimates rather than settled science — if you have better data, open an issue or PR.
