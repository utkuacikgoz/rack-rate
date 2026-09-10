#!/usr/bin/env python3
"""Schema, sanity and citation checks for data/models.json, data/plans.json
and data/sources.json. Exits non-zero on the first class of failure, after
printing every problem it found in that class.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

QUOTA_FIELDS = {
    "budget": ["quota_usd_month"],
    "credits": ["credits_month"],
    "requests": ["requests_month"],
    "tokens_total": ["tokens_month"],
}

REQUIRED_PLAN_FIELDS = [
    "id", "name", "provider", "price_usd_month", "quota_model", "model_scope",
    "confidence", "method", "evidence", "sources", "available",
]

CONFIDENCE_LEVELS = {"measured", "high", "medium", "low"}

REQUIRED_MODEL_FIELDS = [
    "id", "name", "provider", "score_pct", "api_cost_per_task_usd",
    "output_tokens_per_task", "evidence",
]

REQUIRED_SOURCE_FIELDS = ["id", "title", "url", "license", "retrieved", "covers"]


def load(name):
    path = DATA / name
    if not path.exists():
        return None, [f"{name} does not exist"]
    try:
        return json.loads(path.read_text()), []
    except json.JSONDecodeError as e:
        return None, [f"{name} is not valid JSON: {e}"]


def check_sources(sources_doc):
    errors = []
    ids = set()
    if sources_doc is None:
        return errors, ids
    for i, src in enumerate(sources_doc.get("sources", [])):
        where = f"sources[{i}]"
        for field in REQUIRED_SOURCE_FIELDS:
            if not src.get(field):
                errors.append(f"{where} is missing required field '{field}'")
        sid = src.get("id")
        if sid:
            if sid in ids:
                errors.append(f"{where} duplicates source id '{sid}'")
            ids.add(sid)
    return errors, ids


def check_models(models_doc, source_ids):
    errors = []
    ids = set()
    if models_doc is None:
        return errors, ids
    for i, m in enumerate(models_doc.get("models", [])):
        where = f"models[{i}] ({m.get('id', '?')})"
        for field in REQUIRED_MODEL_FIELDS:
            if field not in m or m[field] in (None, ""):
                errors.append(f"{where} is missing required field '{field}'")
        mid = m.get("id")
        if mid:
            if mid in ids:
                errors.append(f"{where} duplicates model id '{mid}'")
            ids.add(mid)
        score = m.get("score_pct")
        if score is not None and not (0 <= score <= 100):
            errors.append(f"{where} score_pct {score} is out of 0-100 range")
        cost = m.get("api_cost_per_task_usd")
        if cost is not None and cost <= 0:
            errors.append(f"{where} api_cost_per_task_usd must be positive, got {cost}")
        for ev in m.get("evidence", []):
            if ev not in source_ids:
                errors.append(f"{where} evidence references unknown source id '{ev}'")
        if not m.get("evidence"):
            errors.append(f"{where} has no evidence entries")
    return errors, ids


def check_plans(plans_doc, source_ids):
    errors = []
    ids = set()
    if plans_doc is None:
        return errors, ids
    for i, p in enumerate(plans_doc.get("plans", [])):
        where = f"plans[{i}] ({p.get('id', '?')})"
        for field in REQUIRED_PLAN_FIELDS:
            if field not in p or p[field] in (None, ""):
                errors.append(f"{where} is missing required field '{field}'")
        pid = p.get("id")
        if pid:
            if pid in ids:
                errors.append(f"{where} duplicates plan id '{pid}'")
            ids.add(pid)

        price = p.get("price_usd_month")
        if price is not None and price <= 0:
            errors.append(f"{where} price_usd_month must be positive, got {price}")

        confidence = p.get("confidence")
        if confidence is not None and confidence not in CONFIDENCE_LEVELS:
            errors.append(f"{where} confidence '{confidence}' not one of {sorted(CONFIDENCE_LEVELS)}")

        quota_model = p.get("quota_model")
        if quota_model is not None and quota_model not in QUOTA_FIELDS:
            errors.append(f"{where} quota_model '{quota_model}' not one of {sorted(QUOTA_FIELDS)}")
        elif quota_model and not p.get("quota_unresolved"):
            for field in QUOTA_FIELDS[quota_model]:
                if p.get(field) in (None, ""):
                    errors.append(
                        f"{where} quota_model '{quota_model}' requires field '{field}' "
                        f"(or set quota_unresolved: true and explain why in known_gaps)"
                    )

        if p.get("available") is False and not p.get("unavailable_reason"):
            errors.append(f"{where} is marked unavailable but has no unavailable_reason")

        for ev in p.get("evidence", []):
            src = ev if isinstance(ev, str) else ev.get("source")
            if src not in source_ids:
                errors.append(f"{where} evidence references unknown source id '{src}'")
        if not p.get("evidence"):
            errors.append(f"{where} has no evidence entries")

        for sid in p.get("sources", []):
            if sid not in source_ids:
                errors.append(f"{where} sources references unknown source id '{sid}'")

    for i, g in enumerate(plans_doc.get("known_gaps", [])):
        where = f"known_gaps[{i}]"
        for field in ("plan", "reason"):
            if not g.get(field):
                errors.append(f"{where} is missing required field '{field}'")

    return errors, ids


def main():
    all_errors = []

    sources_doc, err = load("sources.json")
    all_errors += err
    source_errors, source_ids = check_sources(sources_doc)
    all_errors += source_errors

    models_doc, err = load("models.json")
    all_errors += err
    model_errors, model_ids = check_models(models_doc, source_ids)
    all_errors += model_errors

    plans_doc, err = load("plans.json")
    all_errors += err
    plan_errors, plan_ids = check_plans(plans_doc, source_ids)
    all_errors += plan_errors

    if all_errors:
        print(f"validate.py: {len(all_errors)} problem(s) found\n")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)

    print(
        f"validate.py: ok "
        f"({len(source_ids)} sources, {len(model_ids)} models, {len(plan_ids)} plans)"
    )


if __name__ == "__main__":
    main()
