"""Ablation tests for three independent fee switches."""
import unittest
from djofin.simulator import Bar
from djofin.politiques import Regles, comparer_regle
from djofin.tarification import Tarification

class TestAblation(unittest.TestCase):
    def setUp(self):
        self.bars = [Bar(f"2020-{1+i//28:02d}-{1+i%28:02d}", 100+i*.2, 100+i*.2) for i in range(75)]
        self.fee = Tarification(minimum=2,pourcentage=.005)

    def test_all_disabled_matches_reference(self):
        args=dict(mode="progressif",rapide=2,lente=4,seuil=0,confirmation=1,
                  attente=0,tarification=self.fee)
        before=comparer_regle(self.bars,Regles(**args))
        after=comparer_regle(self.bars,Regles(**args,adaptation_frais=True,
            adapter_achats=False,adapter_ventes=False,dedoublonner_refus=False))
        self.assertEqual(before,after)

    def test_purchase_switch_changes_adaptations(self):
        args=dict(mode="progressif",rapide=2,lente=4,seuil=0,confirmation=1,
                  attente=0,tarification=self.fee,adaptation_frais=False)
        no=comparer_regle(self.bars,Regles(**args))
        yes=comparer_regle(self.bars,Regles(**args,adapter_achats=True))
        self.assertEqual(len(no["adaptations"]),0)
        self.assertGreater(len(yes["adaptations"]),0)

    def test_deduplication_does_not_change_trades(self):
        args=dict(mode="progressif",rapide=2,lente=4,seuil=0,confirmation=1,
                  attente=0,tarification=self.fee)
        a=comparer_regle(self.bars,Regles(**args,dedoublonner_refus=False))
        b=comparer_regle(self.bars,Regles(**args,dedoublonner_refus=True))
        self.assertEqual(a["operations"],b["operations"])
        self.assertEqual(a["capital_final"],b["capital_final"])

if __name__=="__main__":
    unittest.main()
