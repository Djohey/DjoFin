import unittest
from djofin.historical_replay import build_blind_packet, evaluate_blind_attempt, ReplayIsolationError

CASE = {"id": "historical-case-1", "cutoff_utc": "2020-01-15T12:00:00Z",
        "hindsight": {"outcome": "SECRET_FUTURE_OUTCOME"},
        "previous_attempt_feedback": "SECRET_PRIOR_FEEDBACK"}
ROWS = [{"published_utc": "2020-01-14T09:00:00Z",
         "text": "Early reports describe a localized health event; scale uncertain.",
         "source_id": "archived-source-1"}]

class HistoricalReplayTests(unittest.TestCase):
    def test_no_hindsight_or_previous_feedback(self):
        packet = build_blind_packet(CASE, ROWS, attempt_id="attempt-2")
        self.assertNotIn("SECRET_FUTURE_OUTCOME", str(packet))
        self.assertNotIn("SECRET_PRIOR_FEEDBACK", str(packet))
        self.assertNotIn("hindsight", packet)

    def test_same_evidence_new_attempt_isolated(self):
        a = build_blind_packet(CASE, ROWS, attempt_id="attempt-1")
        b = build_blind_packet(CASE, ROWS, attempt_id="attempt-2")
        self.assertEqual(a["observations"], b["observations"])
        self.assertNotEqual(a["packet_sha256"], b["packet_sha256"])

    def test_future_source_rejected(self):
        rows = [dict(ROWS[0], published_utc="2020-01-16T00:00:00Z")]
        with self.assertRaises(ReplayIsolationError):
            build_blind_packet(CASE, rows, attempt_id="attempt-1")

    def test_unexpected_fields_rejected(self):
        rows = [dict(ROWS[0], future_outcome="LEAK")]
        with self.assertRaises(ReplayIsolationError):
            build_blind_packet(CASE, rows, attempt_id="attempt-1")

    def test_evaluation_is_separate(self):
        packet = build_blind_packet(CASE, ROWS, attempt_id="attempt-1")
        report = evaluate_blind_attempt(packet, {"hypothesis":"unknown"},
                                        {"outcome":"SECRET_FUTURE_OUTCOME"})
        self.assertIn("SECRET_FUTURE_OUTCOME", str(report))
        self.assertNotIn("SECRET_FUTURE_OUTCOME", str(packet))

if __name__ == "__main__":
    unittest.main()
