# Claude Code Usage Tracker

Track your personal Claude Code carbon footprint, API spending, and model efficiency — from your Claude session.

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

1. Install this skill into Claude Code
2. Run `/usage-tracking` in any Claude Code session
3. Follow the interactive onboarding (~2 minutes)

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

### Step 1 — Effective tokens

Raw token counts are weighted to reflect actual compute demand:

```
effective_tokens = input_tokens        × 1.00
                 + output_tokens       × 1.00
                 + cache_write_tokens  × 1.25
                 + cache_read_tokens   × 0.10
```

- **Cache reads (0.10×)**: the KV cache is already computed and stored; retrieval requires far less GPU work than a full forward pass.
- **Cache writes (1.25×)**: writing to the prompt cache carries overhead on top of the normal input computation.

### Step 2 — Energy

```
energy_Wh = (effective_tokens / 1000) × 3.0 Wh
```

We use **3.0 Wh per 1,000 effective tokens** as the inference energy rate for large language models running in data center conditions.

### Step 3 — CO2

```
co2_inference_g = energy_Wh × 0.390      # global avg grid carbon intensity (gCO2/Wh)
co2_total_g     = co2_inference_g × 1.5  # lifecycle multiplier for embodied carbon
```

- **0.390 gCO2/Wh**: global average grid carbon intensity (operational emissions only).
- **1.5× lifecycle multiplier**: accounts for embodied carbon — hardware manufacturing, transport, and end-of-life disposal — on top of operational emissions.

### Step 4 — Cost

Cost is calculated per-model using Anthropic's published token prices, applied separately to input, output, cache-write, and cache-read tokens. The pricing table is hardcoded in `scripts/co2-tracker.py` and will need updating if Anthropic changes rates.

### Caveats

- **Carbon intensity is a global average.** Actual intensity varies significantly by region (e.g. France ~0.06 gCO2/Wh vs US ~0.42 gCO2/Wh). A future version may support per-region configuration.
- **Energy and lifecycle constants are estimates** based on published research. Actual figures depend on the specific data center infrastructure and hardware generation Anthropic uses, which is not publicly disclosed.
- **Cost figures may lag** publicly listed Anthropic prices. If you notice a discrepancy, update the pricing table at the top of `scripts/co2-tracker.py`.
