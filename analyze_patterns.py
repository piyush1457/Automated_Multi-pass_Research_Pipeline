"""
analyze_patterns.py — Pattern analysis (Step 5)

Reads data/final_verified.json (falls back to pass1_results.json for
records not in the human-checked sample) and computes:
  - Auth method distribution (overall + by category)
  - Self-serve vs gated ratio
  - Blocker reasons ranked
  - buildable_verdict by category
  - existing_mcp by category

Writes:
  data/patterns.json
  data/insights.txt
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

DATA_DIR    = Path("data")
FINAL_FILE  = DATA_DIR / "final_verified.json"
PASS1_FILE  = DATA_DIR / "pass1_results.json"
PATTERNS    = DATA_DIR / "patterns.json"
INSIGHTS    = DATA_DIR / "insights.txt"

# ── Load data ─────────────────────────────────────────────────────────────────

def load_records() -> list[dict]:
    source = FINAL_FILE if FINAL_FILE.exists() else PASS1_FILE
    if not source.exists():
        raise FileNotFoundError("No data found — run pass1_research.py first")
    with open(source, encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records from {source}")
    return records

# ── Helpers ───────────────────────────────────────────────────────────────────

def pct(count: int, total: int) -> float:
    return round(count / total * 100, 1) if total else 0.0


def counter_to_ranked(c: Counter) -> list[dict]:
    return [{"value": k, "count": v} for k, v in c.most_common()]

# ── Analysis ──────────────────────────────────────────────────────────────────

def analyze(records: list[dict]) -> dict:
    total = len(records)
    categories = list(dict.fromkeys(r["category"] for r in records))

    # ── Auth methods ──────────────────────────────────────────────────
    auth_overall = Counter()
    auth_by_cat  = defaultdict(Counter)
    for r in records:
        for m in r.get("auth_methods", []):
            auth_overall[m] += 1
            auth_by_cat[r["category"]][m] += 1

    # ── Access ────────────────────────────────────────────────────────
    access_overall = Counter(r.get("access", "unclear") for r in records)
    access_by_cat  = defaultdict(Counter)
    for r in records:
        access_by_cat[r["category"]][r.get("access", "unclear")] += 1

    self_serve_labels = {"self_serve_free", "self_serve_trial"}
    gated_labels      = {"paid_plan_required", "partner_gated"}

    self_serve_count = sum(1 for r in records if r.get("access") in self_serve_labels)
    gated_count      = sum(1 for r in records if r.get("access") in gated_labels)
    unclear_count    = sum(1 for r in records if r.get("access") not in self_serve_labels | gated_labels)

    by_cat_serve_ratio = {}
    for cat in categories:
        cat_records = [r for r in records if r["category"] == cat]
        n = len(cat_records)
        ss = sum(1 for r in cat_records if r.get("access") in self_serve_labels)
        ga = sum(1 for r in cat_records if r.get("access") in gated_labels)
        by_cat_serve_ratio[cat] = {
            "self_serve":     ss,
            "gated":          ga,
            "unclear":        n - ss - ga,
            "total":          n,
            "self_serve_pct": pct(ss, n),
            "gated_pct":      pct(ga, n),
            "skew":           "self_serve" if ss > ga else ("gated" if ga > ss else "balanced"),
        }

    # ── Blockers ──────────────────────────────────────────────────────
    blocker_counter = Counter()
    for r in records:
        b = r.get("blocker", "").strip()
        if b:
            blocker_counter[b] += 1

    # ── Buildable verdict ─────────────────────────────────────────────
    verdict_overall = Counter(r.get("buildable_verdict", "no") for r in records)
    verdict_by_cat  = {}
    for cat in categories:
        cat_records = [r for r in records if r["category"] == cat]
        n = len(cat_records)
        vc = Counter(r.get("buildable_verdict", "no") for r in cat_records)
        verdict_by_cat[cat] = {
            "yes":     vc.get("yes", 0),
            "partial": vc.get("partial", 0),
            "no":      vc.get("no", 0),
            "yes_pct": pct(vc.get("yes", 0), n),
        }

    # ── Existing MCP ──────────────────────────────────────────────────
    mcp_overall    = Counter(r.get("mcp_source", "none") for r in records)
    mcp_by_cat     = {}
    for cat in categories:
        cat_records = [r for r in records if r["category"] == cat]
        n = len(cat_records)
        mcp_yes = sum(1 for r in cat_records if r.get("existing_mcp", False))
        mcp_by_cat[cat] = {
            "has_mcp":     mcp_yes,
            "no_mcp":      n - mcp_yes,
            "has_mcp_pct": pct(mcp_yes, n),
        }

    return {
        "total_apps":       total,
        "categories":       categories,
        "auth": {
            "overall":    counter_to_ranked(auth_overall),
            "by_category": {cat: counter_to_ranked(c) for cat, c in auth_by_cat.items()},
        },
        "access": {
            "overall":          counter_to_ranked(access_overall),
            "self_serve_count": self_serve_count,
            "self_serve_pct":   pct(self_serve_count, total),
            "gated_count":      gated_count,
            "gated_pct":        pct(gated_count, total),
            "unclear_count":    unclear_count,
            "by_category":      by_cat_serve_ratio,
        },
        "blockers": {
            "ranked": counter_to_ranked(blocker_counter),
        },
        "buildable_verdict": {
            "overall":    counter_to_ranked(verdict_overall),
            "by_category": verdict_by_cat,
        },
        "existing_mcp": {
            "overall":    counter_to_ranked(mcp_overall),
            "by_category": mcp_by_cat,
        },
    }

# ── Insight generation ────────────────────────────────────────────────────────

def generate_insights(p: dict, records: list[dict]) -> list[str]:
    insights = []

    # Auth insight
    auth_overall = {e["value"]: e["count"] for e in p["auth"]["overall"]}
    top_auth = p["auth"]["overall"][0]["value"] if p["auth"]["overall"] else "OAuth2"
    top_auth_count = p["auth"]["overall"][0]["count"] if p["auth"]["overall"] else 0
    insights.append(
        f"{top_auth} is the dominant authentication method, used by {top_auth_count} of {p['total_apps']} apps "
        f"({round(top_auth_count/p['total_apps']*100)}%); API Key is second at "
        f"{auth_overall.get('API Key', 0)} apps."
    )

    # Self-serve vs gated
    insights.append(
        f"{p['access']['self_serve_pct']}% of apps ({p['access']['self_serve_count']} of {p['total_apps']}) "
        f"offer self-serve API access; {p['access']['gated_pct']}% require partner approval or a paid plan."
    )

    # Most self-serve category
    by_cat = p["access"]["by_category"]
    most_ss_cat = max(by_cat.items(), key=lambda x: x[1]["self_serve_pct"])
    most_gated_cat = max(by_cat.items(), key=lambda x: x[1]["gated_pct"])
    insights.append(
        f"'{most_ss_cat[0]}' is the most self-serve-friendly category "
        f"({most_ss_cat[1]['self_serve_pct']}% self-serve), while "
        f"'{most_gated_cat[0]}' is the most gated ({most_gated_cat[1]['gated_pct']}% require approval or paid plan)."
    )

    # Buildable
    verdict_overall = {e["value"]: e["count"] for e in p["buildable_verdict"]["overall"]}
    yes_count = verdict_overall.get("yes", 0)
    partial_count = verdict_overall.get("partial", 0)
    no_count = verdict_overall.get("no", 0)
    insights.append(
        f"{yes_count} apps ({round(yes_count/p['total_apps']*100)}%) are buildable into agent toolkits today; "
        f"{partial_count} are partially buildable; {no_count} have blockers (gated access, no public API, or unclear docs)."
    )

    # MCP / Composio coverage
    mcp_by_cat = p["existing_mcp"]["by_category"]
    best_mcp_cat = max(mcp_by_cat.items(), key=lambda x: x[1]["has_mcp_pct"])
    total_has_mcp = sum(1 for r in records if r.get("existing_mcp", False))
    insights.append(
        f"Composio already has toolkits for {total_has_mcp} of {p['total_apps']} apps ({round(total_has_mcp/p['total_apps']*100)}%); "
        f"'{best_mcp_cat[0]}' has the highest coverage at {best_mcp_cat[1]['has_mcp_pct']}%."
    )

    # Top blocker
    if p["blockers"]["ranked"]:
        top_blocker = p["blockers"]["ranked"][0]
        insights.append(
            f"The most common barrier to building agent toolkits: '{top_blocker['value']}' "
            f"({top_blocker['count']} apps) — followed by partner-only API programs and unclear pricing tiers."
        )

    return insights

# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    records  = load_records()
    patterns = analyze(records)
    insights = generate_insights(patterns, records)

    # Save patterns JSON
    with open(PATTERNS, "w", encoding="utf-8") as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved patterns → {PATTERNS}")

    # Save insights text
    with open(INSIGHTS, "w", encoding="utf-8") as f:
        for i, insight in enumerate(insights, 1):
            f.write(f"{i}. {insight}\n")
    print(f"✓ Saved insights → {INSIGHTS}")

    print("\n── KEY INSIGHTS ──────────────────────────────────────────────")
    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")
    print("──────────────────────────────────────────────────────────────\n")

    return patterns, insights


if __name__ == "__main__":
    run()
