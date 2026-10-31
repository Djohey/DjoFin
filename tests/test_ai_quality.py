import unittest
from djofin.ai_contract import prepare_request
from djofin.ai_quality import assess_analysis

class QualityTests(unittest.TestCase):
    def setUp(self):
        self.request = prepare_request(
            [{"observation": "Synthetic ETF price jump 16%", "dates": ["2026-10-30"]}],
            snapshot_sha256="a"*64, ticker="CW8.PA",
            as_of_utc="2026-10-31T10:00:00Z", snapshot_dates=["2026-10-30"])
        self.response = {
            "schema_version": self.request["schema_version"],
            "request_digest": self.request["request_digest"],
            "decision": "human_review_only",
            "findings": [{
                "alert_id": "alert-0001", "category": "price_jump",
                "confidence": "low",
                "explanation": "An unusual price move needs an independent check before interpreting its cause.",
                "unknowns": ["The cause is not verified"],
                "checks": ["compare_second_source"],
                "evidence_dates": ["2026-10-30"]
            }]
        }
    def test_good_shape_and_usage(self):
        result = assess_analysis(self.request, self.response, {"total": 842})
        self.assertTrue(result["contract_valid"])
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["tokens_per_finding"], 842)
        self.assertTrue(result["review_required"])
    def test_uncertainty_missing_is_flagged(self):
        self.response["findings"][0]["unknowns"] = []
        result = assess_analysis(self.request, self.response)
        self.assertIn("missing_unknowns", result["issues"])
        self.assertLess(result["score"], 100)
    def test_invalid_contract(self):
        self.response["decision"] = "trade"
        result = assess_analysis(self.request, self.response)
        self.assertFalse(result["contract_valid"])
        self.assertEqual(result["score"], 0)

if __name__ == "__main__":
    unittest.main()
