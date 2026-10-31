"""Daily market archive invariants without contacting external vendors."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from scripts.archive_market_daily import main

class DailyArchiveTests(unittest.TestCase):
    def test_existing_snapshot_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            today = datetime.now(timezone.utc).date().isoformat()
            folder = Path(tmp) / "CW8_PA" / today
            folder.mkdir(parents=True)
            data = b"Date,Open,Close\n2026-10-30,100,101\n"
            (folder / "prices.csv").write_bytes(data)
            (folder / "integrity.json").write_text(json.dumps({
                "csv_file": "prices.csv",
                "csv_sha256": hashlib.sha256(data).hexdigest()
            }))
            with patch("sys.argv", ["archive", "--root", tmp]):
                main()
            self.assertEqual((folder / "prices.csv").read_bytes(), data)

    def test_corrupt_existing_snapshot_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            today = datetime.now(timezone.utc).date().isoformat()
            folder = Path(tmp) / "CW8_PA" / today
            folder.mkdir(parents=True)
            (folder / "prices.csv").write_text("corrupted")
            (folder / "integrity.json").write_text(json.dumps({
                "csv_file": "prices.csv", "csv_sha256": "wrong"
            }))
            with patch("sys.argv", ["archive", "--root", tmp]):
                with self.assertRaisesRegex(RuntimeError, "checksum"):
                    main()

if __name__ == "__main__":
    unittest.main()
