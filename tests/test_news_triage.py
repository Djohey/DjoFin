import json
import unittest
from djofin.news_triage import triage_entry, triage_jsonl, json_report

ENTRY={"id":"a"*64,"feed_id":"ecb_press","title":"Policy update",
       "url":"https://www.ecb.europa.eu/press","fetched_utc":"2026-10-31T12:00:00Z",
       "published_raw":"unverified date"}

class TriageTests(unittest.TestCase):
    def test_no_signal_and_no_evidence(self):
        result=triage_entry(ENTRY)
        self.assertFalse(result["investment_signal"])
        self.assertFalse(result["evidence_eligible"])
        self.assertFalse(result["source_claim_verified"])
        self.assertEqual(result["priority"],"review")
    def test_deterministic_output(self):
        data=json.dumps(ENTRY)
        self.assertEqual(json_report(data),json_report(data))
        self.assertEqual(triage_jsonl(data)["count"],1)
    def test_duplicate_rejected(self):
        data=json.dumps(ENTRY)
        with self.assertRaises(ValueError):triage_jsonl(data+"\n"+data)
    def test_unknown_feed_rejected(self):
        with self.assertRaises(ValueError):triage_entry({**ENTRY,"feed_id":"unknown"})
    def test_bad_url_rejected(self):
        with self.assertRaises(ValueError):triage_entry({**ENTRY,"url":"http://example.com"})
    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):triage_entry({**ENTRY,"fetched_utc":"2026-10-31T12:00:00"})
    def test_invalid_json_rejected(self):
        with self.assertRaises(json.JSONDecodeError):triage_jsonl('{"bad":')
    def test_size_limit(self):
        with self.assertRaises(ValueError):triage_jsonl("x"*900001)
    def test_order_independent(self):
        second={**ENTRY,"id":"b"*64,"fetched_utc":"2026-10-30T12:00:00Z"}
        items=triage_jsonl(json.dumps(ENTRY)+"\n"+json.dumps(second))["items"]
        self.assertEqual([x["id"] for x in items],["b"*64,"a"*64])
if __name__=="__main__":unittest.main()
