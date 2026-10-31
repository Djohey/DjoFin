"""Smoke test: compare candidate and stable against committed real feed data."""
import json
import unittest
from collections import Counter
from pathlib import Path
from djofin import research_priority as v01
from djofin import research_priority_v02 as v02

SOURCE = Path(__file__).resolve().parents[1] / "data/news/news.jsonl"

class RealFeedComparison(unittest.TestCase):
    def test_all_collected_items_without_failure(self):
        self.assertTrue(SOURCE.is_file(), "Collected news fixture missing")
        rows=[json.loads(s) for s in SOURCE.read_text(encoding="utf-8").splitlines() if s.strip()]
        self.assertGreaterEqual(len(rows),40)
        counts01,counts02=Counter(),Counter()
        changed=0
        for row in rows:
            a,b=v01.classify(row),v02.classify(row)
            counts01[a["priority"]]+=1
            counts02[b["priority"]]+=1
            changed+=(a["priority"]!=b["priority"])
            self.assertEqual(a["id"],b["id"])
            self.assertFalse(b["investment_signal"])
            self.assertEqual(len(b["rules_sha256"]),64)
        print("REAL FEED COMPARISON",json.dumps({"total":len(rows),"v01":dict(counts01),"v02":dict(counts02),"priority_changed":changed},sort_keys=True))
        # This is a regression/smoke test, NOT evidence of predictive validity.

if __name__=="__main__":
    unittest.main()
