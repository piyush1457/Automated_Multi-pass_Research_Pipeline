"""
schema.py — canonical record shape for one researched app.
Import APP_SCHEMA or use make_empty_record() for a blank template.
"""

APP_SCHEMA = {
    "id": int,
    "name": str,
    "category": str,            # one of the 10 assignment categories
    "one_liner": str,           # what the app does (1 sentence)
    "auth_methods": list,       # subset of ["OAuth2","API Key","Basic","Token","Other"]
    "access": str,              # "self_serve_free" | "self_serve_trial" | "paid_plan_required" | "partner_gated" | "unclear"
    "api_surface": str,         # "rest" | "graphql" | "both" | "none_public"
    "api_breadth_note": str,    # 1-sentence description of endpoint coverage
    "existing_mcp": bool,       # True if Composio already has a toolkit for this app
    "mcp_source": str,          # "composio" | "official" | "community" | "none"
    "buildable_verdict": str,   # "yes" | "partial" | "no"
    "blocker": str,             # empty string if verdict is "yes"
    "evidence_urls": list,      # real URLs actually fetched — never fabricated
    "confidence": float,        # 0.0–1.0 agent self-rating
    "verification_status": str, # "unverified" | "cross_checked" | "human_verified"
    "notes": str,
}

VALID_AUTH_METHODS = ["OAuth2", "API Key", "Basic", "Token", "Other"]
VALID_ACCESS = ["self_serve_free", "self_serve_trial", "paid_plan_required", "partner_gated", "unclear"]
VALID_API_SURFACE = ["rest", "graphql", "both", "none_public"]
VALID_VERDICTS = ["yes", "partial", "no"]
VALID_MCP_SOURCE = ["composio", "official", "community", "none"]
VALID_VERIFICATION = ["unverified", "cross_checked", "human_verified"]


def make_empty_record(app_id: int, name: str, category: str) -> dict:
    """Return a blank record with safe defaults — used for error fallback."""
    return {
        "id": app_id,
        "name": name,
        "category": category,
        "one_liner": "",
        "auth_methods": [],
        "access": "unclear",
        "api_surface": "none_public",
        "api_breadth_note": "",
        "existing_mcp": False,
        "mcp_source": "none",
        "buildable_verdict": "no",
        "blocker": "docs not found via automated search",
        "evidence_urls": [],
        "confidence": 0.0,
        "verification_status": "unverified",
        "notes": "",
    }


def validate_record(record: dict) -> list[str]:
    """Return list of validation errors (empty list = valid)."""
    errors = []
    for method in record.get("auth_methods", []):
        if method not in VALID_AUTH_METHODS:
            errors.append(f"Invalid auth_method: {method}")
    if record.get("access") not in VALID_ACCESS:
        errors.append(f"Invalid access: {record.get('access')}")
    if record.get("api_surface") not in VALID_API_SURFACE:
        errors.append(f"Invalid api_surface: {record.get('api_surface')}")
    if record.get("buildable_verdict") not in VALID_VERDICTS:
        errors.append(f"Invalid buildable_verdict: {record.get('buildable_verdict')}")
    if record.get("mcp_source") not in VALID_MCP_SOURCE:
        errors.append(f"Invalid mcp_source: {record.get('mcp_source')}")
    if record.get("verification_status") not in VALID_VERIFICATION:
        errors.append(f"Invalid verification_status: {record.get('verification_status')}")
    if not isinstance(record.get("confidence"), (int, float)):
        errors.append("confidence must be a float")
    if not isinstance(record.get("existing_mcp"), bool):
        errors.append("existing_mcp must be a bool")
    return errors
