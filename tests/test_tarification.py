"""Contrôles des commissions et des refus d'ordres."""
import unittest
from djofin.tarification import Tarification, frais_ordre, montant_achat
from djofin.politiques import Regles, comparer_regle
from djofin.simulator import Bar

class TestsTarification(unittest.TestCase):
    def test_fixe(self):
        self.assertEqual(frais_ordre(100, Tarification(fixe=1, pourcentage=0)), 1)

    def test_proportionnel(self):
        self.assertAlmostEqual(frais_ordre(100, Tarification(pourcentage=.001)), .1)

    def test_mixte(self):
        self.assertAlmostEqual(frais_ordre(100, Tarification(fixe=1, pourcentage=.001)), 1.1)

    def test_minimum(self):
        self.assertEqual(frais_ordre(100, Tarification(pourcentage=.005, minimum=2)), 2)

    def test_budget_achat(self):
        t = Tarification(fixe=1, pourcentage=.001)
        brut = montant_achat(100, t)
        self.assertLessEqual(brut + frais_ordre(brut, t), 100.00000001)

    def test_refus_petit_ordre(self):
        bars = [Bar(f"2020-01-{i+1:02d}", 100+i, 100+i) for i in range(20)]
        r = comparer_regle(bars, Regles(mode="progressif", rapide=2, lente=4,
                          confirmation=1, capital=100, attente=0, seuil=0,
                          tarification=Tarification(fixe=5, pourcentage=0)))
        self.assertTrue(r["ordres_refuses"])
        self.assertEqual(len(r["operations"]), 0)

if __name__ == "__main__":
    unittest.main()
