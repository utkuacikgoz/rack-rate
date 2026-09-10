#!/usr/bin/env python3
"""Refresh data/models.json from the live DeepSWE leaderboard.

    python scripts/fetch_deepswe.py --diff   # print what moved, write nothing
    python scripts/fetch_deepswe.py          # write data/models.json

VERIFIED. ENDPOINTS[0] and the response shape below were confirmed against a
real fetch of the live site: `curl -s <url> | head -c 2000` was run outside
this build environment (which cannot reach deepswe.datacurve.ai at all) and
the result matched exactly, field for field, the "rows" schema this file
expects. The other entries in ENDPOINTS are older, unconfirmed guesses kept
only as a fallback if the confirmed one ever moves.

Each row is one (model, harness, reasoning_effort) configuration. Per model,
only the highest pass_rate configuration is kept, per CONTRIBUTING item 7 —
DeepSWE runs some models at several reasoning-effort levels, and this repo
tracks one row per model, not one per configuration. Efficiency figures
(cost, tokens, agent steps) use the median over scored attempts, not the
mean, to resist a few very expensive stuck runs skewing the number.

MODEL_NAME_MAP and MODEL_PROVIDER_MAP are hand-maintained: the API returns
model ids with dashes where a dotted version number reads better (e.g.
"gpt-5-5" for gpt-5.5), and there is no reliable way to guess that
mechanically for a model this script has never seen before ("qwen3-7-max"
and "gpt-5-4-mini" don't dash-to-dot the same way). A model missing from
these maps is still written, just with its raw id as both id and name, and a
warning is printed so a maintainer can add it.

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
    "https://deepswe.datacurve.ai/artifacts/v1/leaderboard-live.json",  # confirmed against a real fetch
    "https://deepswe.datacurve.ai/api/leaderboard",
    "https://deepswe.datacurve.ai/leaderboard.json",
    "https://api.datacurve.ai/deepswe/leaderboard",
]

USER_AGENT = "rack-rate-fetch/1 (+https://github.com/utkuacikgoz/rack-rate)"

MODEL_NAME_MAP = {
    "gpt-5-5": "gpt-5.5",
    "claude-opus-4-8": "claude-opus-4.8",
    "gpt-5-4": "gpt-5.4",
    "claude-opus-4-7": "claude-opus-4.7",
    "glm-5-2": "glm-5.2",
    "claude-sonnet-4-6": "claude-sonnet-4.6",
    "gemini-3-5-flash": "gemini-3.5-flash",
    "claude-opus-4-6": "claude-opus-4.6",
    "gpt-5-4-mini": "gpt-5.4-mini",
    "kimi-k2-6": "kimi-k2.6",
    "minimax-m3": "minimax-m3",
    "mimo-v2-5-pro": "mimo-v2.5-pro",
    "qwen3-7-max": "qwen-3.7-max",
    "glm-5-1": "glm-5.1",
    "grok-build-0-1": "grok-build-0.1",
    "gemini-3-1-pro-preview": "gemini-3.1-pro-preview",
    "deepseek-v4-pro": "deepseek-v4-pro",
    "gemini-3-flash-preview": "gemini-3-flash-preview",
    "qwen3-6-plus": "qwen-3.6-plus",
    "claude-haiku-4-5": "claude-haiku-4.5",
    "minimax-m2-7": "minimax-m2.7",
}

MODEL_PROVIDER_MAP = {
    "gpt-5.5": "OpenAI", "gpt-5.4": "OpenAI", "gpt-5.4-mini": "OpenAI",
    "claude-opus-4.8": "Anthropic", "claude-opus-4.7": "Anthropic", "claude-opus-4.6": "Anthropic",
    "claude-sonnet-4.6": "Anthropic", "claude-haiku-4.5": "Anthropic",
    "glm-5.2": "Zhipu (Z.ai)", "glm-5.1": "Zhipu (Z.ai)",
    "gemini-3.5-flash": "Google", "gemini-3.1-pro-preview": "Google", "gemini-3-flash-preview": "Google",
    "kimi-k2.6": "Moonshot AI",
    "minimax-m3": "MiniMax", "minimax-m2.7": "MiniMax",
    "mimo-v2.5-pro": "Xiaomi",
    "qwen-3.7-max": "Alibaba", "qwen-3.6-plus": "Alibaba",
    "grok-build-0.1": "xAI",
    "deepseek-v4-pro": "DeepSeek",
}


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
        + "\n\nENDPOINTS[0] was confirmed working before. If it has moved, "
          "open https://deepswe.datacurve.ai/ in a browser, find the real "
          "data request in the network tab, and fix ENDPOINTS in this file."
    )


def normalize(raw):
    """raw is the confirmed live schema: {"rows": [...], "n_tasks_in_set": ...}.
    Each row is one (model, harness, reasoning_effort) configuration; keep
    only the best-scoring configuration per model."""
    best = {}
    by_model = {}
    for row in raw.get("rows", []):
        raw_id = row.get("model")
        if raw_id is None:
            continue
        by_model.setdefault(raw_id, []).append(row)
        if raw_id not in best or row.get("pass_rate", 0) > best[raw_id].get("pass_rate", 0):
            best[raw_id] = row

    def variant(row):
        return {
            "reasoning_effort": row.get("reasoning_effort"),
            "score_pct": round(row["pass_rate"] * 100, 2),
            "api_cost_per_task_usd": round(row["median_cost_usd"], 4),
            "output_tokens_per_task": round(row["median_output_tokens"]),
            "input_tokens_per_task": round(row["median_input_tokens"]),
            "agent_steps_per_task": round(row["median_agent_steps"], 1),
        }

    task_count = raw.get("n_tasks_in_set")
    out = []
    for raw_id, row in best.items():
        mid = MODEL_NAME_MAP.get(raw_id, raw_id)
        if raw_id not in MODEL_NAME_MAP:
            print(f"fetch_deepswe.py: warning, no MODEL_NAME_MAP entry for '{raw_id}', using it as-is")
        provider = MODEL_PROVIDER_MAP.get(mid)
        if provider is None:
            print(f"fetch_deepswe.py: warning, no MODEL_PROVIDER_MAP entry for '{mid}'")
        model = {
            "id": mid,
            "name": mid,
            "provider": provider,
            "score_pct": round(row["pass_rate"] * 100, 2),
            "score_pass_at_4_pct": round(row["pass_at_4"] * 100, 2) if row.get("pass_at_4") is not None else None,
            "reasoning_effort": row.get("reasoning_effort"),
            "api_cost_per_task_usd": round(row["median_cost_usd"], 4),
            "output_tokens_per_task": round(row["median_output_tokens"]),
            "input_tokens_per_task": round(row["median_input_tokens"]),
            "agent_steps_per_task": round(row["median_agent_steps"], 1),
            "n_tasks_attempted": row.get("n_tasks_attempted"),
            "evidence": ["src-deepswe-data"],
        }
        variants = sorted((variant(r) for r in by_model[raw_id]), key=lambda v: -v["score_pct"])
        if len(variants) > 1:
            model["effort_variants"] = variants
        out.append(model)
    out.sort(key=lambda m: -m["score_pct"])
    return out, task_count


def diff(old_models, new_models):
    old_by_id = {m["id"]: m for m in old_models}
    changes = []
    for nm in new_models:
        om = old_by_id.get(nm["id"])
        if om is None:
            changes.append(f"new model: {nm['id']}")
            continue
        for field in ("score_pct", "api_cost_per_task_usd", "output_tokens_per_task",
                       "input_tokens_per_task", "agent_steps_per_task", "reasoning_effort"):
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
    new_models, task_count = normalize(raw)

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
    if task_count:
        existing["task_count"] = task_count
    existing_path.write_text(json.dumps(existing, indent=2))
    print(f"fetch_deepswe.py: wrote {len(new_models)} models from {source_url}")


if __name__ == "__main__":
    main()
