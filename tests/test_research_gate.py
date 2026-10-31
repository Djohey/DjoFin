import unittest
from djofin.research_gate import rank_research, bayes_update
from djofin.evidence_ledger import new_hypothesis, add_evidence

ENTRY={"id":"a"*64,"feed_id":"ecb_press","title":"ECB update",
       "url":"https://www.ecb.europa.eu/press","fetched_utc":"2026-10-31T12:00:00Z"}
A={"impact":1,"novelty":1,"uncertainty":0.8,"verifiability":1,"cross_domain":0.5}

class ResearchGateTests(unittest.TestCase):
    def test_headline_only_no_score_no_signal(self):
        r=rank_research(ENTRY)
        self.assertIsNone(r["score"])
        self.assertIsNone(r["bayesian_probability"])
        self.assertFalse(r["investment_signal"])
        self.assertFalse(r["eligible_as_evidence"])
    def test_scored_research_only(self):
        r=rank_research(ENTRY,A)
        self.assertEqual(r["decision"],"investigate")
        self.assertFalse(r["investment_signal"])
        self.assertEqual(r["score"],0.91)
    def test_low_score_deferred(self):
        r=rank_research(ENTRY,{k:0 for k in A})
        self.assertEqual(r["decision"],"defer")
    def test_invalid_assessment_rejected(self):
        for assessment in ({"impact":1}, {**A,"impact":float("nan")},{**A,"novelty":True}):
            with self.assertRaises(ValueError):rank_research(ENTRY,assessment)
    def test_bayes_identity(self):
        self.assertAlmostEqual(bayes_update(.2,[1]),.2)
    def test_bayes_ratio(self):
        self.assertAlmostEqual(bayes_update(.2,[4]),.5)
    def test_bayes_invalid(self):
        for value in (0,-1,float("inf"),True):
            with self.assertRaises(ValueError):bayes_update(.5,[value])
    def test_bayes_extreme_stable(self):
        self.assertAlmostEqual(bayes_update(1e-10,[1e10]),.5,places=6)
    def test_contradiction_integration(self):
        h=new_hypothesis("test","Rates affect equity valuations","2026-10-01T00:00:00Z")
        h=add_evidence(h,source_url="https://example.org/a",
                       published_at="2026-10-01T00:00:00Z",
                       captured_at="2026-10-02T00:00:00Z",stance="contradicts",
                       excerpt="Counterargument",source_sha256="a"*64)
        r=rank_research(ENTRY,A,ledger=h)
        self.assertTrue(r["contradictory_evidence_present"])
        self.assertFalse(r["eligible_as_evidence"])
if __name__=="__main__":unittest.main()
