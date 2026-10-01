# Rack Rate

Compare API spending and subscription estimates for your AI coding workload.

**[Live site](https://rack-rate-flax.vercel.app/)** · [Sources](SOURCES.md) · [Contributing](CONTRIBUTING.md)

Rack Rate combines a DeepSWE benchmark snapshot with cited subscription quotas. Enter a monthly budget and expected task count to compare estimated spending. Recommendations rank the highest-scoring benchmark configurations that fit both your budget and estimated capacity; ties prefer lower monthly spending. Alternatives show different models.

## What the numbers mean

- **Benchmark score:** measured with mini-swe-agent on 113 coding tasks, not separately on every subscription's tool. Highest-scoring reasoning configuration per model; other measured configurations appear in details.
- **API estimate:** benchmark median cost per attempt × requested tasks. Real workloads and expensive outliers can cost more; this is not a forecast based on a workload mean.
- **Your subscription cost per task:** monthly subscription price ÷ tasks you actually expect to run. Unused quota does not reduce the bill.
- **At full use / task:** monthly price ÷ modeled maximum task capacity. This is an optimistic utilization scenario, not the price everyone pays.
- **Break-even:** monthly price ÷ benchmark API cost, rounded up to whole tasks. It only matters if the plan can support that workload and the route is available.
- **Quota-equivalent days:** 113 tasks divided by steady-state daily quota capacity, using a 30-day month and recorded rolling caps. It does not estimate elapsed completion time, initial allowance, actual reset scheduling, run duration or concurrency.

## Evidence and eligibility

`model_scope` contains explicit candidate model IDs; it does **not** establish access. New benchmark models do not silently join every aggregator plan. `model_access` records source-observed or source-listed model access with its citation and date. Access is unverified otherwise.

By default, the site excludes unverified model access, low-confidence plan estimates, and China-only plans. Users can explicitly include exploratory estimates and China-only plans. Other regional restrictions still require checking the vendor. Historical evidence is not a guarantee of present-day availability or support for a particular reasoning setting.

Only three model-plan combinations in the current snapshot have observed or source-listed access evidence. Other calculated combinations remain available for explicitly enabled exploration. The access catalog needs further primary-source verification; missing evidence is not replaced with a guessed catalog.

Quota evidence and conversion confidence are separate. A quota measured on one model is downgraded when applied to another. Higher-tier multipliers and API-equivalent conversion assumptions remain estimates. The cross-check compares two conversions of shared data; its unresolved disagreement is not independent validation.

`data/models.json` records the benchmark's generated timestamp; the page displays it. The current snapshot was generated on 2026-09-22. Source retrieval dates are recorded separately. Known gaps, including unpriced plans, are visible in the method section.

## Build and test

The core pipeline needs Python 3.9+. DOM and decision regression tests use Node 22 and jsdom as a development dependency. The deployed site has no npm runtime dependencies.

```sh
npm ci
python scripts/validate.py
python scripts/compute.py
python -m unittest discover -s tests
npm test
```

GitHub Actions runs these checks on pull requests and main, and fails if regenerated `data/derived.csv`, `data/derived.json`, or `site/index.html` differs from committed output. Vercel serves the prebuilt `site` directory.

To refresh the benchmark from a network that can reach it:

```sh
python scripts/fetch_deepswe.py --diff
python scripts/fetch_deepswe.py
```

Review refreshed data before committing. The fetch does not verify plan catalogs or refresh subscription quotas.

## Layout

- `data/models.json`: benchmark snapshot and effort variants.
- `data/plans.json`: candidate IDs, access evidence, quota methods, regions and known gaps.
- `data/sources.json`: citation and retrieval records.
- `scripts/compute.py`: generates derived data and the page.
- `scripts/validate.py`: validates data and evidence references.
- `site/template.html`: page source.
- `site/decision.js`: workload calculations shared with tests.
- `tests/`: Python arithmetic/evidence checks and Node decision/DOM regression tests.

## Credit

Benchmark methodology and data: [Datacurve DeepSWE](https://github.com/datacurve-ai/deep-swe), Apache-2.0. Quota measurements: [mahonzhan's Awesome Coding Plan](https://github.com/mahonzhan/awesome-coding-plan), CC BY 4.0. Related independent work: [FeiZhuLulu's real-api-pricing](https://github.com/FeiZhuLulu/real-api-pricing). Full attribution and source limitations are in [SOURCES.md](SOURCES.md).

The calculations and any errors in them belong to this project. MIT licensed. Benchmark task content is not mirrored here.
