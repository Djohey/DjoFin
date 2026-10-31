"""Tests for isolation and time-leakage safeguards."""
import unittest
from copy import deepcopy
from djofin.replay_gate import build_analyst_packet, ReplayGateError

CUTOFF = "2020-01-15T21:00:00Z"
ROW = {"source_id": "source_a", "published_utc": "2020-01-12T23:59:59Z", "archive_captured_utc": "2020-01-13T00:00:00Z", "archive_sha256": "a" * 64, "text": "41 preliminarily diagnosed cases reported."}

class ReplayGateTests(unittest.TestCase):
    def setUp(self):
        self.case = {"case_id": "respiratory_outbreak_2020", "cutoff_utc": CUTOFF, "observations": [deepcopy(ROW)]}

    def test_valid_archived_packet_is_minimal(self):
        packet = build_analyst_packet(self.case, attempt_id="a1")
        self.assertEqual(set(packet), {"case_id", "cutoff_utc", "attempt_id", "observations", "packet_sha256"})
        self.assertNotIn("archive_captured_utc", packet["observations"][0])

    def test_rejects_future_publication(self):
        self.case["observations"][0]["published_utc"] = "2020-01-16T00:01:00Z"
        with self.assertRaises(ReplayGateError):
            build_analyst_packet(self.case, attempt_id="a1")

    def test_rejects_future_archive_capture(self):
        self.case["observations"][0]["archive_captured_utc"] = "2020-01-16T00:01:00Z"
        with self.assertRaises(ReplayGateError):
            build_analyst_packet(self.case, attempt_id="a1")

    def test_rejects_hindsight_words(self):
        self.case["observations"][0]["text"] = "COVID-19"
        with self.assertRaises(ReplayGateError):
            build_analyst_packet(self.case, attempt_id="a1")

    def test_rejects_audit_metadata(self):
        self.case["audit"] = "reviewed"
        with self.assertRaises(ReplayGateError):
            build_analyst_packet(self.case, attempt_id="a1")

    def test_rejects_wrong_cutoff(self):
        self.case["cutoff_utc"] = "2020-01-16T00:00:00Z"
        with self.assertRaises(ReplayGateError):
            build_analyst_packet(self.case, attempt_id="a1")

    def test_rejects_missing_archive(self):
        self.case["observations"][0]["archive_sha256"] = ""
        with self.assertRaises(ReplayGateError):
            build_analyst_packet(self.case, attempt_id="a1")

    def test_rejects_unverified_empty_case(self):
        self.case["observations"] = []
        with self.assertRaises(ReplayGateError):
            build_analyst_packet(self.case, attempt_id="a1")

if __name__ == "__main__":
    unittest.main()
