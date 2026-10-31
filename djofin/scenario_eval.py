"""Offline scenario-grounded assessment of read-only market anomaly findings.

Expected categories/checks are human-authored test fixtures, not financial truth.
Never used to authorize investment decisions.
"""
from djofin.ai_contract import validate_response, ContractError

def evaluate_scenario(request, response, expectations):
    """Compare an answer with an independently specified scenario rubric.

    expectations: mapping alert id -> {categories: [...], required_checks: [...],
    require_unknowns: bool}. A passing score is not proof of factual correctness.
    """
    try:
        verdict = validate_response(request, response)
    except ContractError:
        return {"contract_valid": False, "passed": False, "checks": [],
                "issues": ["invalid_contract"], "human_review_required": True}
    ids = {a["id"] for a in request["alerts"]}
    if not isinstance(expectations, dict) or set(expectations) != ids:
        raise ValueError("One expectation per alert required")
    findings = {f["alert_id"]: f for f in response["findings"]}
    checks, issues = [], []
    for ident in sorted(ids):
        rubric = expectations[ident]
        if not isinstance(rubric, dict) or set(rubric) != {
            "categories", "required_checks", "require_unknowns"}:
            raise ValueError("Invalid scenario rubric")
        if not isinstance(rubric["categories"], list) or not rubric["categories"]:
            raise ValueError("Expected categories must be nonempty")
        if not isinstance(rubric["required_checks"], list):
            raise ValueError("Expected checks must be a list")
        if type(rubric["require_unknowns"]) is not bool:
            raise ValueError("require_unknowns must be boolean")
        f = findings[ident]
        results = {
            "category_match": f["category"] in rubric["categories"],
            "required_checks_present": set(rubric["required_checks"]) <= set(f["checks"]),
            "uncertainty_reported": not rubric["require_unknowns"] or bool(f["unknowns"]),
        }
        checks.append({"alert_id": ident, **results})
        issues.extend(f"{ident}:{key}" for key, passed in results.items() if not passed)
    if verdict["flags"]:
        issues.append("contract_review_flags")
    return {"contract_valid": True, "passed": not issues, "checks": checks,
            "issues": issues, "human_review_required": True,
            "note": "Scenario rubric is an offline test, not proof of financial accuracy"}
