"""
pass1_research.py — Bulk research agent (Pass 1)

For each of the 100 apps:
  1. DuckDuckGo search for official API docs
  2. Fetch + clean up to 3 pages with requests/BS4
  3. Groq (llama-3.3-70b-versatile, JSON mode) to extract schema fields
  4. Composio SDK check for existing toolkit
  5. Incremental write to data/pass1_results.json
  6. Log to logs/pass1.log
"""

import os
import json
import time
import random
import logging
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIError
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from apps import APPS
from schema import make_empty_record, validate_record

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

GROQ_API_KEY    = os.environ["GROQ_API_KEY"]
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
TAVILY_API_KEY  = os.environ.get("TAVILY_API_KEY", "")

PRIMARY_MODEL   = "llama-3.1-8b-instant"
FALLBACK_MODEL  = "llama-3.1-8b-instant"
MAX_TEXT_WORDS  = 4000          # truncate fetched page text
MAX_FETCH_PAGES = 3
GROQ_SLEEP      = 3             # seconds between Groq calls (free-tier rate limit)
REQUEST_TIMEOUT = 15            # seconds for HTTP fetches
MAX_GROQ_RETRIES = 4

DATA_DIR = Path("data")
LOGS_DIR = Path("logs")
PASS1_FILE = DATA_DIR / "pass1_results.json"
LOG_FILE   = LOGS_DIR / "pass1.log"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ── Groq client ───────────────────────────────────────────────────────────────

groq_client = Groq(api_key=GROQ_API_KEY)

# ── Composio toolkit check ────────────────────────────────────────────────────

_composio_app_names: list[str] | None = None


def _load_composio_apps() -> list[str]:
    """
    Load Composio supported app slugs from the SDK stub file.
    Avoids the deprecated v1 REST API (returns HTTP 410).
    Falls back to an empty list if the stub cannot be read.
    """
    global _composio_app_names
    if _composio_app_names is not None:
        return _composio_app_names

    try:
        import re
        import composio.client.enums as _ce
        import os
        stub_path = os.path.join(os.path.dirname(_ce.__file__), "app.pyi")
        with open(stub_path, encoding="utf-8") as f:
            stub = f.read()
        # Extract lines like:   HUBSPOT: "App"
        slugs = re.findall(r"^    ([A-Z][A-Z0-9_]+): .App.", stub, re.MULTILINE)
        # Store both UPPER_CASE and lowercased-no-underscore variants
        _composio_app_names = [
            s.lower() for s in slugs
        ] + [
            s.lower().replace("_", "") for s in slugs
        ]
        log.info(f"Loaded {len(slugs)} Composio app slugs from SDK stub")
    except Exception as e:
        log.warning(f"Could not read Composio stub file: {e}")
        _composio_app_names = []
    return _composio_app_names


def check_composio_toolkit(slug: str, name: str) -> tuple[bool, str]:
    """
    Returns (existing_mcp: bool, mcp_source: str).
    Checks slug and app name against the Composio app registry.
    """
    composio_apps = _load_composio_apps()
    slug_lower = slug.lower().replace("_", "").replace("-", "")
    name_lower = name.lower().replace(" ", "").replace("-", "")

    for entry in composio_apps:
        entry_clean = entry.lower().replace("_", "").replace("-", "").replace(" ", "")
        if entry_clean == slug_lower or entry_clean == name_lower:
            return True, "composio"

    return False, "none"

# ── DuckDuckGo / Tavily search ────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """DuckDuckGo search — returns list of {title, href, body}."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        log.warning(f"DuckDuckGo failed for '{query}': {e}")
        return []


def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """Tavily fallback search."""
    if not TAVILY_API_KEY:
        return []
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(query, max_results=max_results)
        return [
            {"href": r.get("url", ""), "title": r.get("title", ""), "body": r.get("content", "")}
            for r in response.get("results", [])
        ]
    except Exception as e:
        log.warning(f"Tavily failed for '{query}': {e}")
        return []


def search(query: str, max_results: int = 5) -> list[dict]:
    """Try Tavily first if key is present, fallback to DuckDuckGo."""
    if TAVILY_API_KEY:
        results = tavily_search(query, max_results)
        if results:
            return results
    return ddg_search(query, max_results)

# ── Page fetch + clean ────────────────────────────────────────────────────────

def fetch_and_clean(url: str) -> tuple[str, str]:
    """
    Fetch a URL and return (cleaned_text, canonical_url).
    Strips nav/footer/script/style; truncates to MAX_TEXT_WORDS words.
    Returns ("", url) on failure.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        canonical = resp.url
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # normalise whitespace
        text = re.sub(r"\s+", " ", text).strip()
        words = text.split()
        if len(words) > MAX_TEXT_WORDS:
            text = " ".join(words[:MAX_TEXT_WORDS]) + " [TRUNCATED]"
        return text, canonical
    except Exception as e:
        log.warning(f"  Fetch failed for {url}: {e}")
        return "", url

# ── Groq extraction ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a precise technical research agent. Given page content fetched from an app's developer documentation, extract exactly the following JSON fields. Output ONLY valid JSON — no markdown fences, no prose, no extra keys.

Required JSON fields:
{
  "one_liner": "<1-sentence description of what the app does>",
  "auth_methods": ["<subset of: OAuth2, API Key, Basic, Token, Other>"],
  "access": "<one of: self_serve_free | self_serve_trial | paid_plan_required | partner_gated | unclear>",
  "api_surface": "<one of: rest | graphql | both | none_public>",
  "api_breadth_note": "<1-sentence on endpoint coverage, e.g. '40+ endpoints covering contacts, deals, pipelines'>",
  "buildable_verdict": "<one of: yes | partial | no>",
  "blocker": "<empty string if verdict is yes; otherwise reason>",
  "confidence": <float 0.0-1.0>,
  "notes": "<any caveats or extra context>"
}

Rules:
- Only state what is explicitly in the provided content. Do NOT guess.
- Use "unclear" for access if pricing/gating is not mentioned in the content.
- Set confidence low (<=0.4) if the content is sparse or off-topic.
- buildable_verdict = "yes" means an agent could use this API today with self-serve access and clear docs.
- buildable_verdict = "partial" means partially possible (e.g. some endpoints accessible, or trial needed).
- buildable_verdict = "no" means API is gated, not public, or has no usable surface.
"""

def call_groq(app_name: str, fetched_pages: list[tuple[str, str]], model: str = PRIMARY_MODEL) -> dict:
    """
    Call Groq with the combined page text and return the extracted dict.
    fetched_pages: list of (cleaned_text, url)
    """
    combined = ""
    for text, url in fetched_pages:
        if text:
            combined += f"\n\n--- SOURCE: {url} ---\n{text}"

    if not combined.strip():
        return {}

    user_content = (
        f"App name: {app_name}\n\n"
        f"Fetched documentation content:\n{combined[:12000]}"  # ~12k chars safety cap
    )

    for attempt in range(MAX_GROQ_RETRIES):
        try:
            response = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1024,
            )
            raw = response.choices[0].message.content
            return json.loads(raw)
        except RateLimitError as e:
            err_msg = str(e)
            # Try to parse wait time from error message (e.g., "try again in 31s")
            wait = 10  # default short wait
            match = re.search(r"try again in ([0-9\.]+)\s*s", err_msg)
            if match:
                wait = float(match.group(1)) + 1.5
            else:
                match_m = re.search(r"try again in ([0-9\.]+)\s*m", err_msg)
                if match_m:
                    wait = float(match_m.group(1)) * 60 + 5.0
            
            log.warning(f"  Rate limit hit — sleeping {wait:.1f}s (attempt {attempt+1})")
            time.sleep(wait)
            if model == PRIMARY_MODEL:
                log.warning(f"  Switching immediately to fallback model: {FALLBACK_MODEL}")
                model = FALLBACK_MODEL
        except json.JSONDecodeError as e:
            log.warning(f"  JSON parse error (attempt {attempt+1}): {e}")
            time.sleep(2)
        except APIError as e:
            log.warning(f"  Groq API error (attempt {attempt+1}): {e}")
            time.sleep(5)
    return {}

# ── Incremental save ──────────────────────────────────────────────────────────

def load_existing_results() -> dict[int, dict]:
    """Load existing pass1_results.json keyed by app id."""
    if not PASS1_FILE.exists():
        return {}
    try:
        with open(PASS1_FILE, encoding="utf-8") as f:
            records = json.load(f)
        return {r["id"]: r for r in records}
    except Exception:
        return {}


def save_results(results: dict[int, dict]):
    """Overwrite pass1_results.json with current state."""
    records = sorted(results.values(), key=lambda r: r["id"])
    tmp = PASS1_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    tmp.replace(PASS1_FILE)

# ── Per-app research ──────────────────────────────────────────────────────────

def research_app(app: dict) -> dict:
    """Full research pipeline for one app. Returns a schema-compliant record."""
    app_id   = app["id"]
    name     = app["name"]
    slug     = app["slug"]
    category = app["category"]

    log.info(f"[{app_id:03d}/100] Starting: {name}")

    record = make_empty_record(app_id, name, category)

    # 1. Search
    queries = [
        f'"{name}" API documentation developer',
        f'"{name}" REST API authentication docs',
    ]
    search_results = []
    for q in queries:
        results = search(q, max_results=4)
        search_results.extend(results)
        if len(search_results) >= 3:
            break

    if not search_results:
        log.warning(f"  No search results found — marking unclear")
        record["blocker"] = "no search results returned"
        return record

    # 2. Pick best URLs (prefer official docs, auth, pricing pages)
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

    # 3. Fetch pages
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
        else:
            record["blocker"] = "page fetches returned no content"
            return record

    # 4. LLM extraction
    time.sleep(GROQ_SLEEP)  # respect rate limit
    extracted = call_groq(name, fetched_pages)

    if not extracted:
        log.warning(f"  Groq extraction returned nothing")
        record["blocker"] = "LLM extraction failed"
        return record

    # Merge extracted fields into record
    for field in ["one_liner", "auth_methods", "access", "api_surface",
                  "api_breadth_note", "buildable_verdict", "blocker",
                  "confidence", "notes"]:
        if field in extracted:
            record[field] = extracted[field]

    # Coerce + normalise auth_methods
    AUTH_ALIASES = {
        "oauth 2.0": "OAuth2", "oauth2.0": "OAuth2", "oauth": "OAuth2",
        "oauth2": "OAuth2", "apikey": "API Key", "api_key": "API Key",
        "token": "Token", "bearer": "Token", "basic auth": "Basic",
        "basic authentication": "Basic",
    }
    if isinstance(record["auth_methods"], str):
        record["auth_methods"] = [record["auth_methods"]]
    normalised = []
    for m in record["auth_methods"]:
        key = m.strip().lower()
        normalised.append(AUTH_ALIASES.get(key, m.strip()))
    record["auth_methods"] = list(dict.fromkeys(normalised))  # dedup, preserve order

    if not isinstance(record["confidence"], float):
        try:
            record["confidence"] = float(record["confidence"])
        except (TypeError, ValueError):
            record["confidence"] = 0.5
    record["confidence"] = max(0.0, min(1.0, record["confidence"]))

    # 5. Composio MCP check
    existing_mcp, mcp_source = check_composio_toolkit(slug, name)
    record["existing_mcp"] = existing_mcp
    record["mcp_source"]   = mcp_source

    # 6. Evidence URLs (real fetched pages only)
    record["evidence_urls"] = fetched_urls

    # Upgrade verification status since we actually fetched content
    record["verification_status"] = "unverified"

    errors = validate_record(record)
    if errors:
        log.warning(f"  Validation issues: {errors}")

    log.info(
        f"  ✓ Done — verdict={record['buildable_verdict']}, "
        f"access={record['access']}, "
        f"mcp={record['existing_mcp']}, "
        f"confidence={record['confidence']:.2f}"
    )
    return record

# ── Main ──────────────────────────────────────────────────────────────────────

def run(smoke_test: bool = False, start_from: int = 1):
    """
    Run Pass 1.
    smoke_test=True → only process the first 5 apps.
    start_from → resume from this app id (1-indexed).
    """
    apps_to_run = APPS if not smoke_test else APPS[:5]
    apps_to_run = [a for a in apps_to_run if a["id"] >= start_from]

    results = load_existing_results()
    log.info(f"Loaded {len(results)} existing results; running {len(apps_to_run)} apps")

    # Pre-load Composio app list once
    _load_composio_apps()

    for app in apps_to_run:
        app_id = app["id"]
        if app_id in results:
            log.info(f"[{app_id:03d}] Already done — skipping")
            continue
        try:
            record = research_app(app)
        except Exception as e:
            log.error(f"  Unexpected error for {app['name']}: {e}")
            record = make_empty_record(app_id, app["name"], app["category"])
            record["blocker"] = f"unexpected error: {e}"

        results[app_id] = record
        save_results(results)
        log.info(f"  Saved record {app_id}")

        # Small courtesy delay between apps
        time.sleep(1)

    log.info(f"Pass 1 complete. {len(results)} records in {PASS1_FILE}")


if __name__ == "__main__":
    import sys
    smoke = "--smoke" in sys.argv
    resume_from = 1
    for arg in sys.argv[1:]:
        if arg.startswith("--from="):
            resume_from = int(arg.split("=")[1])
    run(smoke_test=smoke, start_from=resume_from)
