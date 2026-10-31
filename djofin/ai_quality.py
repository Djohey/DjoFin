"""Offline quality checks for DjoFin AI findings; no model calls.

Heuristics are review signals, not proof of financial correctness.
"""
from djofin.ai_contract import validate_response, ContractError

def assess_analysis(request, response, usage=None):
    """Score explainability and uncertainty after strict contract validation."""
    try:
        verdict = validate_response(request, response)
    except ContractError as exc:
        return {"contract_valid": False, "score": 0, "issues": ["invalid_contract"],
                "review_required": True}
    findings = response["findings"]
    issues = [flag["flag"] for flag in verdict["flags"]]
    score = 100
    for finding in findings:
        if not finding["unknowns"]:
            issues.append("missing_unknowns")
            score -= 20
        if len(finding["explanation"].strip()) < 40:
            issues.append("shallow_explanation")
            score -= 15
        if not finding["evidence_dates"]:
            issues.append("no_dated_evidence")
            score -= 10
        if finding["confidence"] == "high":
            issues.append("high_confidence_needs_review")
            score -= 10
        if finding["checks"] == ["no_check_needed"] and finding["unknowns"]:
            issues.append("unknowns_without_followup")
            score -= 15
    score -= 15 * len(verdict["flags"])
    total = None
    if isinstance(usage, dict):
        raw = usage.get("total")
        if type(raw) is int and raw >= 0:
            total = raw
    return {"contract_valid": True, "score": max(0, score),
            "issues": sorted(set(issues)), "review_required": True,
            "total_tokens": total, "tokens_per_finding": (
                round(total / len(findings), 2) if total is not None and findings else None),
            "note": "Heuristic only; factual accuracy and sources require independent verification"}
