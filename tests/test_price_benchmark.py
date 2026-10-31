import hashlib
import unittest
from datetime import date,timedelta
from djofin.price_benchmark import load_prices,benchmark

def fixture(n=55):
    start=date(2020,1,1)
    lines=["Date,Open,Close"]
    for i in range(n):
        day=start+timedelta(days=i)
        lines.append(f"{day.isoformat()},{100+i},{100+i+.5}")
    text="\n".join(lines)+"\n"
    return text,hashlib.sha256(text.encode()).hexdigest()

class PriceBenchmarkTests(unittest.TestCase):
    def test_baseline_and_no_alpha_claim(self):
        raw,digest=fixture()
        result=benchmark(raw,digest,start_date="2020-01-01",
                         train_end_date="2020-01-30",end_date="2020-02-24")
        self.assertFalse(result["market_alpha_validated"])
        self.assertGreater(result["validation_days"],0)
        self.assertEqual(result["reference_sha256"],digest)
    def test_checksum_rejected(self):
        raw,_=fixture()
        with self.assertRaises(ValueError):load_prices(raw,"0"*64)
    def test_future_out_of_range_rejected(self):
        raw,digest=fixture()
        with self.assertRaises(ValueError):
            benchmark(raw,digest,start_date="2020-01-01",
                      train_end_date="2020-01-30",end_date="2020-05-01")
    def test_insufficient_lookback_rejected(self):
        raw,digest=fixture()
        with self.assertRaises(ValueError):
            benchmark(raw,digest,start_date="2020-01-01",
                      train_end_date="2020-01-05",end_date="2020-01-20")
    def test_bad_fee_rejected(self):
        raw,digest=fixture()
        with self.assertRaises(ValueError):
            benchmark(raw,digest,start_date="2020-01-01",
                      train_end_date="2020-01-30",end_date="2020-02-24",
                      fee_rate=float("nan"))
    def test_nonmonotonic_dates_rejected(self):
        raw,_=fixture()
        raw=raw.replace("2020-01-03","2020-01-02")
        with self.assertRaises(ValueError):
            load_prices(raw,hashlib.sha256(raw.encode()).hexdigest())
    def test_invalid_split_rejected(self):
        raw,digest=fixture()
        with self.assertRaises(ValueError):
            benchmark(raw,digest,start_date="2020-01-30",
                      train_end_date="2020-01-01",end_date="2020-02-24")
if __name__=="__main__":unittest.main()
