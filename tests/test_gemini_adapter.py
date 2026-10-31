"""Offline tests for Gemini experimental adapter."""
import unittest
from djofin.ai_contract import prepare_request
from djofin.gemini_adapter import prepare_gemini_payload, extract_gemini_response, GeminiPreparationError

class GeminiAdapterTests(unittest.TestCase):
    def test_payload_is_offline_and_bounded(self):
        request = prepare_request(
            [{"observation": "Public price anomaly", "dates": ["2026-10-30"]}],
            snapshot_sha256="a"*64, ticker="CW8.PA",
            as_of_utc="2026-10-31T10:00:00Z",
            snapshot_dates=["2026-10-30"])
        result = prepare_gemini_payload(request)
        self.assertFalse(result["network_enabled"])
        self.assertEqual(result["payload"]["generationConfig"]["maxOutputTokens"], 600)
        self.assertIn(request["request_digest"], result["payload"]["contents"][0]["parts"][0]["text"])
    def test_extract_usage(self):
        answer, usage = extract_gemini_response({
            "candidates": [{"content": {"parts": [{"text": '{"ok":true}'}]}}],
            "usageMetadata": {"promptTokenCount": 20, "candidatesTokenCount": 10, "totalTokenCount": 30}})
        self.assertEqual(answer, {"ok": True})
        self.assertEqual(usage["total"], 30)
    def test_invalid_response_rejected(self):
        with self.assertRaises(GeminiPreparationError):
            extract_gemini_response({"candidates": []})

if __name__ == "__main__":
    unittest.main()
