"""Offline tests for Gemini experimental adapter."""
import unittest
import json
from djofin.ai_contract import serialize_request
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
        self.assertIn("systemInstruction", result["payload"])
        self.assertNotIn("system_instruction", result["payload"])
        self.assertEqual(result["payload"]["contents"][0]["role"], "user")
        self.assertEqual(result["payload"]["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(result["payload"]["generationConfig"]["maxOutputTokens"], 600)
        self.assertIn(request["request_digest"], result["payload"]["contents"][0]["parts"][0]["text"])
    def test_compact_request_preserves_all_fields(self):
        request = prepare_request(
            [{"observation": "Synthetic ETF jump 16%", "dates": ["2026-10-30"]}],
            snapshot_sha256="a"*64, ticker="CW8.PA",
            as_of_utc="2026-10-31T10:00:00Z",
            snapshot_dates=["2026-10-30"])
        result = prepare_gemini_payload(request)
        compact = result["payload"]["contents"][0]["parts"][0]["text"]
        self.assertEqual(json.loads(compact), request)
        self.assertLess(len(compact.encode("utf-8")), len(serialize_request(request).encode("utf-8")))
        self.assertEqual(result["estimated_input_bytes"], len(compact.encode("utf-8")))
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
