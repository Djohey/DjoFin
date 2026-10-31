import unittest
from djofin.evidence_ledger import new_hypothesis, add_evidence, review

T0="2026-10-01T09:00:00+00:00"
T1="2026-10-02T09:00:00+00:00"
SHA="a"*64

class EvidenceLedgerTests(unittest.TestCase):
    def setUp(self):
        self.ledger=new_hypothesis("hyp-1","A rate change may affect equities",T0)
    def evidence(self,ledger=None,**kwargs):
        values={"source_url":"https://example.org/study","published_at":T0,
                "captured_at":T1,"stance":"supports","excerpt":"Test evidence",
                "source_sha256":SHA}
        values.update(kwargs)
        return add_evidence(self.ledger if ledger is None else ledger,**values)
    def test_append_and_review(self):
        updated=self.evidence()
        self.assertEqual(review(updated)["counts"]["supports"],1)
        self.assertEqual(review(self.ledger)["counts"]["supports"],0)
        self.assertFalse(review(updated)["investment_signal"])
    def test_contradiction(self):
        a=self.evidence()
        b=self.evidence(a,stance="contradicts",excerpt="Counterevidence")
        self.assertTrue(review(b)["has_contradiction"])
    def test_duplicate_rejected(self):
        a=self.evidence()
        with self.assertRaises(ValueError):self.evidence(a)
    def test_future_publication_rejected(self):
        with self.assertRaises(ValueError):self.evidence(published_at=T1,captured_at=T0)
    def test_tamper_rejected(self):
        self.ledger["claim"]="changed without new hash"
        with self.assertRaises(ValueError):self.evidence()
    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):new_hypothesis("x","A meaningful hypothesis","2026-10-01T00:00:00")
    def test_invalid_sha_rejected(self):
        with self.assertRaises(ValueError):self.evidence(source_sha256="abc")
if __name__=="__main__":unittest.main()
