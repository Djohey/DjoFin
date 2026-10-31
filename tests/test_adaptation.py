"""Validation du dimensionnement adaptatif des ordres."""
import unittest
from djofin.simulator import Bar
from djofin.politiques import Regles, comparer_regle
from djofin.tarification import Tarification

class TestsAdaptation(unittest.TestCase):
    def setUp(self):
        self.bars = [Bar(f"2020-01-{i+1:02d}", 100+i, 100+i) for i in range(25)]
        self.tarif = Tarification(pourcentage=.005, minimum=2)

    def test_premiere_position_adaptee(self):
        r = comparer_regle(self.bars, Regles(mode="progressif", rapide=2, lente=4,
            seuil=0, confirmation=1, attente=0, tarification=self.tarif,
            adaptation_frais=True))
        self.assertGreater(len(r["operations"]), 0)
        self.assertGreater(len(r["adaptations"]), 0)

    def test_premiere_position_sous_plafond(self):
        r = comparer_regle(self.bars, Regles(mode="progressif", rapide=2, lente=4,
            seuil=0, confirmation=1, attente=0, tarification=self.tarif,
            adaptation_frais=True))
        self.assertLessEqual(r["adaptations"][0]["montant_adapte"], 350)

    def test_regle_initiale_reste_inchangee(self):
        p = dict(mode="progressif", rapide=2, lente=4, seuil=0,
                 confirmation=1, attente=0, tarification=self.tarif)
        a = comparer_regle(self.bars, Regles(**p))
        b = comparer_regle(self.bars, Regles(**p, adaptation_frais=False))
        self.assertEqual(a, b)

    def test_avenir_n_influence_pas_decision(self):
        p = Regles(mode="progressif", rapide=2, lente=4, seuil=0,
                   confirmation=1, attente=0, tarification=self.tarif,
                   adaptation_frais=True)
        mod = self.bars[:15] + [Bar(b.day, 500, 500) for b in self.bars[15:]]
        a = comparer_regle(self.bars, p)["decisions"][:15]
        b = comparer_regle(mod, p)["decisions"][:15]
        self.assertEqual(a, b)

if __name__ == "__main__":
    unittest.main()
