import unittest
from djofin.ai_contract import prepare_request
from djofin.wire_benchmark import compare_wire_formats, pack_positional, unpack_positional

class WireBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.request = prepare_request(
            [{"observation": "Synthetic ETF price jump 16%; cause unknown",
              "dates": ["2026-10-30"]}],
            snapshot_sha256="a"*64, ticker="CW8.PA",
            as_of_utc="2026-10-31T10:00:00Z", snapshot_dates=["2026-10-30"])

    def test_roundtrip(self):
        self.assertEqual(unpack_positional(pack_positional(self.request)), self.request)

    def test_compact_saves_bytes_without_data_loss(self):
        result = compare_wire_formats(self.request)
        self.assertLess(result["compact_json_bytes"], result["readable_json_bytes"])
        self.assertGreater(result["positional_bytes"], 0)

    def test_reject_modified_digest(self):
        import json
        wire = json.loads(pack_positional(self.request))
        wire["values"][2] = "OTHER"
        with self.assertRaises(ValueError):
            unpack_positional(json.dumps(wire))

if __name__ == "__main__":
    unittest.main()
