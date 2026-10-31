import unittest
from djofin.counterfactual_review import review_decisions
T0="2026-01-01T00:00:00Z"
T1="2026-01-02T00:00:00Z"
T2="2026-02-01T00:00:00Z"
SHA="a"*64

def case(ident,action,outcome,reason="risk"):
    return {"id":ident,"observed_at_utc":T0,"decision_at_utc":T1,
            "outcome_at_utc":T2,"action":action,"outcome":outcome,
            "reason":reason,"in_universe_at_decision":True,
            "predecision_snapshot_sha256":SHA,"outcome_source_sha256":SHA}

class CounterfactualTests(unittest.TestCase):
    def test_four_decision_types(self):
        rows=[case("win","invest","gain"),case("loss","invest","loss"),
              case("miss","abstain","gain"),case("avoid","abstain","loss"),
              case("unseen","not_detected","gain","not_collected")]
        result=review_decisions(rows,cutoff_utc=T2)
        self.assertEqual(result["total"],5)
        self.assertEqual(result["matrix"]["not_detected"]["gain"],1)
        self.assertFalse(result["investment_signal"])
        self.assertFalse(result["automatic_learning_permitted"])
    def test_missing_universe_rejected(self):
        row=case("x","not_detected","gain","not_collected")
        row["in_universe_at_decision"]=False
        with self.assertRaises(ValueError):review_decisions([row],cutoff_utc=T2)
    def test_hindsight_rejected(self):
        row=case("x","invest","gain")
        row["observed_at_utc"]=T2
        with self.assertRaises(ValueError):review_decisions([row],cutoff_utc=T2)
    def test_future_outcome_rejected(self):
        with self.assertRaises(ValueError):review_decisions([case("x","abstain","loss")],cutoff_utc=T1)
    def test_duplicates_rejected(self):
        row=case("x","invest","gain")
        with self.assertRaises(ValueError):review_decisions([row,row],cutoff_utc=T2)
    def test_missing_hash_rejected(self):
        row=case("x","invest","gain")
        row["predecision_snapshot_sha256"]=""
        with self.assertRaises(ValueError):review_decisions([row],cutoff_utc=T2)
    def test_abstention_requires_universe(self):
        row=case("x","abstain","loss")
        row["in_universe_at_decision"]=False
        with self.assertRaises(ValueError):review_decisions([row],cutoff_utc=T2)
    def test_empty_result(self):
        self.assertEqual(review_decisions([],cutoff_utc=T2)["total"],0)
if __name__=="__main__":unittest.main()
