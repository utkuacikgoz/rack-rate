#!/usr/bin/env python3
"""Join data/models.json against data/plans.json, derive cost per task and
days for a full run for every pair, and write data/derived.csv,
data/derived.json and site/index.html.

Run scripts/validate.py first. This script assumes the data already passed.
"""
import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"

FIVE_HOUR_WINDOWS_PER_DAY = 24 / 5


def load(name):
    return json.loads((DATA / name).read_text())


def total_tokens_per_task(model):
    input_tokens = model.get("input_tokens_per_task")
    output_tokens = model.get("output_tokens_per_task")
    if not input_tokens or not output_tokens:
        return None
    return input_tokens + output_tokens


def tasks_per_month(model, plan):
    """Return (tasks_per_month, method_used) or (None, reason) if the pair
    cannot be priced."""
    quota_model = plan["quota_model"]

    if quota_model == "budget":
        quota = plan.get("quota_usd_month")
        cost = model.get("api_cost_per_task_usd")
        if not quota or not cost:
            return None, "missing quota_usd_month or api_cost_per_task_usd"
        return quota / cost, "budget"

    if quota_model == "credits":
        credits = plan.get("credits_month")
        input_tokens = model.get("input_tokens_per_task")
        output_tokens = model.get("output_tokens_per_task")
        input_rate = model.get("input_rate_per_mtok_usd")
        output_rate = model.get("output_rate_per_mtok_usd")
        if not all([credits, input_tokens, output_tokens, input_rate, output_rate]):
            return None, "missing credits_month or token rate card fields for credit conversion"
        output_weight = output_rate / input_rate
        credits_per_task = (input_tokens + output_tokens * output_weight) / 10_000
        if credits_per_task <= 0:
            return None, "non-positive credits per task"
        return credits / credits_per_task, "credits"

    if quota_model == "requests":
        requests = plan.get("requests_month")
        steps = model.get("agent_steps_per_task") or plan.get("agent_steps_per_task_assumed")
        if not requests or not steps:
            return None, "missing requests_month or agent_steps_per_task"
        return requests / steps, "requests"

    if quota_model == "tokens_total":
        tokens = plan.get("tokens_month")
        tokens_per_task = total_tokens_per_task(model)
        if not tokens or not tokens_per_task:
            return None, "missing tokens_month, or model has no input/output tokens per task"
        return tokens / tokens_per_task, "tokens_total"

    return None, f"unknown quota_model '{quota_model}'"


def days_for_full_run(plan, model, tpm, task_count):
    tasks_per_day_monthly = tpm / 30
    window_hours = plan.get("rolling_window_hours")
    window_usd = plan.get("rolling_window_usd")
    tasks_per_day = tasks_per_day_monthly
    if window_hours and window_usd:
        cost = model.get("api_cost_per_task_usd")
        if cost:
            tasks_per_window = window_usd / cost
            windows_per_day = 24 / window_hours
            tasks_per_day = min(tasks_per_day_monthly, tasks_per_window * windows_per_day)
    if tasks_per_day <= 0:
        return None
    return task_count / tasks_per_day


def model_allowed(model, plan):
    """A plan only prices models its vendor actually lets you run. 'any'
    covers multi-model aggregator plans (Cursor, Ollama, GitHub Copilot);
    otherwise model_scope is a list of provider names or exact model ids."""
    scope = plan.get("model_scope")
    if scope is None or scope == "any":
        return True
    return model.get("provider") in scope or model.get("id") in scope


def build_pairs(models, plans, task_count):
    pairs = []
    for plan in plans:
        if not plan.get("available", True):
            continue
        for model in models:
            if not model_allowed(model, plan):
                continue
            tpm, method = tasks_per_month(model, plan)
            if tpm is None or tpm <= 0:
                continue
            cost_per_task = plan["price_usd_month"] / tpm
            pairs.append({
                "model_id": model["id"],
                "model_name": model["name"],
                "score_pct": model["score_pct"],
                "plan_id": plan["id"],
                "plan_name": plan["name"],
                "provider": plan["provider"],
                "price_usd_month": plan["price_usd_month"],
                "api_cost_per_task_usd": model["api_cost_per_task_usd"],
                "tasks_per_month": round(tpm, 2),
                "cost_per_task_usd": round(cost_per_task, 4),
                "days_for_full_run": (
                    round(d, 2) if (d := days_for_full_run(plan, model, tpm, task_count)) else None
                ),
                "quota_method": method,
                "confidence": plan["confidence"],
            })
    pairs.sort(key=lambda p: p["cost_per_task_usd"])
    return pairs


def best_routes(pairs):
    best = {}
    for p in pairs:
        mid = p["model_id"]
        if mid not in best or p["cost_per_task_usd"] < best[mid]["cost_per_task_usd"]:
            best[mid] = p
    return sorted(best.values(), key=lambda p: p["cost_per_task_usd"])


def cross_check(models, plans):
    """For plans that publish both a dollar quota and a token quota for the
    same measurement period, compute tasks_per_month both ways and report the
    ratio between them."""
    rows = []
    for plan in plans:
        if plan.get("quota_model") != "budget":
            continue
        tokens_month = plan.get("cross_check_tokens_month")
        if not tokens_month:
            continue
        for model in models:
            if not model_allowed(model, plan):
                continue
            tokens_per_task = total_tokens_per_task(model)
            if not tokens_per_task:
                continue
            quota = plan.get("quota_usd_month")
            cost = model.get("api_cost_per_task_usd")
            if not quota or not cost:
                continue
            tasks_dollars = quota / cost
            tasks_tokens = tokens_month / tokens_per_task
            if tasks_dollars <= 0 or tasks_tokens <= 0:
                continue
            ratio = max(tasks_dollars, tasks_tokens) / min(tasks_dollars, tasks_tokens)
            rows.append({
                "plan_id": plan["id"],
                "plan_name": plan["name"],
                "model_id": model["id"],
                "model_name": model["name"],
                "tasks_by_dollars": round(tasks_dollars, 2),
                "tasks_by_tokens": round(tasks_tokens, 2),
                "ratio": round(ratio, 3),
            })
    ratios = [r["ratio"] for r in rows]
    summary = {}
    if ratios:
        summary = {
            "median_ratio": round(statistics.median(ratios), 3),
            "min_ratio": round(min(ratios), 3),
            "max_ratio": round(max(ratios), 3),
            "pair_count": len(ratios),
        }
    return rows, summary


def write_csv(pairs, path):
    fields = [
        "model_id", "model_name", "score_pct", "plan_id", "plan_name", "provider",
        "price_usd_month", "api_cost_per_task_usd", "tasks_per_month",
        "cost_per_task_usd", "days_for_full_run", "quota_method", "confidence",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in pairs:
            writer.writerow(row)


def inject_into_template(payload):
    template = (SITE / "template.html").read_text()
    marker = "__RACK_RATE_DATA__"
    if marker not in template:
        raise SystemExit("site/template.html is missing the __RACK_RATE_DATA__ placeholder")
    injected = template.replace(marker, json.dumps(payload, separators=(",", ":")))
    (SITE / "index.html").write_text(injected)


def main():
    models_doc = load("models.json")
    plans_doc = load("plans.json")
    sources_doc = load("sources.json")
    models = models_doc["models"]
    plans = plans_doc["plans"]
    sources = sources_doc["sources"]
    task_count = models_doc.get("task_count", 113)

    pairs = build_pairs(models, plans, task_count)
    routes = best_routes(pairs)
    cross_rows, cross_summary = cross_check(models, plans)

    derived = {
        "generated_from": {
            "models": len(models),
            "plans": len(plans),
            "task_count": task_count,
        },
        "pairs": pairs,
        "best_routes": routes,
        "cross_check": {
            "pairs": cross_rows,
            "summary": cross_summary,
        },
        "known_gaps": plans_doc.get("known_gaps", []),
    }

    (DATA / "derived.json").write_text(json.dumps(derived, indent=2))
    write_csv(pairs, DATA / "derived.csv")

    payload = {
        "models": models,
        "plans": plans,
        "sources": sources,
        "derived": derived,
    }
    inject_into_template(payload)

    print(
        f"compute.py: {len(pairs)} pairs, {len(routes)} best routes, "
        f"{len(cross_rows)} cross-check pairs. Wrote derived.csv, derived.json, site/index.html"
    )


if __name__ == "__main__":
    main()
