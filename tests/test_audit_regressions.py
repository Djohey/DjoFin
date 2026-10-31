"""Regression checks after independent audit."""
import unittest
from djofin.simulator import Bar
from djofin.politiques import Regles, comparer_regle
from djofin.tarification import Tarification

class AuditRegressions(unittest.TestCase):
    def setUp(self):
        self.bars = [Bar(f"2020-{1+i//28:02d}-{1+i%28:02d}",100+i*.2,100+i*.2) for i in range(75)]

    def test_complete_liquidation(self):
        bars = self.bars[:45] + [Bar(b.day, 40, 40) for b in self.bars[45:]]
        result = comparer_regle(bars,Regles(mode="initial",rapide=2,lente=4))
        for op in result["operations"]:
            if op["sens"] == "vente" and op["cible"] == 0:
                self.assertEqual(op["parts_apres"],0.0)

    def test_all_operations_reconcile(self):
        result = comparer_regle(self.bars,Regles(mode="progressif",rapide=2,lente=4,seuil=0,confirmation=1,attente=0))
        for op in result["operations"]:
            self.assertAlmostEqual(op["cash_apres"],op["cash_avant"]+(op["brut"] if op["sens"]=="vente" else -op["brut"])-op["frais"],places=7)
            self.assertGreaterEqual(op["parts_apres"],0)

    def test_initial_unchanged_by_adaptation(self):
        params=dict(mode="initial",rapide=2,lente=4,tarification=Tarification(minimum=2,pourcentage=.005))
        a=comparer_regle(self.bars,Regles(**params))
        b=comparer_regle(self.bars,Regles(**params,adaptation_frais=True))
        self.assertEqual(a["capital_final"],b["capital_final"])

if __name__=="__main__":
    unittest.main()
