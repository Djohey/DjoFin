"""Contract regression tests: reject hallucinated evidence and unauthorized actions."""
import unittest
from djofin.ai_contract import prepare_request, validate_response

class AIContractTests(unittest.TestCase):
    def setUp(self):
        self.req=prepare_request(["Unexpected 20% jump"],snapshot_sha256="a"*64,
                                 ticker="CW8.PA",as_of_utc="2026-10-31T10:00:00Z")
        self.answer={
            "schema_version":"1.0",
            "decision":"human_review_only",
            "findings":[{
                "alert_id":"alert-0001",
                "category":"price_jump",
                "confidence":"low",
                "explanation":"Observed jump; cause not established.",
                "unknowns":["Corporate action or bad data?"],
                "checks":["Verify independent official price"],
                "evidence_ids":["alert-0001"]
            }]
        }
    def test_valid_response(self):
        self.assertTrue(validate_response(self.req,self.answer))
    def test_reject_fake_evidence(self):
        self.answer["findings"][0]["evidence_ids"]=["made-up-url"]
        with self.assertRaisesRegex(ValueError,"evidence"):
            validate_response(self.req,self.answer)
    def test_reject_trading_authorization(self):
        self.answer["decision"]="buy"
        with self.assertRaisesRegex(ValueError,"authorize"):
            validate_response(self.req,self.answer)
    def test_reject_missing_findings(self):
        self.answer["findings"]=[]
        with self.assertRaisesRegex(ValueError,"One finding"):
            validate_response(self.req,self.answer)
    def test_reject_duplicate_findings(self):
        self.req["alerts"].append({"id":"alert-0002","observation":"Missing day"})
        self.answer["findings"].append(self.answer["findings"][0].copy())
        with self.assertRaisesRegex(ValueError,"repeated"):
            validate_response(self.req,self.answer)

if __name__=="__main__":
    unittest.main()
