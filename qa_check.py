"""
qa_check.py — Testing & QA harness (Step 1-5 of QA prompt)

Run AFTER all passes and generate_html.py are complete.
Produces a machine-readable + human-readable QA report.
"""

import json
import os
import sys
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR   = Path("data")
FINAL_FILE = DATA_DIR / "final_verified.json"
PASS1_FILE = DATA_DIR / "pass1_results.json"
REPORT_FILE= DATA_DIR / "verification_report.json"
HTML_FILE  = Path("index.html")
LOG_FILE   = Path("logs") / "pass1.log"

# ── Load best available data ────────────────────────────────────────────────

def load_records() -> list[dict]:
    src = FINAL_FILE if FINAL_FILE.exists() else PASS1_FILE
    if not src.exists():
        print("ERROR: No data file found. Run pass1_research.py first.")
        sys.exit(1)
    with open(src, encoding="utf-8") as f:
        records = json.load(f)
    print(f"\n{'='*65}")
    print(f"  DATA SOURCE: {src}  ({len(records)} records)")
    print(f"{'='*65}")
    return records, str(src)

# ── Step 1: Data sanity ─────────────────────────────────────────────────────

def step1_sanity(records):
    print("\n── STEP 1: Data Sanity ────────────────────────────────────────")

    # 1a. Count
    n = len(records)
    print(f"\n  Total records: {n}  (expected: 100)")
    if n != 100:
        ids_present = {r["id"] for r in records}
        missing = [i for i in range(1, 101) if i not in ids_present]
        print(f"  ⚠  MISSING IDs: {missing}")
    else:
        print("  ✓ Record count is exactly 100")

    # 1b. Required field completeness
    REQUIRED = ["name", "category", "access", "buildable_verdict"]
    print("\n  Required field completeness:")
    incomplete = []
    for r in records:
        blank = [f for f in REQUIRED if not r.get(f)]
        if blank:
            incomplete.append({"id": r["id"], "name": r.get("name","?"), "blank_fields": blank})
    if incomplete:
        print(f"  ⚠  {len(incomplete)} records have blank required fields:")
        for x in incomplete:
            print(f"     id={x['id']} ({x['name']}): {x['blank_fields']}")
    else:
        print(f"  ✓ All {n} records have required fields populated")

    # 1c. Evidence URL check
    print("\n  Evidence URL audit:")
    no_url_confident = []
    for r in records:
        urls = r.get("evidence_urls", [])
        access = r.get("access", "unclear")
        conf = r.get("confidence", 0)
        if not urls and access != "unclear" and conf > 0.4:
            no_url_confident.append({
                "id": r["id"], "name": r.get("name","?"),
                "access": access, "confidence": conf
            })
    if no_url_confident:
        print(f"  ⚠  {len(no_url_confident)} records claim confident access but have NO evidence URLs:")
        for x in no_url_confident:
            print(f"     id={x['id']} ({x['name']}) access={x['access']} conf={x['confidence']}")
    else:
        print(f"  ✓ No confident records are missing evidence URLs")

    # 1d. 'unclear' distribution
    access_dist = Counter(r.get("access","unclear") for r in records)
    unclear_count = access_dist.get("unclear", 0)
    unclear_pct   = round(unclear_count / n * 100, 1) if n else 0
    print(f"\n  Access distribution (of {n} records):")
    for k, v in sorted(access_dist.items(), key=lambda x: -x[1]):
        bar = "█" * int(v / n * 30)
        flag = " ⚠  HIGH" if k == "unclear" and unclear_pct > 25 else ""
        print(f"     {k:<22} {v:>3}  ({v/n*100:5.1f}%)  {bar}{flag}")

    if unclear_pct > 25:
        print(f"\n  ⚠  ALERT: {unclear_count} records ({unclear_pct}%) are 'unclear' — above 25% threshold.")
        print(f"     This indicates the search/fetch step failed silently for many apps.")
        print(f"     Check logs/pass1.log for 'Fetch failed' or 'no search results' patterns.")
    else:
        print(f"\n  ✓ 'unclear' rate ({unclear_pct}%) is within acceptable range (<25%)")

    return {
        "record_count": n,
        "missing_ids":  [i for i in range(1, 101) if {r["id"] for r in records} and i not in {r["id"] for r in records}],
        "incomplete_records": incomplete,
        "no_url_confident":   no_url_confident,
        "access_distribution": dict(access_dist),
        "unclear_pct": unclear_pct,
    }

# ── Step 2: Spot-check specific apps ────────────────────────────────────────

SPOT_CHECK_APPS = ["Stripe", "Salesforce", "GitHub", "Slack",
                   "PitchBook", "Waterfall.io", "fanbasis", "DealCloud"]

KNOWN_FACTS = {
    "Stripe":     {"access": ["self_serve_free"], "auth": ["API Key"], "verdict": ["yes"]},
    "GitHub":     {"access": ["self_serve_free"], "auth": ["OAuth2","Token","API Key"], "verdict": ["yes"]},
    "Slack":      {"access": ["self_serve_free","self_serve_trial"], "auth": ["OAuth2"], "verdict": ["yes","partial"]},
    "Salesforce": {"access": ["self_serve_trial","paid_plan_required"], "auth": ["OAuth2"], "verdict": ["yes","partial"]},
}

def step2_spotcheck(records):
    print("\n── STEP 2: Spot-check Known Apps ──────────────────────────────")
    rec_by_name = {r["name"]: r for r in records}

    for app_name in SPOT_CHECK_APPS:
        print(f"\n  ┌─ {app_name}")
        record = rec_by_name.get(app_name)

        if not record:
            print(f"  │  ⚠  NOT IN DATASET — this app is not one of the 100 researched apps.")
            print(f"  │     (The QA prompt references apps from a different brief)")
            print(f"  └─────────────────────────────────────────────────────")
            continue

        # Print key fields
        for field in ["auth_methods","access","api_surface","buildable_verdict",
                      "existing_mcp","mcp_source","confidence","verification_status"]:
            val = record.get(field, "")
            print(f"  │  {field:<22} {val}")

        print(f"  │  evidence_urls ({len(record.get('evidence_urls',[]))}):")
        for u in record.get("evidence_urls", [])[:3]:
            print(f"  │    - {u}")

        # Plausibility check
        known = KNOWN_FACTS.get(app_name)
        flags = []
        if known:
            if record.get("access") not in known["access"]:
                flags.append(f"access={record.get('access')} — expected one of {known['access']}")
            if not any(m in record.get("auth_methods",[]) for m in known["auth"]):
                flags.append(f"auth_methods={record.get('auth_methods')} — expected one of {known['auth']}")
            if record.get("buildable_verdict") not in known["verdict"]:
                flags.append(f"buildable_verdict={record.get('buildable_verdict')} — expected one of {known['verdict']}")

        if flags:
            print(f"  │  ⚠  PLAUSIBILITY FLAGS:")
            for f in flags:
                print(f"  │     - {f}")
        else:
            print(f"  │  ✓ Fields look plausible")
        print(f"  └─────────────────────────────────────────────────────")

# ── Step 3: HTML verification ───────────────────────────────────────────────

def step3_html():
    print("\n── STEP 3: HTML Verification ──────────────────────────────────")

    if not HTML_FILE.exists():
        print("  ⚠  index.html not found — run generate_html.py first")
        return

    with open(HTML_FILE, encoding="utf-8") as f:
        html = f.read()

    size_kb = len(html.encode("utf-8")) // 1024
    print(f"\n  File size: {size_kb} KB")

    # 3a. Check no external fetch of data files
    import re
    fetch_calls = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", html)
    data_fetches = [u for u in fetch_calls if "data/" in u or ".json" in u.lower()]
    if data_fetches:
        print(f"  ⚠  Found {len(data_fetches)} fetch() calls pointing to local files:")
        for u in data_fetches:
            print(f"     {u}")
    else:
        print("  ✓ No fetch() calls to local data/ files — data is inline")

    # 3b. Confirm inline data blob
    for var in ["RECORDS", "APP_DATA", "appData", "records"]:
        idx = html.find(f"const {var}")
        if idx != -1:
            snippet = html[idx:idx+120].replace("\n", " ")
            print(f"\n  ✓ Found inline JS data variable:")
            print(f"    {snippet}...")
            # Count records in the blob
            count = html.count('"buildable_verdict"')
            print(f"    Embedded record count (by 'buildable_verdict' occurrences): {count}")
            break
    else:
        print("  ⚠  Could not find inline data variable (RECORDS/APP_DATA)")

    # 3c. Check filter/sort JS
    has_filter = "addEventListener" in html and "filter" in html.lower()
    has_sort   = "sort" in html and "data-col" in html
    print(f"\n  Filter wiring:  {'✓ addEventListener found' if has_filter else '⚠  Not found'}")
    print(f"  Sort wiring:    {'✓ data-col sort handlers found' if has_sort else '⚠  Not found'}")

    print(f"\n  → Open in browser: http://localhost:8000/index.html")
    print(f"    (run: python -m http.server 8000 in this folder)")

# ── Step 4: Verification report ─────────────────────────────────────────────

def step4_report():
    print("\n── STEP 4: Verification Report ────────────────────────────────")

    if not REPORT_FILE.exists():
        print("  ⚠  data/verification_report.json not found — run pass3_human_check.py")
        print("     (Pass 3 requires interactive human input via CLI)")
        return

    with open(REPORT_FILE, encoding="utf-8") as f:
        report = json.load(f)

    print("\n  Full verification_report.json contents:")
    print(json.dumps(report, indent=4))

    # Check three distinct numbers
    p1  = report.get("pass1_raw_accuracy_pct")
    p2  = report.get("pass2_agreement_rate_pct")
    fin = report.get("final_accuracy_pct")
    print(f"\n  Pass 1 raw accuracy:    {p1}%")
    print(f"  Pass 2 agreement rate:  {p2}%")
    print(f"  Final (human-verified): {fin}%")

    if all(x is not None for x in [p1, p2, fin]):
        print("  ✓ All 3 accuracy numbers present")
    else:
        print("  ⚠  One or more accuracy numbers are None — pass may not have run")

# ── Step 5: Manual checks required ──────────────────────────────────────────

def step5_manual():
    print("\n── STEP 5: What Still Needs Your Manual Eyes ──────────────────")
    items = [
        ("Evidence URL validity",
         "I fetched real URLs and recorded them, but I cannot guarantee the page content matched\n"
         "     the specific claim made (e.g. 'auth=OAuth2'). Open 3-5 evidence_urls yourself\n"
         "     and verify the page actually says what the agent claimed."),
        ("Salesforce 403 pattern",
         "developer.salesforce.com blocks bot fetches with 403. The Salesforce record was\n"
         "     populated via Tavily's web cache/snippets, not the raw docs page. The access=\n"
         "     'self_serve_trial' finding may be from a snippet, not the full pricing page.\n"
         "     Verify: https://developer.salesforce.com/developer-centers/rest-api"),
        ("'unclear' access records",
         "Any record with access='unclear' means the fetched pages didn't state pricing/access\n"
         "     clearly. This is NOT necessarily wrong — some apps genuinely don't publish this.\n"
         "     But spot-check 3-4 of these against the actual product website."),
        ("Pass 3 human verification",
         "pass3_human_check.py is an INTERACTIVE CLI — I cannot run it for you.\n"
         "     Run: python pass3_human_check.py\n"
         "     You'll be prompted for ~10 apps. Type 'correct' or type a correction.\n"
         "     Without this step, verification_status='human_verified' records = 0."),
        ("MCP source = 'composio' accuracy",
         "The Composio check reads from the SDK's local app.pyi stub (293 apps).\n"
         "     The stub's app names use UPPER_SNAKE_CASE. My fuzzy match may miss:\n"
         "     - Apps with non-obvious slugs (e.g. GOOGLEANALYTICS vs google_analytics)\n"
         "     - Apps added to Composio after this SDK version was built\n"
         "     Verify the mcp=True records against: https://composio.dev"),
        ("PitchBook / Waterfall.io / fanbasis / DealCloud",
         "These 4 apps from the QA prompt are NOT in our 100-app list. Our list covers\n"
         "     10 standard SaaS categories. If these were meant to be researched, they need\n"
         "     to be added to apps.py and re-run."),
    ]
    for i, (title, detail) in enumerate(items, 1):
        print(f"\n  {i}. {title}")
        print(f"     {detail}")

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    records, source = load_records()

    s1 = step1_sanity(records)
    step2_spotcheck(records)
    step3_html()
    step4_report()
    step5_manual()

    print(f"\n{'='*65}")
    print(f"  QA SUMMARY")
    print(f"{'='*65}")
    print(f"  Records: {s1['record_count']}/100")
    print(f"  Unclear rate: {s1['unclear_pct']}%")
    print(f"  Incomplete records: {len(s1['incomplete_records'])}")
    print(f"  Zero-URL confident records: {len(s1['no_url_confident'])}")
    print(f"  Data source: {source}")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
