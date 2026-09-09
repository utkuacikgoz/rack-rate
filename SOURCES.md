# Sources

Every number in `data/plans.json` and `data/models.json` traces to a record in
`data/sources.json`. This file is the human-readable version of that record.
`scripts/validate.py` fails the build if an `evidence` entry points at a source
id that is not listed here.

## DeepSWE (Datacurve)

- Repository: [github.com/datacurve-ai/deep-swe](https://github.com/datacurve-ai/deep-swe)
- Live leaderboard: [deepswe.datacurve.ai](https://deepswe.datacurve.ai/)
- License: Apache-2.0
- Used for: benchmark methodology, task count (113 tasks), and, once
  `data/models.json` is populated, model scores, cost per task at API rates,
  output tokens and agent steps.
- **Status: the live leaderboard is currently blocked by this build
  environment's network egress.** `data/models.json` ships empty as a result.
  Methodology facts above were confirmed by cloning the repository directly,
  which was reachable. See `known_gaps` in `data/plans.json` and
  CONTRIBUTING.md item 1.
- DeepSWE task content is never mirrored here. The benchmark carries a canary
  string specifically to catch that, and contamination would ruin the
  benchmark this project depends on.

## Awesome Coding Plan

- Repository: [github.com/mahonzhan/awesome-coding-plan](https://github.com/mahonzhan/awesome-coding-plan)
- License: **CC BY 4.0**
- Used for: measured monthly quotas, and their value at API rates, for
  Claude Pro, ChatGPT Plus, Ollama Pro, OpenCode Go, Kimi Code Andante, Kimi
  Code Allegretto, GLM Coding Plan Lite, GLM Coding Plan Pro, Cursor Pro's
  floor value, and GitHub Copilot Pro's floor value.

  **Required attribution, per the upstream license file:**

  > Identification of the creator: mahonzhan@gmail.com
  > License Notice: Licensed under the Creative Commons Attribution 4.0
  > International License.
  > Link to the License: https://creativecommons.org/licenses/by/4.0/

  This attribution also appears in `data/sources.json` (the `src-awesome-coding-plan`
  record) and on the site's Sources section. It must not be dropped by a
  future refactor; see CONTRIBUTING.md.

- Changes made: selected rows were converted from the source's table into
  this project's plan schema. Higher subscription tiers not directly measured
  by the source (Claude Max 5x/20x, ChatGPT Pro 20x) are this project's own
  scaling of the measured entry-tier row by the vendor's advertised
  multiplier, clearly marked `confidence: medium` and not attributed to this
  source as a measurement.

## real-api-pricing

- Repository: [github.com/FeiZhuLulu/real-api-pricing](https://github.com/FeiZhuLulu/real-api-pricing)
- License: MIT (the project's own software); the underlying third-party
  datasets it references keep their original terms, per the project's own
  `SOURCES.md`.
- Used for: credit only. This is independent prior work reaching a similar
  conclusion by a different route (per-token pricing across other
  leaderboards). No figures from it are copied into `data/plans.json`.

## Vendor pricing, search-corroborated

The following vendor pricing pages were unreachable from this build
environment (network egress blocked to their domains). The figures used from
them were corroborated through search-result summaries and third-party
coverage rather than a direct fetch, and are marked `confidence: medium` or
`low` in `data/plans.json` accordingly. A contributor without this
restriction fetching and confirming these directly is exactly the kind of PR
described in CONTRIBUTING.md.

- Claude Max plan pricing: [anthropic.com/pricing](https://www.anthropic.com/pricing)
- ChatGPT Pro plan pricing: [openai.com/chatgpt/pricing](https://openai.com/chatgpt/pricing/)
- Cursor plan pricing: [cursor.com/pricing](https://cursor.com/pricing)
- Z.ai GLM Coding Plan (international, USD): [z.ai/subscribe](https://z.ai/subscribe) — not used, see known_gaps
- Google AI Pro / AI Ultra: [gemini.google/subscriptions](https://gemini.google/subscriptions/)

## What is not here

Benchmark task content from DeepSWE is not mirrored, per its canary string
and this project's own commitment not to risk contamination. No regional or
promotional pricing is included. No affiliate links are included.
