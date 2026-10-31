"""Strict contract for a read-only AI analyst of market-data anomalies.

The model may explain and suggest investigations, never rewrite data or trade.
No external model/API is required for contract validation.
"""
import json

SCHEMA_VERSION = "1.0"
ALLOWED_CATEGORIES = {"missing_data", "price_jump", "historical_revision", "invalid_data", "other"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}

def prepare_request(alerts, *, snapshot_sha256, ticker, as_of_utc):
    if not isinstance(alerts, list) or not all(isinstance(a, str) for a in alerts):
        raise ValueError("Alerts must be a list of strings")
    if len(snapshot_sha256) != 64 or any(c not in "0123456789abcdef" for c in snapshot_sha256):
        raise ValueError("Invalid snapshot digest")
    return {
        "schema_version": SCHEMA_VERSION,
        "mission": "Explain recorded anomalies; do not invent evidence or prices.",
        "ticker": ticker,
        "as_of_utc": as_of_utc,
        "snapshot_sha256": snapshot_sha256,
        "alerts": [{"id": f"alert-{i+1:04d}", "observation": a}
                   for i, a in enumerate(alerts)],
        "permissions": {"read_only": True, "can_trade": False,
                        "can_modify_prices": False, "can_modify_strategies": False}
    }

def validate_response(request, response):
    if not isinstance(response, dict) or response.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported AI response")
    expected = {a["id"] for a in request["alerts"]}
    findings = response.get("findings")
    if not isinstance(findings, list) or len(findings) != len(expected):
        raise ValueError("One finding required for every alert")
    seen = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("Finding must be an object")
        ident = finding.get("alert_id")
        if ident not in expected or ident in seen:
            raise ValueError("Unknown or repeated alert id")
        seen.add(ident)
        if finding.get("category") not in ALLOWED_CATEGORIES:
            raise ValueError("Unknown category")
        if finding.get("confidence") not in ALLOWED_CONFIDENCE:
            raise ValueError("Unknown confidence")
        for key in ("explanation", "unknowns", "checks", "evidence_ids"):
            if key not in finding:
                raise ValueError(f"Missing {key}")
        if not isinstance(finding["explanation"], str):
            raise ValueError("Explanation must be text")
        if not all(isinstance(finding[k], list) and all(isinstance(v, str) for v in finding[k])
                   for k in ("unknowns", "checks", "evidence_ids")):
            raise ValueError("Invalid lists")
        if any(e not in (ident, request["snapshot_sha256"]) for e in finding["evidence_ids"]):
            raise ValueError("Unverifiable evidence reference")
    if response.get("decision") != "human_review_only":
        raise ValueError("AI cannot authorize trading or data modification")
    return True

def serialize_request(request):
    return json.dumps(request, ensure_ascii=False, indent=2) + "\n"
