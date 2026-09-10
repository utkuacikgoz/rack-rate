# Contributing to Rack Rate

Plan pricing moves faster than one person can track. That is why this is a repo and not a blog post.

## The fixes worth the most, in order

1. **A measured month on a tier nobody has measured.** Claude Pro and ChatGPT Plus have real numbers. Max 5x, Max 20x, Pro 5x and Pro 20x scale off them by the multiplier the vendor advertises. One measured Max month replaces four rows of arithmetic. If you have run a tool that reports what your month would have cost at API rates, that number is worth more than everything derived here.
2. **Anything at all for Google.** AI Pro and AI Ultra are metered in credits with no published conversion. Those rows are placeholders. They are the weakest numbers on the page and they are marked as such.
3. **Z.ai's real credit multipliers.** The GLM plans use Z.ai's published formula but assume the output weight equals the ratio of its output and input API rates. If the real weights appear in the docs, they drop straight into `plans.json`.
4. **Cursor's included pool per tier.** Pro is roughly its sticker price. Pro+ and Ultra are scaled from it, which is a guess.
5. **An explanation for the 1.6x cross-check gap.** Two methods disagree by a stable factor. Cache pricing is the leading suspect. Proving or killing that would tighten every budget row on the page.
6. **Missing plans.** `known_gaps` in `plans.json` lists what exists and is not priced yet, with the reason each one is missing.

## Adding or fixing a plan

Edit `data/plans.json`, run `python scripts/validate.py`, then `python scripts/compute.py`. Commit the regenerated `derived.csv`, `derived.json` and `site/index.html` with your change so the diff shows what moved.

Every plan needs:

- `price_usd_month`, US list price, monthly billing, no annual discount
- `quota_model`, one of `budget`, `credits`, `requests`, `tokens_total`
- the fields that quota model requires, listed in `quota_model_docs` at the top of the file
- `confidence`. Be honest. `measured` means somebody ran the plan to exhaustion and counted
- `method`, one sentence on where the number came from
- `evidence`, one entry per number, each pointing at a source id in `data/sources.json`
- `sources`, the ids again at plan level
- `available`, false if signups are closed, with `unavailable_reason`

The validator fails the build if a citation does not resolve or if an evidence entry is missing. That is deliberate. A number without a source does not belong on the page.

## Adding a source

Add the record to `data/sources.json` first. It needs a title, a url, a licence, a retrieval date, what it covers, and what you changed. If the licence requires attribution, say so in the record and check it appears on the page.

## Licensing what you send

Code and data you contribute go out under the repo's MIT licence. The measured
quota issue template asks you to confirm that.

This matters more than usual here. Rack Rate builds on Awesome Coding Plan, which
is CC BY 4.0, so attribution travels with those figures and must not be dropped.
If your contribution derives from a third party dataset, say which one and under
what terms, and add a record to `data/sources.json` before you use it.

Accepted measurements are credited to your GitHub handle in `data/sources.json`
unless you ask otherwise.

## What does not belong here

- Annual or promotional pricing. One billing basis keeps the comparison readable.
- Regional pricing. Worth doing, but as its own axis, not by quietly changing the base numbers.
- Benchmark task content. See the note in SOURCES.md.
- Affiliate links.

## Upstream changes

`python scripts/fetch_deepswe.py --diff` prints what moved on the leaderboard without writing anything. If the endpoint list in that file has gone stale, fixing it is a welcome PR on its own.
