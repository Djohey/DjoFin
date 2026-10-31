"""Offline tests: AI transport must not send requests by default."""
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from djofin.ai_contract import prepare_request
from djofin.ai_connector import ConnectorError, run_analysis

class FakeResponse:
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, size):
        return self.body[:size]

class ConnectorTests(unittest.TestCase):
    def setUp(self):
        self.req = prepare_request(
            [{"observation":"20% jump on 2026-10-30","dates":["2026-10-30"]}],
            snapshot_sha256="a"*64, ticker="CW8.PA",
            as_of_utc="2026-10-31T10:00:00Z", snapshot_dates=["2026-10-30"])
        self.env = {
            "DJOFIN_AI_ENABLED":"1",
            "DJOFIN_AI_ENDPOINT":"https://api.example.org/v1/chat/completions",
            "DJOFIN_AI_API_KEY":"secret-test",
            "DJOFIN_AI_MODEL":"test-model",
            "DJOFIN_AI_INPUT_USD_PER_M":"0",
            "DJOFIN_AI_OUTPUT_USD_PER_M":"0",
        }
    def test_disabled_by_default(self):
        with patch.dict(os.environ, {"DJOFIN_AI_ENABLED":"0"}):
            with self.assertRaisesRegex(ConnectorError,"disabled"):
                run_analysis(self.req, transport=lambda _: self.fail("network called"))
    def test_valid_mock_response_and_redacted_log(self):
        finding={"alert_id":"alert-0001","category":"price_jump","confidence":"low",
                 "explanation":"Cause unknown","unknowns":["Independent quote unavailable"],
                 "checks":["compare_second_source"],"evidence_dates":["2026-10-30"]}
        answer={"schema_version":"1.1","request_digest":self.req["request_digest"],
                "decision":"human_review_only","findings":[finding]}
        raw=json.dumps({"choices":[{"message":{"content":json.dumps(answer)}}]}).encode()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,self.env):
            result=run_analysis(self.req,transport=lambda _: FakeResponse(raw),
                                log_path=directory+"/audit.jsonl")
            self.assertTrue(result["validation"]["ok"])
            log=open(directory+"/audit.jsonl",encoding="utf-8").read()
            self.assertNotIn("secret-test",log)
            self.assertNotIn("Cause unknown",log)
    def test_preflight_budget_rejects_expensive_model(self):
        with patch.dict(os.environ,{**self.env,"DJOFIN_AI_INPUT_USD_PER_M":"1000"}):
            with self.assertRaisesRegex(ConnectorError,"Zero-dollar budget"):
                run_analysis(self.req,transport=lambda _: self.fail("network called"))
    def test_rejects_insecure_endpoint(self):
        with patch.dict(os.environ,{**self.env,"DJOFIN_AI_ENDPOINT":"http://localhost:8080"}):
            with self.assertRaisesRegex(ConnectorError,"HTTPS"):
                run_analysis(self.req,transport=lambda _: self.fail("network called"))

if __name__=="__main__":
    unittest.main()
