"""Historical case integrity: never treat hindsight as available at cutoff."""
import json
import unittest
from pathlib import Path
from datetime import datetime

PATH = Path(__file__).parent / "fixtures" / "historical_incidents_v1.json"

class HistoricalCaseTests(unittest.TestCase):
    def test_sources_and_hindsight_are_separate(self):
        cases = json.loads(PATH.read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases), 2)
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        for c in cases:
            with self.subTest(id=c["id"]):
                self.assertTrue(c["asof_observation"])
                self.assertTrue(c["hindsight"]["outcome"])
                self.assertGreaterEqual(len(c["hindsight"]["source_urls"]), 1)
                self.assertTrue(all(url.startswith("https://") for url in c["hindsight"]["source_urls"]))
                self.assertFalse(c["ready_for_point_in_time"])
                self.assertIsNotNone(datetime.fromisoformat(c["cutoff_utc"].replace("Z","+00:00")))
                self.assertNotIn("hindsight", {"observation":c["asof_observation"]})

if __name__ == "__main__":
    unittest.main()
