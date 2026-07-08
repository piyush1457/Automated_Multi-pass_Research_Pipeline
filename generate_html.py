"""
generate_html.py — Produces index.html from the pipeline outputs.

Run after all passes and analyze_patterns.py are complete.
Embeds all data as inline JSON — no server needed, opens directly in browser.
"""

import json
from pathlib import Path

DATA_DIR   = Path("data")
FINAL_FILE = DATA_DIR / "final_verified.json"
PASS1_FILE = DATA_DIR / "pass1_results.json"
PATTERNS   = DATA_DIR / "patterns.json"
INSIGHTS   = DATA_DIR / "insights.txt"
REPORT     = DATA_DIR / "verification_report.json"
OUT_FILE   = Path("index.html")

# ── Load data ─────────────────────────────────────────────────────────────────

def load_or(path, default):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def load_insights():
    if INSIGHTS.exists():
        with open(INSIGHTS, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return ["Run analyze_patterns.py to generate insights."]


def main():
    records  = load_or(FINAL_FILE, None) or load_or(PASS1_FILE, [])
    patterns = load_or(PATTERNS, {})
    report   = load_or(REPORT, {})
    insights = load_insights()

    records_json  = json.dumps(records,  ensure_ascii=False)
    patterns_json = json.dumps(patterns, ensure_ascii=False)
    report_json   = json.dumps(report,   ensure_ascii=False)
    insights_json = json.dumps(insights, ensure_ascii=False)

    categories = sorted(list({r.get("category", "") for r in records}))
    cats_json  = json.dumps(categories, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Composio Toolkit Research — 100 Apps</title>
<meta name="description" content="Agent-driven research into 100 apps: auth methods, API access, and buildability as Composio toolkits — verified across 3 passes."/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<style>
/* ── Reset & Base ──────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --bg:      #0a0b0f;
  --surface: #12141a;
  --card:    #1a1d27;
  --border:  #252836;
  --accent:  #6c63ff;
  --accent2: #a78bfa;
  --green:   #22c55e;
  --amber:   #f59e0b;
  --red:     #ef4444;
  --text:    #e2e8f0;
  --muted:   #64748b;
  --radius:  12px;
  --font:    'Inter', system-ui, sans-serif;
  --mono:    'JetBrains Mono', monospace;
}}
html {{ scroll-behavior: smooth; }}
body {{
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 15px;
  line-height: 1.6;
  min-height: 100vh;
}}
a {{ color: var(--accent2); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* ── Layout ─────────────────────────────────────────────── */
.page-wrap {{
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px 80px;
}}
section {{ margin-bottom: 72px; }}

/* ── Hero ────────────────────────────────────────────────── */
.hero {{
  text-align: center;
  padding: 80px 24px 56px;
  background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(108,99,255,.18) 0%, transparent 70%);
  border-bottom: 1px solid var(--border);
  margin-bottom: 64px;
}}
.hero-badge {{
  display: inline-block;
  background: rgba(108,99,255,.15);
  border: 1px solid rgba(108,99,255,.35);
  color: var(--accent2);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .08em;
  text-transform: uppercase;
  padding: 4px 14px;
  border-radius: 20px;
  margin-bottom: 20px;
}}
.hero h1 {{
  font-size: clamp(2rem, 5vw, 3.2rem);
  font-weight: 700;
  letter-spacing: -.02em;
  background: linear-gradient(135deg, #fff 30%, var(--accent2) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
}}
.hero p {{
  color: var(--muted);
  font-size: 1.05rem;
  max-width: 600px;
  margin: 0 auto 32px;
}}
.stat-row {{
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
  margin-top: 36px;
}}
.stat-item {{
  text-align: center;
}}
.stat-num {{
  font-size: 2.4rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}}
.stat-label {{
  font-size: 12px;
  color: var(--muted);
  margin-top: 4px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: .06em;
}}

/* ── Section headers ──────────────────────────────────────── */
.section-header {{
  margin-bottom: 28px;
}}
.section-num {{
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: .1em;
  margin-bottom: 6px;
}}
.section-title {{
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -.015em;
}}
.section-sub {{
  color: var(--muted);
  margin-top: 6px;
  font-size: .9rem;
}}

/* ── Insight cards ──────────────────────────────────────────── */
.insights-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}}
.insight-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 24px;
  position: relative;
  overflow: hidden;
  transition: border-color .2s, transform .2s;
}}
.insight-card:hover {{
  border-color: var(--accent);
  transform: translateY(-2px);
}}
.insight-card::before {{
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--accent), var(--accent2));
  border-radius: 3px 0 0 3px;
}}
.insight-num {{
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: .08em;
  margin-bottom: 8px;
}}
.insight-text {{
  font-size: .9rem;
  line-height: 1.65;
  color: var(--text);
}}

/* ── Filters ────────────────────────────────────────────────── */
.filters {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
}}
.filter-label {{
  font-size: 12px;
  color: var(--muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
}}
select, input[type=text] {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  padding: 8px 12px;
  font-family: var(--font);
  font-size: 13px;
  outline: none;
  transition: border-color .2s;
}}
select:focus, input[type=text]:focus {{
  border-color: var(--accent);
}}
#search-box {{
  width: 220px;
}}
.result-count {{
  font-size: 12px;
  color: var(--muted);
  margin-left: auto;
}}

/* ── Table ──────────────────────────────────────────────────── */
.table-wrap {{
  overflow-x: auto;
  border-radius: var(--radius);
  border: 1px solid var(--border);
}}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}}
thead {{
  background: var(--surface);
  position: sticky;
  top: 0;
  z-index: 2;
}}
th {{
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .07em;
  white-space: nowrap;
  cursor: pointer;
  user-select: none;
  transition: color .15s;
}}
th:hover {{ color: var(--text); }}
th.sort-asc::after  {{ content: ' ↑'; color: var(--accent); }}
th.sort-desc::after {{ content: ' ↓'; color: var(--accent); }}
td {{
  padding: 11px 14px;
  border-top: 1px solid var(--border);
  vertical-align: top;
}}
tr:hover td {{ background: rgba(255,255,255,.025); }}

/* ── Badges ──────────────────────────────────────────────────── */
.badge {{
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;
}}
.badge-yes     {{ background: rgba(34,197,94,.15);  color: #4ade80; }}
.badge-partial {{ background: rgba(245,158,11,.15); color: #fbbf24; }}
.badge-no      {{ background: rgba(239,68,68,.15);  color: #f87171; }}
.badge-self    {{ background: rgba(108,99,255,.15); color: #a78bfa; }}
.badge-gated   {{ background: rgba(239,68,68,.12);  color: #fca5a5; }}
.badge-trial   {{ background: rgba(245,158,11,.12); color: #fcd34d; }}
.badge-paid    {{ background: rgba(239,68,68,.12);  color: #fca5a5; }}
.badge-unclear {{ background: rgba(100,116,139,.15);color: #94a3b8; }}
.badge-mcp     {{ background: rgba(34,197,94,.15);  color: #4ade80; border: 1px solid rgba(34,197,94,.3); }}
.badge-none    {{ background: rgba(100,116,139,.1); color: #64748b; }}
.auth-pill {{
  display: inline-block;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  background: rgba(167,139,250,.12);
  color: var(--accent2);
  margin: 2px 2px 2px 0;
}}
.cat-label {{
  font-size: 11px;
  color: var(--muted);
}}
.conf-bar {{
  width: 60px;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
  display: inline-block;
  vertical-align: middle;
}}
.conf-fill {{
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  border-radius: 3px;
}}

/* ── Pipeline diagram ────────────────────────────────────────── */
.pipeline {{
  display: flex;
  align-items: center;
  gap: 0;
  flex-wrap: wrap;
  margin: 32px 0;
  justify-content: center;
}}
.pipe-step {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 24px;
  width: 220px;
  text-align: center;
  position: relative;
  transition: border-color .2s;
}}
.pipe-step:hover {{ border-color: var(--accent); }}
.pipe-icon {{
  font-size: 2rem;
  margin-bottom: 10px;
}}
.pipe-title {{
  font-weight: 700;
  font-size: .9rem;
  margin-bottom: 6px;
}}
.pipe-desc {{
  font-size: .78rem;
  color: var(--muted);
  line-height: 1.5;
}}
.pipe-arrow {{
  width: 40px;
  text-align: center;
  font-size: 1.4rem;
  color: var(--muted);
  flex-shrink: 0;
}}
.pipe-human {{
  border-color: var(--amber) !important;
}}
.pipe-human .pipe-icon {{
  filter: none;
}}
.human-badge {{
  display: inline-block;
  background: rgba(245,158,11,.15);
  color: var(--amber);
  border: 1px solid rgba(245,158,11,.3);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 12px;
  margin-bottom: 8px;
}}

/* ── Accuracy ───────────────────────────────────────────────── */
.accuracy-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 36px;
}}
.acc-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 22px;
  text-align: center;
}}
.acc-val {{
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent2);
}}
.acc-label {{
  font-size: 12px;
  color: var(--muted);
  margin-top: 4px;
}}
.diff-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: var(--card);
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--border);
}}
.diff-table th {{
  background: var(--surface);
  padding: 10px 14px;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .07em;
  cursor: default;
}}
.diff-table td {{
  padding: 10px 14px;
  border-top: 1px solid var(--border);
}}
.diff-before {{
  color: #f87171;
  text-decoration: line-through;
  font-family: var(--mono);
  font-size: 12px;
}}
.diff-after {{
  color: #4ade80;
  font-family: var(--mono);
  font-size: 12px;
}}

/* ── Nav ─────────────────────────────────────────────────────── */
.top-nav {{
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(10,11,15,.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 0 32px;
}}
.nav-inner {{
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 28px;
  height: 52px;
}}
.nav-logo {{
  font-weight: 700;
  font-size: .9rem;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-right: 8px;
}}
.nav-link {{
  font-size: 13px;
  color: var(--muted);
  transition: color .15s;
  font-weight: 500;
}}
.nav-link:hover {{ color: var(--text); text-decoration: none; }}

/* ── Proof ───────────────────────────────────────────────────── */
.proof-box {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px 32px;
  display: flex;
  align-items: center;
  gap: 28px;
  flex-wrap: wrap;
}}
.proof-code {{
  font-family: var(--mono);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px 12px;
  font-size: 13px;
  color: var(--accent2);
}}

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 768px) {{
  .pipeline {{ flex-direction: column; }}
  .pipe-arrow {{ transform: rotate(90deg); }}
  .pipe-step {{ width: 100%; max-width: 300px; }}
}}
</style>
</head>
<body>

<nav class="top-nav">
  <div class="nav-inner">
    <span class="nav-logo">Composio Research</span>
    <a class="nav-link" href="#insights">Insights</a>
    <a class="nav-link" href="#matrix">Matrix</a>
    <a class="nav-link" href="#pipeline">Pipeline</a>
    <a class="nav-link" href="#verification">Verification</a>
    <a class="nav-link" href="#proof">Proof</a>
  </div>
</nav>

<!-- Hero -->
<div class="hero">
  <div class="page-wrap">
    <div class="hero-badge">Agent-Driven Research · 3-Pass Verification</div>
    <h1>100 Apps.<br/>One Agent. Zero Guesses.</h1>
    <p>An automated pipeline researched every app's auth method, API access model, and agent toolkit buildability — then verified itself through independent cross-checks and human review.</p>
    <div class="stat-row" id="hero-stats"></div>
  </div>
</div>

<div class="page-wrap">

<!-- ── Section 1: Insights ──────────────────────────────────── -->
<section id="insights">
  <div class="section-header">
    <div class="section-num">01 — Key Findings</div>
    <div class="section-title">Headline Patterns</div>
    <div class="section-sub">Derived from aggregated data across all 100 apps, post-verification.</div>
  </div>
  <div class="insights-grid" id="insights-grid"></div>
</section>

<!-- ── Section 2: Matrix ────────────────────────────────────── -->
<section id="matrix">
  <div class="section-header">
    <div class="section-num">02 — The Data</div>
    <div class="section-title">App Research Matrix</div>
    <div class="section-sub">Filter by category, access type, or verdict. Click column headers to sort.</div>
  </div>
  <div class="filters">
    <span class="filter-label">Filter:</span>
    <input type="text" id="search-box" placeholder="Search app name…"/>
    <select id="cat-filter">
      <option value="">All categories</option>
    </select>
    <select id="access-filter">
      <option value="">All access types</option>
      <option value="self_serve_free">Self-serve (free)</option>
      <option value="self_serve_trial">Self-serve (trial)</option>
      <option value="paid_plan_required">Paid plan required</option>
      <option value="partner_gated">Partner gated</option>
      <option value="unclear">Unclear</option>
    </select>
    <select id="verdict-filter">
      <option value="">All verdicts</option>
      <option value="yes">✓ Buildable</option>
      <option value="partial">~ Partial</option>
      <option value="no">✗ Blocked</option>
    </select>
    <span class="result-count" id="result-count"></span>
  </div>
  <div class="table-wrap">
    <table id="app-table">
      <thead>
        <tr>
          <th data-col="id">#</th>
          <th data-col="name">App</th>
          <th data-col="category">Category</th>
          <th data-col="auth_methods">Auth</th>
          <th data-col="access">Access</th>
          <th data-col="api_surface">API</th>
          <th data-col="buildable_verdict">Verdict</th>
          <th data-col="existing_mcp">MCP</th>
          <th data-col="confidence">Conf.</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>
</section>

<!-- ── Section 3: Pipeline ──────────────────────────────────── -->
<section id="pipeline">
  <div class="section-header">
    <div class="section-num">03 — Methodology</div>
    <div class="section-title">How the Agent Worked</div>
    <div class="section-sub">Three-pass architecture with an explicit human verification step.</div>
  </div>
  <div class="pipeline">
    <div class="pipe-step">
      <div class="pipe-title">Pass 1 — Research</div>
      <div class="pipe-desc">DuckDuckGo search + page fetch for 100 apps. Groq LLM extracts JSON schema fields. Composio SDK checks existing MCP coverage. Saves incrementally.</div>
    </div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step">
      <div class="pipe-title">Pass 2 — Cross-Check</div>
      <div class="pipe-desc">Independent re-extraction for 20 apps (10 lowest-confidence + 10 random). Different search queries, fresh LLM call. Fields diffed automatically.</div>
    </div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step pipe-human">
      <div class="human-badge">Human required</div>
      <div class="pipe-title">Pass 3 — Human Review</div>
      <div class="pipe-desc">CLI tool presents each field + evidence URL to a human reviewer. Corrections recorded. Produces final accuracy metrics and before/after comparison.</div>
    </div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step">
      <div class="pipe-title">Analysis</div>
      <div class="pipe-desc">Pattern aggregation across all 100 records. Auth, access, verdict, and MCP distributions by category. Insights generated automatically.</div>
    </div>
  </div>
  <div style="background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;margin-top:8px;">
    <p style="font-size:.9rem;color:var(--muted);">
      <strong style="color:var(--text);">Key design decision:</strong>
      Pass 2 uses deliberately different search query phrasing to avoid correlated errors — if both passes find the same wrong page, the diff would miss it. The 3-second inter-call delay and model fallback (llama-3.1-8b-instant) handle Groq's free-tier rate limits without crashing the batch.
    </p>
  </div>
</section>

<!-- ── Section 4: Verification ──────────────────────────────── -->
<section id="verification">
  <div class="section-header">
    <div class="section-num">04 — Accuracy</div>
    <div class="section-title">Verification — Shown Honestly</div>
    <div class="section-sub">Before/after accuracy numbers from Pass 3, plus concrete correction examples.</div>
  </div>
  <div class="accuracy-grid" id="acc-cards"></div>
  <h3 style="font-size:1rem;font-weight:600;margin-bottom:14px;">Where the Agent Was Wrong (Pass 1 vs Human)</h3>
  <table class="diff-table" id="diff-table">
    <thead>
      <tr>
        <th>App</th>
        <th>Field</th>
        <th>Pass 1 Answer</th>
        <th>Human Correction</th>
      </tr>
    </thead>
    <tbody id="diff-body"></tbody>
  </table>
</section>

<!-- ── Section 5: Proof ─────────────────────────────────────── -->
<section id="proof">
  <div class="section-header">
    <div class="section-num">05 — Proof</div>
    <div class="section-title">Run It Yourself</div>
  </div>
  <div class="proof-box">
    <div style="flex:1;min-width:260px;">
      <p style="font-size:.9rem;color:var(--muted);margin-bottom:16px;">
        The full pipeline is open-source and reproducible. Clone the repo, set your API keys, and run the four-step pipeline in order.
      </p>
      <div style="display:flex;flex-direction:column;gap:8px;">
        <code class="proof-code">python pass1_research.py --smoke</code>
        <code class="proof-code">python pass2_verify.py</code>
        <code class="proof-code">python pass3_human_check.py</code>
        <code class="proof-code">python analyze_patterns.py</code>
        <code class="proof-code">python generate_html.py</code>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;gap:12px;align-items:flex-start;">
      <a href="https://github.com/piyush1457/Automated_Multi-pass_Research_Pipeline" target="_blank" style="display:inline-flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--border);padding:10px 18px;border-radius:8px;color:var(--text);font-size:13px;font-weight:600;transition:border-color .2s;" onmouseover="this.style.borderColor='#6c63ff'" onmouseout="this.style.borderColor='var(--border)'">
        View on GitHub
      </a>
      <button id="live-demo-btn" style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,#6c63ff,#a78bfa);border:none;padding:10px 18px;border-radius:8px;color:#fff;font-size:13px;font-weight:600;cursor:pointer;font-family:var(--font);transition:opacity .2s;" onmouseover="this.style.opacity='.85'" onmouseout="this.style.opacity='1'">
        View Research Snapshot (Salesforce)
      </button>
    </div>
  </div>
  <div id="live-demo-result" style="margin-top:16px;display:none;"></div>
</section>

</div><!-- /page-wrap -->

<!-- ── Embedded data ─────────────────────────────────────────── -->
<script>
const RECORDS  = {records_json};
const PATTERNS = {patterns_json};
const REPORT   = {report_json};
const INSIGHTS = {insights_json};
const CATEGORIES = {cats_json};
</script>

<script>
// ── Hero stats ──────────────────────────────────────────────
(function() {{
  const total    = RECORDS.length;
  const yes      = RECORDS.filter(r => r.buildable_verdict === 'yes').length;
  const hasMcp   = RECORDS.filter(r => r.existing_mcp).length;
  const selfServe= RECORDS.filter(r => r.access === 'self_serve_free' || r.access === 'self_serve_trial').length;
  const stats = [
    [total, 'Apps Researched'],
    [yes, 'Buildable Today'],
    [hasMcp, 'Have Composio MCP'],
    [selfServe, 'Self-Serve Access'],
  ];
  const el = document.getElementById('hero-stats');
  el.innerHTML = stats.map(([n, l]) =>
    `<div class="stat-item"><div class="stat-num">${{n}}</div><div class="stat-label">${{l}}</div></div>`
  ).join('');
}})();

// ── Insights ────────────────────────────────────────────────
(function() {{
  const grid = document.getElementById('insights-grid');
  grid.innerHTML = INSIGHTS.map((text, i) => `
    <div class="insight-card">
      <div class="insight-num">INSIGHT ${{String(i+1).padStart(2,'0')}}</div>
      <div class="insight-text">${{text.replace(/^\\d+\\.\\s*/,'').trim()}}</div>
    </div>
  `).join('');
}})();

// ── Category filter ─────────────────────────────────────────
(function() {{
  const sel = document.getElementById('cat-filter');
  CATEGORIES.forEach(c => {{
    const o = document.createElement('option');
    o.value = c; o.textContent = c;
    sel.appendChild(o);
  }});
}})();

// ── Table ────────────────────────────────────────────────────
(function() {{
  let sortCol = 'id', sortDir = 1;
  let filtered = [...RECORDS];

  function accessBadge(a) {{
    const map = {{
      'self_serve_free':   ['badge-self',  'Free'],
      'self_serve_trial':  ['badge-trial', 'Trial'],
      'paid_plan_required':['badge-paid',  'Paid'],
      'partner_gated':     ['badge-gated', 'Gated'],
      'unclear':           ['badge-unclear','?'],
    }};
    const [cls, label] = map[a] || ['badge-unclear', a || '?'];
    return `<span class="badge ${{cls}}">${{label}}</span>`;
  }}

  function verdictBadge(v) {{
    const map = {{ yes:'badge-yes', partial:'badge-partial', no:'badge-no' }};
    return `<span class="badge ${{map[v]||'badge-unclear'}}">${{v||'?'}}</span>`;
  }}

  function authPills(arr) {{
    if (!Array.isArray(arr)) arr = arr ? [arr] : [];
    return arr.map(m => `<span class="auth-pill">${{m}}</span>`).join('');
  }}

  function mcpBadge(existing, source) {{
    if (!existing) return `<span class="badge badge-none">None</span>`;
    return `<span class="badge badge-mcp">✓ ${{source||'mcp'}}</span>`;
  }}

  function confBar(c) {{
    const pct = Math.round((c || 0) * 100);
    return `<span class="conf-bar" title="${{pct}}%"><span class="conf-fill" style="width:${{pct}}%"></span></span> ${{pct}}%`;
  }}

  function render() {{
    const q   = document.getElementById('search-box').value.toLowerCase();
    const cat = document.getElementById('cat-filter').value;
    const acc = document.getElementById('access-filter').value;
    const ver = document.getElementById('verdict-filter').value;

    filtered = RECORDS.filter(r =>
      (!q   || r.name.toLowerCase().includes(q) || (r.one_liner||'').toLowerCase().includes(q)) &&
      (!cat || r.category === cat) &&
      (!acc || r.access === acc) &&
      (!ver || r.buildable_verdict === ver)
    );

    filtered.sort((a, b) => {{
      let av = a[sortCol], bv = b[sortCol];
      if (Array.isArray(av)) av = av.join(',');
      if (Array.isArray(bv)) bv = bv.join(',');
      if (av < bv) return -sortDir;
      if (av > bv) return  sortDir;
      return 0;
    }});

    document.getElementById('result-count').textContent =
      `${{filtered.length}} of ${{RECORDS.length}} apps`;

    const tbody = document.getElementById('table-body');
    tbody.innerHTML = filtered.map(r => `
      <tr>
        <td style="color:var(--muted);font-family:var(--mono);font-size:11px">${{r.id}}</td>
        <td>
          <strong style="font-size:13px">${{r.name}}</strong>
          ${{r.evidence_urls && r.evidence_urls[0]
            ? `<br><a href="${{r.evidence_urls[0]}}" target="_blank" style="font-size:10px;color:var(--muted)">docs ↗</a>`
            : ''}}
        </td>
        <td><span class="cat-label">${{r.category}}</span></td>
        <td>${{authPills(r.auth_methods)}}</td>
        <td>${{accessBadge(r.access)}}</td>
        <td><code style="font-size:11px;color:var(--accent2)">${{r.api_surface||'?'}}</code></td>
        <td>${{verdictBadge(r.buildable_verdict)}}</td>
        <td>${{mcpBadge(r.existing_mcp, r.mcp_source)}}</td>
        <td>${{confBar(r.confidence)}}</td>
      </tr>
    `).join('');
  }}

  // Sort on header click
  document.querySelectorAll('#app-table th[data-col]').forEach(th => {{
    th.addEventListener('click', () => {{
      const col = th.dataset.col;
      if (sortCol === col) sortDir *= -1;
      else {{ sortCol = col; sortDir = 1; }}
      document.querySelectorAll('#app-table th').forEach(t => t.classList.remove('sort-asc','sort-desc'));
      th.classList.add(sortDir === 1 ? 'sort-asc' : 'sort-desc');
      render();
    }});
  }});

  ['search-box','cat-filter','access-filter','verdict-filter'].forEach(id =>
    document.getElementById(id).addEventListener('input', render)
  );

  render();
}})();

// ── Accuracy cards ───────────────────────────────────────────
(function() {{
  const r = REPORT;
  const cards = [
    [r.pass1_raw_accuracy_pct != null ? r.pass1_raw_accuracy_pct + '%' : 'N/A', 'Pass 1 Raw Accuracy'],
    [r.pass2_agreement_rate_pct != null ? r.pass2_agreement_rate_pct + '%' : 'N/A', 'Pass 2 Agreement Rate'],
    [r.final_accuracy_pct != null ? r.final_accuracy_pct + '%' : 'N/A', 'After Human Correction'],
    [r.human_checked_apps || 0, 'Apps Human-Verified'],
    [r.total_fields_corrected || 0, 'Fields Corrected'],
  ];
  document.getElementById('acc-cards').innerHTML = cards.map(([v, l]) =>
    `<div class="acc-card"><div class="acc-val">${{v}}</div><div class="acc-label">${{l}}</div></div>`
  ).join('');

  const tbody = document.getElementById('diff-body');
  const examples = r.wrong_examples || [];
  if (examples.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="4" style="color:var(--muted);text-align:center;padding:20px">Run pass3_human_check.py to populate correction examples.</td></tr>';
  }} else {{
    tbody.innerHTML = examples.map(e => `
      <tr>
        <td style="font-weight:600">${{e.app_name}}</td>
        <td><code style="font-size:11px;color:var(--accent2)">${{e.field}}</code></td>
        <td><span class="diff-before">${{e.pass1_answer}}</span></td>
        <td><span class="diff-after">${{e.corrected_answer}}</span></td>
      </tr>
    `).join('');
  }}
}})();

// ── Live demo button ─────────────────────────────────────────
document.getElementById('live-demo-btn').addEventListener('click', function() {{
  const btn = this;
  const out = document.getElementById('live-demo-result');
  const demoApp = RECORDS[0];
  if (!demoApp) {{ out.textContent = 'No data loaded.'; out.style.display='block'; return; }}
  btn.textContent = 'Loading…';
  btn.disabled = true;
  setTimeout(() => {{
    out.style.display = 'block';
    out.innerHTML = `
      <div style="background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;">
        <p style="font-size:12px;color:var(--muted);margin-bottom:12px;">Research snapshot from embedded data (Pass 1 result for: <strong style="color:var(--text)">${{demoApp.name}}</strong>)</p>
        <pre style="font-family:var(--mono);font-size:12px;color:var(--accent2);white-space:pre-wrap;overflow-x:auto">${{JSON.stringify({{
          name: demoApp.name,
          auth_methods: demoApp.auth_methods,
          access: demoApp.access,
          api_surface: demoApp.api_surface,
          buildable_verdict: demoApp.buildable_verdict,
          existing_mcp: demoApp.existing_mcp,
          confidence: demoApp.confidence,
          evidence_urls: demoApp.evidence_urls,
        }}, null, 2)}}</pre>
      </div>`;
    btn.textContent = 'View Research Snapshot (Salesforce)';
    btn.disabled = false;
  }}, 600);
}});
</script>
</body>
</html>"""

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved -> {OUT_FILE}  ({OUT_FILE.stat().st_size // 1024} KB)")
    print("  Open with: start index.html")


if __name__ == "__main__":
    main()
