"""Market archive quality checks on synthetic dated snapshots."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.verify_market_archive import main

def snapshot(root, day, data):
    folder=Path(root)/"CW8_PA"/day
    folder.mkdir(parents=True)
    csv_file=folder/"prices.csv"
    csv_file.write_text(data,encoding="utf-8")
    (folder/"integrity.json").write_text(json.dumps({
        "csv_file":"prices.csv",
        "csv_sha256":hashlib.sha256(csv_file.read_bytes()).hexdigest()
    }),encoding="utf-8")

class QualityTests(unittest.TestCase):
    def test_detects_revised_historical_price(self):
        with tempfile.TemporaryDirectory() as root:
            snapshot(root,"2026-10-30","Date,Open,Close\n2026-10-29,100,100\n")
            snapshot(root,"2026-10-31","Date,Open,Close\n2026-10-29,100,101\n")
            with patch("sys.argv",["verify","--root",root]):
                main()
            report=Path("sortie/archive_status.md").read_text()
            self.assertIn("Historical revision",report)

    def test_duplicate_dates_fail(self):
        with tempfile.TemporaryDirectory() as root:
            snapshot(root,"2026-10-31","Date,Open,Close\n2026-10-29,100,100\n2026-10-29,100,101\n")
            with patch("sys.argv",["verify","--root",root]):
                with self.assertRaisesRegex(RuntimeError,"duplicated"):
                    main()

    def test_large_variation_alert(self):
        with tempfile.TemporaryDirectory() as root:
            snapshot(root,"2026-10-31","Date,Open,Close\n2026-10-29,100,100\n2026-10-30,100,120\n")
            with patch("sys.argv",["verify","--root",root]):
                main()
            self.assertIn("Large close variation",Path("sortie/archive_status.md").read_text())

if __name__=="__main__":
    unittest.main()
