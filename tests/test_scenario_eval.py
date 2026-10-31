import unittest
from djofin.ai_contract import prepare_request
from djofin.scenario_eval import evaluate_scenario

class ScenarioEvalTests(unittest.TestCase):
    def setUp(self):
        self.req = prepare_request(
            [{"observation": "Synthetic ETF jump 16%; cause unverified",
              "dates": ["2026-10-30"]}],
            snapshot_sha256="a"*64, ticker="CW8.PA",
            as_of_utc="2026-10-31T10:00:00Z", snapshot_dates=["2026-10-30"])
        self.answer = {
            "schema_version": self.req["schema_version"],
            "request_digest": self.req["request_digest"],
            "decision": "human_review_only",
            "findings": [{
                "alert_id": "alert-0001", "category": "price_jump",
                "confidence": "low", "explanation": "Unverified anomaly: compare another public source before interpreting it.",
                "unknowns": ["Underlying cause unknown"],
                "checks": ["compare_second_source"],
                "evidence_dates": ["2026-10-30"]}]}
        self.rubric = {"alert-0001": {
            "categories": ["price_jump"], "required_checks": ["compare_second_source"],
            "require_unknowns": True}}

    def test_passes_grounded_rubric(self):
        self.assertTrue(evaluate_scenario(self.req, self.answer, self.rubric)["passed"])

    def test_rejects_wrong_financial_category_despite_valid_contract(self):
        self.answer["findings"][0]["category"] = "other"
        result = evaluate_scenario(self.req, self.answer, self.rubric)
        self.assertTrue(result["contract_valid"])
        self.assertFalse(result["passed"])
        self.assertIn("alert-0001:category_match", result["issues"])

    def test_missing_check_fails(self):
        self.answer["findings"][0]["checks"] = ["inspect_raw_rows"]
        self.assertFalse(evaluate_scenario(self.req, self.answer, self.rubric)["passed"])

    def test_missing_uncertainty_fails(self):
        self.answer["findings"][0]["unknowns"] = []
        self.assertFalse(evaluate_scenario(self.req, self.answer, self.rubric)["passed"])

    def test_malformed_response_fails(self):
        self.answer["decision"] = "trade"
        self.assertFalse(evaluate_scenario(self.req, self.answer, self.rubric)["contract_valid"])

if __name__ == "__main__":
    unittest.main()
