"""Offline tests for official feed collection (no internet needed)."""
import tempfile
import unittest
from pathlib import Path
from scripts.collect_public_feeds import parse_feed, collect, save

RSS = b"""<?xml version="1.0"?><rss><channel><item><title>Policy update</title><link>https://example.org/release</link><pubDate>Thu, 29 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>"""
ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Study published</title><link href="https://example.org/study"/><updated>2026-10-29T12:00:00Z</updated></entry></feed>"""

class FeedTests(unittest.TestCase):
    def test_rss_provenance(self):
        rows = parse_feed(RSS, "test", "2026-10-31T00:00:00Z")
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["publication_time_verified"])
        self.assertEqual(rows[0]["url"], "https://example.org/release")
    def test_atom(self):
        self.assertEqual(parse_feed(ATOM, "test", "2026-10-31T00:00:00Z")[0]["title"], "Study published")
    def test_deduplicate_on_disk(self):
        rows = parse_feed(RSS, "test", "2026-10-31T00:00:00Z")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "items.jsonl"
            self.assertEqual(save(rows, p), 1)
            self.assertEqual(save(rows, p), 0)
    def test_one_failed_feed_does_not_erase_success(self):
        def fetcher(url):
            if url.endswith("bad"):
                raise OSError("not available")
            return RSS
        rows, errors = collect({"good":"https://example.org/ok","bad":"https://example.org/bad"}, fetcher)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(errors), 1)

if __name__ == "__main__":
    unittest.main()
