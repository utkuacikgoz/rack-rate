# Rack Rate

**A hotel's rack rate is the price on the back of the door. Nobody pays it.**

API list pricing is the same instrument. Published, high, and quietly discounted for almost everyone who walks in.

**[rackrate.dev](https://rackrate.dev)** · [method](#the-method) · [sources](SOURCES.md) · [contributing](CONTRIBUTING.md)

[DeepSWE](https://deepswe.datacurve.ai/) is a public coding benchmark: 113 original tasks, hand written verifiers, no contamination. It prices every model at API list rates.

Nobody buys coding tokens at list rates. People pay $10 to $200 a month and work inside a quota.

This repo joins the two: same scores, real prices, every number cited.

## What it shows

28 models, 16 plans, 178 model-and-plan pairs that are actually possible (a
Claude subscription cannot run a Kimi model, and `data/plans.json`'s
`model_scope` field enforces that).

| Model | Score | API list | Cheapest usable plan | |
|---|---|---|---|---|
| gpt-6-astra | 74.12% | $5.67 | $0.130 on ChatGPT Pro 20x | 44x |
| claude-opus-5 | 73.65% | $10.43 | $0.082 on Claude Max 20x | 127x |
| deepseek-v4-flash | 53.32% | $0.09 | $0.030 on Ollama Pro | 3x |
| gemini-3.1-pro-preview | 11.73% | $1.72 | $0.575 on Ollama Pro | 3x |

The cheapest route on the page, deepseek-v4-flash on Ollama Pro, is also
mid-pack on score (53%) — the frontier here isn't as one-sided as "cheap or
good, pick one." gemini-3.1-pro-preview shows the other end: a discounted
route that still barely solves anything. See the chart's
list-price-to-subscription flight for the full picture across all 28 models.

## Where this stands right now

`data/plans.json` has 16 real, cited subscription plans, and `data/models.json`
has 28 real models from a DeepSWE results snapshot (the v1.1 scoring run,
dated 2026-09-03).

`deepswe.datacurve.ai`, the live leaderboard, is still blocked by this build
environment's network egress, so the snapshot in `data/models.json` was
supplied directly rather than fetched here. `scripts/fetch_deepswe.py`'s
endpoint and field mapping are now confirmed against that exact data (a real
fetch outside this build environment matched it exactly), so running it from
an unblocked network is a plain refresh, not a fix. See `src-deepswe-data` in
`data/sources.json`. gpt-6-astra's cost figures are DeepSWE's own disclosed
*expected launch pricing*, not confirmed GA API pricing; treat them as
provisional. See CONTRIBUTING.md.

## The method

```
cost_per_task = price_per_month / tasks_per_month
```

`tasks_per_month` comes from whichever unit the vendor publishes.

| Quota model | Conversion | Used by |
|---|---|---|
| `budget` | quota in dollars / DeepSWE cost per task | Claude, ChatGPT, Cursor, OpenCode, Ollama, GitHub Copilot |
| `credits` | weighted token sum / 10,000, Z.ai's own formula | GLM (international plan, not yet priced, see known_gaps) |
| `requests` | request quota / agent steps per task | Kimi, GLM (domestic plan, priced here by request count) |
| `tokens_total` | token quota / tokens per task | cross-check only |

Credit and request plans in this repo were measured directly by
[Awesome Coding Plan](https://github.com/mahonzhan/awesome-coding-plan), CC BY
4.0. Higher subscription tiers not directly measured (Claude Max 5x/20x,
ChatGPT Pro) are this project's own scaling of the measured entry tier by the
vendor's advertised multiplier: a promise carried through arithmetic, marked
`confidence: medium`, not a second measurement.

## Throughput, not just price

A price per task hides the cap. `days_for_full_run` is how long all 113 tasks
would take, limited by whichever cap bites first: the monthly quota or the
rolling five hour window (recorded for Claude's plans, where the source
measured it directly). This column only populates once `data/models.json` has
a real cost-per-task figure to divide the quota by.

## Where this is weakest

- **DeepSWE model data is a real snapshot, not a live pull.** See "Where this
  stands right now" above. The fetch script itself is confirmed working, it
  just hasn't been re-run from a network that can reach the site.
- **Only the best reasoning-effort configuration per model is captured.**
  DeepSWE published more configurations than that (some models were run at
  up to five effort levels — low, medium, high, xhigh, max); this repo keeps
  only the highest-scoring one per model, per CONTRIBUTING item 7.
- **gpt-6-astra's pricing is provisional.** DeepSWE scored it against its own
  disclosed *expected launch pricing*, not a confirmed GA rate card. Treat its
  cost-per-task figures as a forecast, not a receipt.
- **Two models ship with `provider: "Unknown"`.** muse-spark-1.1 and
  muse-spark-1.2 appear in the DeepSWE snapshot with no vendor identified
  anywhere in the response. Rather than guess, this repo ships them with an
  honest "Unknown" rather than a made-up company name.
- **Google.** AI Pro and AI Ultra are metered in AI credits with no published
  conversion to tokens or dollars anywhere found. AI Pro is priced as a
  placeholder, drawn hollow once the chart has data. AI Ultra's price itself
  is disputed across sources and is not priced at all; see `known_gaps`.
- **Z.ai's real credit formula.** The GLM plans priced here are the
  CNY-denominated domestic product, priced by measured request count. Z.ai's
  international USD plan and its published credit formula (weighted token
  sum, output weight unconfirmed) are not yet priced; see `known_gaps`.
- **Cursor's Pro+ and Ultra tiers, and Ollama's Max and Team tiers.** Only
  found via third-party aggregators, not a reachable vendor page. Low
  confidence, flagged as such.

`known_gaps` in `data/plans.json` lists every route that exists and is not
priced, with the reason.

## Layout

```
data/models.json     DeepSWE snapshot: 28 models, best config per model, dated 2026-09-03 (v1.1)
data/plans.json      Plans, quota models, evidence, confidence, known_gaps
data/sources.json    Full citation record for every external dataset
data/derived.csv     Every model and plan pair, cheapest first. Generated.
data/derived.json    The same, plus best routes and the cross-check. Generated.
scripts/fetch_deepswe.py   Refresh models.json from the live leaderboard. Endpoint confirmed working.
scripts/validate.py        Schema, sanity and citation checks. Runs in CI.
scripts/compute.py         Join, derive, write derived.* and site/index.html
scripts/make_og.py         Render the social card from derived.json
site/template.html   The page, with a data placeholder
site/index.html      Built output, one self contained file. Generated.
```

## Build

No dependencies for the core pipeline. Python 3.9 or newer.

```bash
python scripts/fetch_deepswe.py --diff   # see what moved upstream
python scripts/validate.py               # catch a broken plan before it ships
python scripts/compute.py                # rebuild derived.* and the site
```

CI validates then rebuilds, and fails if the committed output does not match
the source data. The site ships prebuilt, so a stale `index.html` would serve
wrong numbers quietly.

`scripts/make_og.py` regenerates the social card. It needs Pillow
(`pip install pillow`), the only dependency anywhere in this repo.

## The thing this repo actually needs

Two things, in order:

1. **A current run of `scripts/fetch_deepswe.py`.** The endpoint and field
   mapping are confirmed working; the snapshot in `data/models.json` is just
   three months old. Anyone who can reach `deepswe.datacurve.ai` can refresh
   it with `python scripts/fetch_deepswe.py`.
2. **Measured plan quotas.** Most of what is priced here is measured by one
   external contributor (Awesome Coding Plan) or scaled from their
   measurement by a vendor's advertised multiplier. If you have run a plan to
   exhaustion and counted, your number beats everything derived here.

**[Submit a measured quota](../../issues/new?template=measured-quota.yml)**

You do not need every field. Send what you have and say what you do not.
Every accepted measurement is credited to your handle in `data/sources.json`.

Other corrections are welcome too. See CONTRIBUTING.md for the fixes worth
the most, in order.

## Credit

See [SOURCES.md](SOURCES.md) for the full record. In short:

- DeepSWE methodology and licensing: Datacurve, Apache-2.0. The benchmark
  tasks are not mirrored here. DeepSWE carries a canary string and
  contamination would ruin the thing this work depends on.
- Measured quotas come from [Awesome Coding Plan](https://github.com/mahonzhan/awesome-coding-plan)
  by mahonzhan, **CC BY 4.0**. That dataset replaced the guesses in the first
  draft of this project.
- [real-api-pricing](https://github.com/FeiZhuLulu/real-api-pricing) by
  FeiZhuLulu reached a related idea first, pricing per token across other
  leaderboards. Independent work, credited here.

The join, the arithmetic and any error in it belong to this project. MIT, see
`LICENSE`.
