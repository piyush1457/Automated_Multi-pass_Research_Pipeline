# Composio Toolkit Research — 100 Apps

An automated, multi-pass research pipeline that investigates 100 named apps and determines, for each:
- **Auth method** (OAuth2, API Key, Basic, Token)
- **Developer access model** (self-serve free/trial vs. paid plan vs. partner-gated)
- **API surface** (REST, GraphQL, both, or none public)
- **Agent toolkit buildability** verdict with blockers explained
- **Composio MCP coverage** (does Composio already have a toolkit for this app?)

The pipeline runs three passes: an automated bulk research pass (DuckDuckGo + Groq LLM), an independent cross-check pass, and a human verification CLI. Final results are aggregated into pattern insights and presented in a single self-contained `index.html` deliverable.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in your keys:

```
GROQ_API_KEY=your_groq_key         # console.groq.com — free tier
COMPOSIO_API_KEY=your_composio_key # app.composio.dev — free tier
TAVILY_API_KEY=your_tavily_key     # app.tavily.com  — optional, fallback search
```

**Never commit `.env` — it is already in `.gitignore`.**

---

## Running the pipeline

### Step 1 — Smoke test (first 5 apps)

```bash
python pass1_research.py --smoke
```

Verify the output looks sane in `data/pass1_results.json`, then run the full batch:

```bash
python pass1_research.py
```

To resume after a crash (e.g. from app 42 onwards):
```bash
python pass1_research.py --from=42
```

### Step 2 — Cross-check (Pass 2)

```bash
python pass2_verify.py
```

Selects 20 apps (10 lowest-confidence + 10 random), re-researches independently,
diffs results, prints agreement rate.

### Step 3 — Human verification (Pass 3)

```bash
python pass3_human_check.py
```

Interactive CLI — for each of ~10 apps, you'll see the agent's answer per field
plus the evidence URL. Type `correct` to accept or type a correction.

### Step 4 — Pattern analysis

```bash
python analyze_patterns.py
```

### Step 5 — Generate final deliverable

```bash
python generate_html.py
```

Then open in your browser:
```bash
start index.html   # Windows
open index.html    # macOS
```

---

## Output files

| File | Description |
|---|---|
| `data/pass1_results.json` | 100 app records from Pass 1 |
| `data/pass2_diffs.json` | Field-level diffs for 20 sampled apps |
| `data/final_verified.json` | Merged: human-verified records + remaining Pass 1 |
| `data/patterns.json` | Aggregated pattern analysis |
| `data/insights.txt` | 4-6 plain-English insight bullets |
| `data/verification_report.json` | Before/after accuracy numbers |
| `logs/pass1.log` | Per-app status log |
| `index.html` | Self-contained final deliverable |

---

## Known limitations

- **Rate limits**: Groq's free tier has per-minute request caps. The pipeline adds 3-second delays between calls and retries with exponential backoff. Very large batches may take 20–40 minutes.
- **DuckDuckGo reliability**: DDG occasionally blocks or throttles. If more than ~5 apps fail search, enable Tavily as the primary by setting `TAVILY_API_KEY`.
- **JavaScript-heavy docs**: Pages that load content via JS (e.g. some Swagger UIs) may return sparse text. Affected apps are marked with low confidence and `notes` explaining this.
- **Partner-gated apps**: Apps like WhatsApp Business, Salesforce Marketing Cloud, and Workday have API access that requires enterprise partnership review — the agent correctly marks these as `partner_gated` with `buildable_verdict: "no"`, but evidence may be thin if partner docs aren't publicly indexed.
- **Composio slug matching**: The SDK lookup uses fuzzy name matching. If a Composio toolkit uses an unexpected slug, it may be missed and appear as `mcp_source: "none"` when it should be `"composio"`.

---

## Viewing the deliverable

```bash
start index.html      # Windows — opens directly in your default browser
```

Or deploy as a static file to any CDN (Vercel, Netlify, GitHub Pages) — it has no server-side dependencies.
