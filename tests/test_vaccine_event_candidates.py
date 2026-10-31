"""Offline quality gates for historical vaccine event candidates."""
import json
import unittest
from datetime import date
from pathlib import Path

FILE = Path(__file__).parent / "fixtures" / "covid_vaccine_event_candidates_v1.json"

class VaccineEventCandidateTests(unittest.TestCase):
    def test_events_have_unique_dates_and_sources(self):
        data = json.loads(FILE.read_text(encoding="utf-8"))
        events = data["events"]
        self.assertGreaterEqual(len(events), 8)
        self.assertEqual(len({e["id"] for e in events}), len(events))
        for event in events:
            with self.subTest(event=event["id"]):
                self.assertEqual(date.fromisoformat(event["event_date"]).isoformat(), event["event_date"])
                self.assertTrue(event["companies"])
                self.assertTrue(event["primary_source_candidate"].startswith("https://"))
                self.assertTrue(event["cutoff_rule"])
        self.assertIn("require", data["status"])

if __name__ == "__main__":
    unittest.main()
