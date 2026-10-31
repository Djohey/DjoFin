import json
import unittest
from pathlib import Path
from djofin.ai_contract import prepare_request, ALLOWED_CATEGORIES, ALLOWED_CHECKS
from djofin.scenario_eval import evaluate_scenario

FIXTURE = Path(__file__).parent / "fixtures" / "financial_scenarios_v1.json"

class FinancialScenarioFixtureTests(unittest.TestCase):
    def test_ten_distinct_valid_scenarios(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cases = data["scenarios"]
        self.assertEqual(len(cases), 10)
        self.assertEqual(len({c["id"] for c in cases}), 10)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(set(case["expected"]["categories"]) <= ALLOWED_CATEGORIES)
                self.assertTrue(set(case["expected"]["required_checks"]) <= ALLOWED_CHECKS)
                self.assertIs(type(case["expected"]["require_unknowns"]), bool)
                req = prepare_request(
                    [{"observation": case["observation"], "dates": case["dates"]}],
                    ticker=case["ticker"], as_of_utc=case["as_of_utc"],
                    snapshot_sha256="a"*64, snapshot_dates=case["dates"],
                    previous_snapshot_sha256=("b"*64 if case["requires_previous_snapshot"] else None))
                rubric = {"alert-0001": case["expected"]}
                self.assertEqual(set(rubric), {a["id"] for a in req["alerts"]})
                self.assertTrue(req["request_digest"])

if __name__ == "__main__":
    unittest.main()
