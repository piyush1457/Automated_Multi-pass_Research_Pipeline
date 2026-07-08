"""
pass2_verify.py — Independent cross-check (Pass 2)

Selects ~20 apps: 10 lowest-confidence from Pass 1 + 10 random.
Runs fresh search/fetch/LLM for each — no knowledge of Pass 1 answers.
Diffs every field, writes data/pass2_diffs.json, prints agreement rate.
"""

import os
import json
import time
import random
import logging
from pathlib import Path

from dotenv import load_dotenv

from apps import APP_BY_ID
from schema import make_empty_record
from pass1_research import (
    search, fetch_and_clean, call_groq, check_composio_toolkit,
    log as p1_log, GROQ_SLEEP, MAX_FETCH_PAGES, DATA_DIR, LOGS_DIR
)

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_FILE = LOGS_DIR / "pass2.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("pass2")

PASS1_FILE   = DATA_DIR / "pass1_results.json"
PASS2_DIFFS  = DATA_DIR / "pass2_diffs.json"

DIFF_SKIP_FIELDS = {"id", "name", "category", "verification_status"}
SAMPLE_SIZE      = 20   # 10 lowest-confidence + 10 random

# ── Load Pass 1 ───────────────────────────────────────────────────────────────

def load_pass1() -> list[dict]:
    if not PASS1_FILE.exists():
        raise FileNotFoundError(f"Run pass1_research.py first — {PASS1_FILE} not found")
    with open(PASS1_FILE, encoding="utf-8") as f:
        return json.load(f)

# ── Sample selection ──────────────────────────────────────────────────────────

def select_sample(records: list[dict]) -> list[dict]:
    sorted_by_conf = sorted(records, key=lambda r: r.get("confidence", 1.0))
    bottom_10 = sorted_by_conf[:10]
    bottom_ids = {r["id"] for r in bottom_10}
    rest = [r for r in records if r["id"] not in bottom_ids]
    random_10 = random.sample(rest, min(10, len(rest)))
    sample = bottom_10 + random_10
    random.shuffle(sample)
    log.info(f"Selected {len(sample)} apps for Pass 2")
    return sample

# ── Independent extraction ────────────────────────────────────────────────────

def independent_extract(app_meta: dict) -> dict:
    """
    Run a completely fresh search+fetch+LLM for an app.
    Uses different query phrasing to get different evidence URLs.
    """
    name     = app_meta["name"]
    slug     = app_meta["slug"]
    category = app_meta["category"]
    app_id   = app_meta["id"]

    log.info(f"[P2 {app_id:03d}] Re-checking: {name}")

    # Deliberately different search queries for independence
    queries = [
        f"{name} developer API authentication setup",
        f"site:docs OR site:developers {name} API reference",
    ]
    search_results = []
    for q in queries:
        results = search(q, max_results=4)
        search_results.extend(results)
        if len(search_results) >= 3:
            break

    # Pick best URLs (prefer official docs, auth, pricing pages)
    priority_keywords = ["docs", "developers", "api", "authentication", "auth", "pricing", "developer"]
    scored = []
    from urllib.parse import urlparse
    slug_clean = slug.replace("_", "").replace("-", "").lower()
    for r in search_results:
        url  = r.get("href", "")
        body = r.get("body", "")
        if not url:
            continue
        score = sum(kw in url.lower() or kw in body.lower() for kw in priority_keywords)
        # Domain boost logic
        domain = urlparse(url.lower()).netloc
        if slug_clean in domain.replace(".", ""):
            score += 15
        scored.append((score, url, body))
    scored.sort(key=lambda x: -x[0])
    top_urls = [url for _, url, _ in scored[:MAX_FETCH_PAGES] if url]

    fetched_pages = []
    fetched_urls  = []
    for url in top_urls:
        text, canonical = fetch_and_clean(url)
        if text:
            fetched_pages.append((text, canonical))
            fetched_urls.append(canonical)
        time.sleep(0.5)

    if not fetched_pages:
        log.warning(f"  All page fetches failed — falling back to search snippets")
        fallback_text = ""
        for r in search_results:
            body = r.get("body", "").strip()
            url = r.get("href", "")
            if body:
                fallback_text += f"\n\n--- Source: {url} ---\n{body}"
                if url not in fetched_urls:
                    fetched_urls.append(url)
        if fallback_text.strip():
            fetched_pages.append((fallback_text, fetched_urls[0] if fetched_urls else "search_snippets"))

    record = make_empty_record(app_id, name, category)
    record["evidence_urls"] = fetched_urls

    if fetched_pages:
        time.sleep(GROQ_SLEEP)
        extracted = call_groq(name, fetched_pages)
        for field in ["one_liner", "auth_methods", "access", "api_surface",
                      "api_breadth_note", "buildable_verdict", "blocker",
                      "confidence", "notes"]:
            if field in extracted:
                record[field] = extracted[field]

        if isinstance(record["auth_methods"], str):
            record["auth_methods"] = [record["auth_methods"]]
        try:
            record["confidence"] = float(record.get("confidence", 0.5))
        except (TypeError, ValueError):
            record["confidence"] = 0.5

        mcp, source = check_composio_toolkit(slug, name)
        record["existing_mcp"] = mcp
        record["mcp_source"]   = source

    record["verification_status"] = "cross_checked"
    log.info(f"  P2 verdict={record['buildable_verdict']}, conf={record['confidence']:.2f}")
    return record

# ── Field diff ────────────────────────────────────────────────────────────────

def diff_records(r1: dict, r2: dict) -> list[dict]:
    """Return list of {field, pass1_value, pass2_value} for fields that differ."""
    diffs = []
    all_fields = set(r1.keys()) | set(r2.keys())
    for field in sorted(all_fields):
        if field in DIFF_SKIP_FIELDS:
            continue
        v1 = r1.get(field)
        v2 = r2.get(field)
        # Normalise lists for comparison
        if isinstance(v1, list):
            v1 = sorted(v1)
        if isinstance(v2, list):
            v2 = sorted(v2)
        if v1 != v2:
            diffs.append({
                "field":       field,
                "pass1_value": r1.get(field),
                "pass2_value": r2.get(field),
                "pass1_urls":  r1.get("evidence_urls", [])[:2],
                "pass2_urls":  r2.get("evidence_urls", [])[:2],
            })
    return diffs

# ── Agreement rate ────────────────────────────────────────────────────────────

def compute_agreement(diffs_data: list[dict]) -> float:
    """Return % of fields that matched across all sampled apps."""
    total_fields   = 0
    matched_fields = 0
    compare_fields = [
        "auth_methods", "access", "api_surface", "buildable_verdict",
        "existing_mcp", "mcp_source",
    ]
    for entry in diffs_data:
        diff_field_names = {d["field"] for d in entry["diffs"]}
        for f in compare_fields:
            total_fields += 1
            if f not in diff_field_names:
                matched_fields += 1
    if total_fields == 0:
        return 0.0
    return round(matched_fields / total_fields * 100, 1)

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    records    = load_pass1()
    sample     = select_sample(records)
    pass1_map  = {r["id"]: r for r in records}

    diffs_data = []
    for p1_record in sample:
        app_meta = APP_BY_ID.get(p1_record["id"])
        if not app_meta:
            log.warning(f"No app meta for id={p1_record['id']}")
            continue

        p2_record = independent_extract(app_meta)

        field_diffs = diff_records(p1_record, p2_record)
        entry = {
            "id":            p1_record["id"],
            "name":          p1_record["name"],
            "category":      p1_record["category"],
            "diffs":         field_diffs,
            "diff_count":    len(field_diffs),
            "pass1_confidence": p1_record.get("confidence", 0.0),
            "pass2_confidence": p2_record.get("confidence", 0.0),
        }
        diffs_data.append(entry)
        log.info(f"  → {len(field_diffs)} field(s) differ")

        # Update pass1 verification_status for sampled records
        pass1_map[p1_record["id"]]["verification_status"] = "cross_checked"

        time.sleep(1)

    # Save diffs
    with open(PASS2_DIFFS, "w", encoding="utf-8") as f:
        json.dump(diffs_data, f, indent=2, ensure_ascii=False)
    log.info(f"Saved diffs → {PASS2_DIFFS}")

    # Update pass1 results with cross_checked statuses
    records_updated = sorted(pass1_map.values(), key=lambda r: r["id"])
    tmp = Path("data/pass1_results.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(records_updated, f, indent=2, ensure_ascii=False)
    tmp.replace(Path("data/pass1_results.json"))

    # Agreement rate
    rate = compute_agreement(diffs_data)
    print("\n" + "=" * 60)
    print(f"  PASS 2 AGREEMENT RATE: {rate:.1f}%")
    print(f"  (across {len(diffs_data)} sampled apps, 6 key fields)")
    print("=" * 60 + "\n")

    return diffs_data, rate


if __name__ == "__main__":
    run()
