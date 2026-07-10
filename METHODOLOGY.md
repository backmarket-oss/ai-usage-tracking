# Methodology

Carbon emissions from AI inference largely come from the electricity needed to power the hardware LLMs run on.
Our approach estimates green house gases emissions by multiplying three quantities:
- number of tokens as a proxy for the compute intensity,
- model and hardware power-intensity rate to get energy consumed,
- global average electricity mix (carbon emissions per Wh).

**Orders of magnitude, not measurements.** Public research on the energy/carbon cost of LLM inference is still limited, so any estimate here requires stacking several hypotheses. Treat any final CO2/energy figures as "roughly this ballpark," not as precise numbers.

**When in doubt, worst case scenario.** Wherever the research leaves a range instead of a single answer, we pick the conservative end — we'd rather overestimate the footprint than underestimate it.

All estimates are computed locally from your Claude Code transcript files (`~/.claude/projects/**/*.jsonl`). No data is sent anywhere.

The AI industry is still largely opaque about per-query energy/carbon cost. Some hypotheses below are grounded in research; others are our own reasoning, called out explicitly.

## Hypothesis 1 — Effective tokens

Raw token counts are weighted to reflect actual compute demand:

```
effective_tokens = input_tokens        × 1.00
                 + output_tokens       × 1.00
                 + cache_write_tokens  × 1.25
                 + cache_read_tokens   × 0.10
```

- **Cache reads (0.10×) / cache writes (1.25×) — price-based hypothesis.** These match Anthropic's own pricing ratios for cache read/write vs. base input tokens, consistent across model tiers (see the [pricing table](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#pricing)). We reuse them as a proxy for relative compute cost, but we have no published benchmark confirming price is proportionate to compute-intensity.
- **Token completeness, incl. thinking tokens — unverified hypothesis.** `input_tokens`/`output_tokens` come straight from each transcript entry's `usage` object. We assume Claude Code's logged `usage` already bundles extended-thinking tokens into `output_tokens` rather than dropping them. If wrong, sessions using extended thinking would be silently undercounted.

## Hypothesis 2 — Energy

```
energy_Wh = (effective_tokens / 1000) × 3.0 Wh
```

**3.0 Wh per 1,000 effective tokens**

We derived energy-per-token from [*How Hungry is AI?* (arXiv:2505.09598)](https://arxiv.org/abs/2505.09598) research paper — which benchmarks energy across 30 commercial LLMs for three prompt sizes (short/medium/long). Energy-per-token isn't constant across those sizes: shorter prompts have a worse (higher) ratio, since fixed per-query overhead is amortized over fewer tokens. We took the short-prompt ratio — the worst case of the three — as our flat rate.

Assuming the "average query" is short is deliberately conservative, a worst-case assumption, since agentic tools typically run much larger prompts (file contents, tool output, long context), which the paper's data implies would score a *better* ratio. Net effect: biased toward overestimating energy (and CO2) for typical usage.

**Mapping the paper to today's models.** The paper's data cutoff (July 2025) predates the models Claude Code uses today, so two more hypotheses bridge that gap:
- *Price-ratio scaling*: we compare the price of the models studied in the paper to the price of today's models, and use that ratio as a proxy for relative energy cost — the same price-as-proxy logic as the cache factors above.
- *Same infrastructure*: we assume the provider runs newer models on the same hardware as at the time of the study. We believe this is conservative: if infrastructure changed, providers more likely moved to *more* efficient hardware over time, which would lower real energy-per-token below our estimate, not raise it.

## Hypothesis 3 — CO2

```
co2_inference_g = energy_Wh × 0.390      # global avg grid carbon intensity (gCO2/Wh)
co2_total_g     = co2_inference_g × 1.5  # lifecycle multiplier for embodied carbon
```

**Grid carbon intensity (0.390 gCO2/Wh)** — a commonly-cited global average for operational grid emissions. The one constant here sourced from external reference data rather than derived by us.

**Lifecycle multiplier (1.5×)** — a chain of two of our own hypotheses:
1. *Inference + training as a fixed share of lifecycle emissions.* Mistral's published [lifecycle breakdown for Large 2](https://mistral.ai/fr/news/our-contribution-to-a-global-environmental-standard-for-ai/) puts inference + training at **85.5%** of total lifecycle GHG emissions (the rest being embodied carbon: manufacturing, infrastructure, transport, end-of-life). We hypothesize this ratio generalizes to other transformer models, since no equivalent public breakdown exists for them.
2. *Inference dominates training.* Literature commonly cites inference as ~**90%** of inference+training emissions for heavily-used models — widely repeated but untraceable to a rigorous primary source. We lean on it anyway: it's what lets us generalize from inference (what tokens measure) to the full lifecycle.

Chained: inference ≈ 85.5% × 90% ≈ **77%** of total lifecycle emissions → implied multiplier ≈ 1/0.77 ≈ **1.3×**. The code uses **1.5×**, deliberately higher than that derived figure, as a conservative buffer given how little the 90%-inference-share hypothesis is backed.

## Hypothesis 4 — Cost

Calculated per-model from Anthropic's published token prices, applied separately to input/output/cache-write/cache-read tokens. Pricing table is hardcoded in `scripts/co2-tracker.py` — needs manual updates if Anthropic changes rates.

## Caveats

- **Carbon intensity is a global average** — actual intensity varies a lot by region (e.g. France ~0.06 gCO2/Wh vs US ~0.42 gCO2/Wh). Per-region configuration may come later.
- **The energy rate compresses a 65x real-world range into one flat number**, applied uniformly across model tiers. Actual figures depend on Anthropic's (undisclosed) data center infrastructure and hardware generation.
- **The lifecycle multiplier rests on a single-model generalization (Mistral Large 2) plus an unverifiable inference-share figure** — the constant most likely to be wrong, and the one we'd most welcome better data on.
- **Cost figures may lag published Anthropic prices** — update the pricing table in `scripts/co2-tracker.py` if you spot a discrepancy.
