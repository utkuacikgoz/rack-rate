#!/usr/bin/env python3
"""Refresh data/models.json from the live DeepSWE leaderboard.

    python scripts/fetch_deepswe.py --diff   # print what moved, write nothing
    python scripts/fetch_deepswe.py          # write data/models.json

UNVERIFIED. The endpoints below have not been confirmed against the live
site. deepswe.datacurve.ai renders as a JavaScript SPA, so a plain request
to the page itself returns an empty shell, not leaderboard data. Whoever
opens the site's network tab and finds the real JSON endpoint should replace
ENDPOINTS below and delete this notice. See CONTRIBUTING.md and the open
work list for this task.

This script never touches DeepSWE task content, only leaderboard metadata
(model id, score, cost per task, output tokens, agent steps). The benchmark
carries a canary string specifically to catch that kind of mirroring.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

ENDPOINTS = [
    "https://deepswe.datacurve.ai/api/leaderboard",
    "https://deepswe.datacurve.ai/leaderboard.json",
    "https://api.datacurve.ai/deepswe/leaderboard",
]

USER_AGENT = "rack-rate-fetch/1 (+https://github.com/utkuacikgoz/rack-rate)"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_leaderboard():
    errors = []
    for url in ENDPOINTS:
        try:
            return fetch_json(url), url
        except Exception as e:
            errors.append(f"{url}: {e}")
    raise SystemExit(
        "fetch_deepswe.py: could not reach any candidate endpoint.\n"
        + "\n".join(f"  - {e}" for e in errors)
        + "\n\nThese endpoints are unverified guesses. Open "
          "https://deepswe.datacurve.ai/ in a browser, find the real data "
          "request in the network tab, and fix ENDPOINTS in this file."
    )


def normalize(raw):
    """Map whatever shape the endpoint returns onto our model schema. This
    is necessarily a guess until a real payload has been seen."""
    models = raw.get("models", raw if isinstance(raw, list) else [])
    out = []
    for m in models:
        out.append({
            "id": m.get("id") or m.get("model") or m.get("name"),
            "name": m.get("display_name") or m.get("name") or m.get("model"),
            "provider": m.get("provider"),
            "score_pct": m.get("score") or m.get("score_pct"),
            "api_cost_per_task_usd": m.get("cost_per_task") or m.get("api_cost_per_task_usd"),
            "output_tokens_per_task": m.get("output_tokens") or m.get("output_tokens_per_task"),
            "agent_steps_per_task": m.get("agent_steps") or m.get("agent_steps_per_task"),
        })
    return out


def diff(old_models, new_models):
    old_by_id = {m["id"]: m for m in old_models}
    changes = []
    for nm in new_models:
        om = old_by_id.get(nm["id"])
        if om is None:
            changes.append(f"new model: {nm['id']}")
            continue
        for field in ("score_pct", "api_cost_per_task_usd", "output_tokens_per_task", "agent_steps_per_task"):
            if om.get(field) != nm.get(field):
                changes.append(f"{nm['id']}.{field}: {om.get(field)!r} -> {nm.get(field)!r}")
    new_ids = {m["id"] for m in new_models}
    for om in old_models:
        if om["id"] not in new_ids:
            changes.append(f"removed model: {om['id']}")
    return changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff", action="store_true", help="print what changed, write nothing")
    args = parser.parse_args()

    raw, source_url = fetch_leaderboard()
    new_models = normalize(raw)

    existing_path = DATA / "models.json"
    existing = json.loads(existing_path.read_text()) if existing_path.exists() else {"models": []}

    changes = diff(existing.get("models", []), new_models)

    if args.diff:
        if changes:
            print(f"fetch_deepswe.py: {len(changes)} change(s) from {source_url}")
            for c in changes:
                print(f"  - {c}")
            sys.exit(1)
        print("fetch_deepswe.py: no changes")
        return

    if not changes:
        print("fetch_deepswe.py: no changes, models.json left untouched")
        return

    existing["models"] = new_models
    existing["source_url"] = source_url
    existing_path.write_text(json.dumps(existing, indent=2))
    print(f"fetch_deepswe.py: wrote {len(new_models)} models from {source_url}")


if __name__ == "__main__":
    main()
