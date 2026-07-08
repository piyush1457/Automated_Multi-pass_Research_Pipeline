"""
pass3_human_check.py — Human verification CLI (Pass 3)

Picks ~10 apps (prioritises Pass 1/2 disagreements), presents each field
to the human, collects corrections, writes data/final_verified.json and
data/verification_report.json.

Usage:
  python pass3_human_check.py
"""

import os
import json
import copy
from pathlib import Path
from datetime import datetime

DATA_DIR        = Path("data")
PASS1_FILE      = DATA_DIR / "pass1_results.json"
PASS2_DIFFS     = DATA_DIR / "pass2_diffs.json"
FINAL_FILE      = DATA_DIR / "final_verified.json"
REPORT_FILE     = DATA_DIR / "verification_report.json"

HUMAN_SAMPLE_SIZE = 10

EDITABLE_FIELDS = [
    "one_liner",
    "auth_methods",
    "access",
    "api_surface",
    "api_breadth_note",
    "existing_mcp",
    "mcp_source",
    "buildable_verdict",
    "blocker",
    "notes",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path: Path) -> list | dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path: Path):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def fmt(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def parse_input(field: str, raw: str):
    """Parse human correction for a field (handles lists, bools, floats)."""
    raw = raw.strip()
    if field == "auth_methods":
        return [m.strip() for m in raw.split(",") if m.strip()]
    if field == "existing_mcp":
        return raw.lower() in ("yes", "true", "1", "y")
    if field == "confidence":
        try:
            return float(raw)
        except ValueError:
            return 0.5
    return raw

# ── App selection ─────────────────────────────────────────────────────────────

def select_human_sample(pass1: list[dict], diffs: list[dict]) -> list[dict]:
    """Prioritise apps with P1/P2 disagreements, fill rest with low-confidence."""
    diff_ids = sorted(
        [(d["id"], d["diff_count"]) for d in diffs],
        key=lambda x: -x[1]
    )
    priority_ids = [d_id for d_id, _ in diff_ids[:HUMAN_SAMPLE_SIZE]]
    pass1_map = {r["id"]: r for r in pass1}

    sample = [pass1_map[i] for i in priority_ids if i in pass1_map]

    if len(sample) < HUMAN_SAMPLE_SIZE:
        rest = sorted(
            [r for r in pass1 if r["id"] not in set(priority_ids)],
            key=lambda r: r.get("confidence", 1.0)
        )
        sample += rest[:HUMAN_SAMPLE_SIZE - len(sample)]

    return sample[:HUMAN_SAMPLE_SIZE]

# ── CLI loop ──────────────────────────────────────────────────────────────────

def review_app(record: dict) -> tuple[dict, dict]:
    """
    Interactive review of one app.
    Returns (corrected_record, correction_log).
    correction_log: {field: {"original": ..., "corrected": ..., "was_correct": bool}}
    """
    corrected = copy.deepcopy(record)
    correction_log = {}

    print("\n" + "=" * 70)
    print(f"  APP: {record['name']}  (id={record['id']}, cat={record['category']})")
    print(f"  Evidence URLs:")
    for url in record.get("evidence_urls", []):
        print(f"    - {url}")
    print("=" * 70)

    for field in EDITABLE_FIELDS:
        current = record.get(field, "")
        print(f"\n  Field:   {field}")
        print(f"  Current: {fmt(current)}")
        user_in = input("  → Type 'correct' to accept, or enter correction: ").strip()

        if user_in.lower() in ("correct", "c", "ok", ""):
            correction_log[field] = {
                "original":   current,
                "corrected":  current,
                "was_correct": True,
            }
        else:
            corrected[field] = parse_input(field, user_in)
            correction_log[field] = {
                "original":   current,
                "corrected":  corrected[field],
                "was_correct": False,
            }
            print(f"  ✏  Updated to: {fmt(corrected[field])}")

    corrected["verification_status"] = "human_verified"
    return corrected, correction_log

# ── Accuracy metrics ──────────────────────────────────────────────────────────

def compute_accuracy(correction_logs: dict[int, dict]) -> dict:
    """
    Returns:
      - pass1_accuracy: % fields agent got right (before human correction)
      - per_app breakdown
    """
    total   = 0
    correct = 0
    per_app = {}

    for app_id, log in correction_logs.items():
        app_total   = len(log)
        app_correct = sum(1 for v in log.values() if v["was_correct"])
        total   += app_total
        correct += app_correct
        per_app[app_id] = {
            "total_fields":   app_total,
            "correct_fields": app_correct,
            "accuracy":       round(app_correct / app_total * 100, 1) if app_total else 0,
        }

    return {
        "pass1_raw_accuracy_pct": round(correct / total * 100, 1) if total else 0,
        "total_fields_checked":   total,
        "total_fields_correct":   correct,
        "per_app": per_app,
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    if not PASS1_FILE.exists():
        print("ERROR: data/pass1_results.json not found. Run pass1_research.py first.")
        return

    pass1 = load_json(PASS1_FILE)
    pass1_map = {r["id"]: r for r in pass1}

    # Load diffs if available
    diffs = []
    if PASS2_DIFFS.exists():
        diffs = load_json(PASS2_DIFFS)
    else:
        print("Warning: pass2_diffs.json not found — selecting by confidence only")

    sample = select_human_sample(pass1, diffs)

    print(f"\nPass 3 Human Verification — reviewing {len(sample)} apps")
    print("For each field: type 'correct' (or press Enter) to accept,")
    print("or type a correction and press Enter.\n")

    correction_logs: dict[int, dict] = {}
    human_verified: dict[int, dict]  = {}

    for record in sample:
        corrected, log = review_app(record)
        correction_logs[record["id"]] = log
        human_verified[record["id"]]  = corrected

    # Build final_verified.json: human-verified records + untouched Pass 1 records
    final = {}
    for app_id, record in pass1_map.items():
        if app_id in human_verified:
            final[app_id] = human_verified[app_id]
        else:
            # keep existing verification_status (unverified or cross_checked)
            final[app_id] = record

    final_records = sorted(final.values(), key=lambda r: r["id"])
    save_json(final_records, FINAL_FILE)
    print(f"\n✓ Saved {len(final_records)} records → {FINAL_FILE}")

    # Accuracy
    accuracy = compute_accuracy(correction_logs)

    # Load pass2 agreement rate from diffs if available
    p2_rate = None
    if diffs:
        from pass2_verify import compute_agreement
        p2_rate = compute_agreement(diffs)

    # Before/after breakdown for human-checked apps
    wrong_examples = []
    for app_id, log in correction_logs.items():
        for field, entry in log.items():
            if not entry["was_correct"]:
                wrong_examples.append({
                    "app_id":   app_id,
                    "app_name": pass1_map.get(app_id, {}).get("name", "?"),
                    "field":    field,
                    "pass1_answer": fmt(entry["original"]),
                    "corrected_answer": fmt(entry["corrected"]),
                })

    report = {
        "generated_at":            datetime.utcnow().isoformat() + "Z",
        "human_checked_apps":      len(sample),
        "pass1_raw_accuracy_pct":  accuracy["pass1_raw_accuracy_pct"],
        "pass2_agreement_rate_pct": p2_rate,
        "final_accuracy_pct":      100.0,  # after human correction, verified fields are 100% accurate
        "total_fields_checked":    accuracy["total_fields_checked"],
        "total_fields_corrected":  accuracy["total_fields_checked"] - accuracy["total_fields_correct"],
        "wrong_examples":          wrong_examples[:8],  # top 8 for display
        "per_app_accuracy":        accuracy["per_app"],
    }

    save_json(report, REPORT_FILE)
    print(f"✓ Saved verification report → {REPORT_FILE}")

    print("\n" + "=" * 60)
    print(f"  PASS 1 RAW ACCURACY:   {accuracy['pass1_raw_accuracy_pct']:.1f}%")
    if p2_rate is not None:
        print(f"  PASS 2 AGREEMENT RATE: {p2_rate:.1f}%")
    print(f"  AFTER HUMAN CORRECTION: 100% (for {len(sample)} verified apps)")
    print(f"  WRONG FIELDS CORRECTED: {len(wrong_examples)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run()
