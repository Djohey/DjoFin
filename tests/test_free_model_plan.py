import unittest
from djofin.free_model_plan import POLICY, CANDIDATES, authorize_operation, manifest

class FreeOnlyPolicyTests(unittest.TestCase):
    def test_budget_zero(self):
        self.assertEqual(POLICY.max_eur, 0)
        self.assertTrue(authorize_operation())
    def test_forbidden_operations(self):
        for kwargs in (
            {"estimated_eur":0.01}, {"paid_api":True}, {"live_trade":True},
            {"model_download":True}, {"gpu_rental":True},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(PermissionError):
                authorize_operation(**kwargs)
    def test_candidates_are_not_active(self):
        self.assertEqual(set(CANDIDATES), {"minilm", "mdeberta", "finbert"})
        self.assertTrue(all(v["status"]=="proposed_not_executed" for v in CANDIDATES.values()))
        self.assertFalse(manifest()["policy"]["allow_paid_api"])

if __name__ == "__main__":
    unittest.main()
