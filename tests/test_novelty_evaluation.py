import unittest
from djofin.novelty_evaluation import novelty,evaluate_alerts

def item(ident,title,date):
    return {"id":ident*64,"feed_id":"ecb_press","title":title,
            "url":"https://www.ecb.europa.eu/press",
            "fetched_utc":date}

T0="2026-10-01T12:00:00Z"
T1="2026-10-02T12:00:00Z"
T2="2026-10-03T12:00:00Z"
T3="2026-10-04T12:00:00Z"
class NoveltyTests(unittest.TestCase):
    def test_exact_repeated_title(self):
        r=novelty(item("a","ECB rates decision",T1),
                  [item("b","ECB rates decision",T0)],cutoff_utc=T1)
        self.assertEqual(r["lexical_novelty"],0)
        self.assertFalse(r["investment_signal"])
    def test_unseen_title(self):
        r=novelty(item("a","ECB rates decision",T1),
                  [item("b","corporate securities filing",T0)],cutoff_utc=T1)
        self.assertEqual(r["lexical_novelty"],1)
        self.assertFalse(r["market_novelty_verified"])
    def test_empty_history_not_false_novelty(self):
        self.assertIsNone(novelty(item("a","ECB rates decision",T1),[],cutoff_utc=T1)["lexical_novelty"])
    def test_future_history_rejected(self):
        with self.assertRaises(ValueError):
            novelty(item("a","ECB rates decision",T1),
                    [item("b","ECB rates decision",T2)],cutoff_utc=T2)
    def test_same_time_history_rejected(self):
        with self.assertRaises(ValueError):
            novelty(item("a","ECB rates decision",T1),
                    [item("b","ECB rates decision",T1)],cutoff_utc=T1)
    def test_candidate_future_rejected(self):
        with self.assertRaises(ValueError):
            novelty(item("a","ECB rates decision",T2),[],cutoff_utc=T1)
    def test_metrics_and_missing_labels(self):
        predictions=[{"id":"a","alert":True,"predicted_at_utc":T0},
                     {"id":"b","alert":True,"predicted_at_utc":T0},
                     {"id":"c","alert":False,"predicted_at_utc":T0},
                     {"id":"d","alert":True,"predicted_at_utc":T0}]
        labels={"a":{"positive":True,"adjudicated_at_utc":T1},
                "b":{"positive":False,"adjudicated_at_utc":T1},
                "c":{"positive":True,"adjudicated_at_utc":T1}}
        r=evaluate_alerts(predictions,labels,cutoff_utc=T2)
        self.assertEqual((r["tp"],r["fp"],r["fn"],r["unlabeled"]),(1,1,1,1))
        self.assertEqual(r["precision"],.5)
        self.assertEqual(r["recall"],.5)
    def test_missing_denominator_is_none(self):
        r=evaluate_alerts([],{},cutoff_utc=T2)
        self.assertIsNone(r["precision"])
    def test_label_leakage_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_alerts([{"id":"a","alert":True,"predicted_at_utc":T1}],
                            {"a":{"positive":True,"adjudicated_at_utc":T0}},cutoff_utc=T2)
    def test_future_label_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_alerts([{"id":"a","alert":True,"predicted_at_utc":T0}],
                            {"a":{"positive":True,"adjudicated_at_utc":T3}},cutoff_utc=T2)
    def test_duplicate_prediction_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_alerts([{"id":"a","alert":True,"predicted_at_utc":T0}]*2,{},cutoff_utc=T2)
if __name__=="__main__":unittest.main()
