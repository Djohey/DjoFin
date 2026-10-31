"""Tests reproductibles des outils quantitatifs P0."""
import unittest
from djofin.quantitatif import (fraction_kelly, volatilite_historique,
                                HypothesesMonteCarlo, monte_carlo)


class TestsQuantitatifs(unittest.TestCase):
    def test_kelly_avantage_nul(self):
        self.assertEqual(fraction_kelly(.5, 1, 1)["fraction_retenue"], 0)

    def test_kelly_fraction_et_plafond(self):
        x = fraction_kelly(.6, 1, 1, prudence=.25, plafond=.02)
        self.assertAlmostEqual(x["kelly_theorique"], .2)
        self.assertEqual(x["fraction_retenue"], .02)

    def test_kelly_avantage_negatif(self):
        self.assertEqual(fraction_kelly(.3, 1, 1)["fraction_retenue"], 0)

    def test_kelly_rejette_probabilite_invalide(self):
        with self.assertRaises(ValueError):
            fraction_kelly(1.2, 1, 1)

    def test_volatilite_constante(self):
        self.assertEqual(volatilite_historique([.01, .01, .01])["volatilite_annualisee"], 0)

    def test_volatilite_rejette_donnees_invalides(self):
        with self.assertRaises(ValueError):
            volatilite_historique([.1, -1])

    def test_monte_carlo_reproductible(self):
        h = HypothesesMonteCarlo(jours=12, simulations=50)
        self.assertEqual(monte_carlo(h), monte_carlo(h))

    def test_monte_carlo_sans_volatilite_ni_tendance(self):
        h = HypothesesMonteCarlo(jours=5, simulations=20, volatilite_journaliere=0)
        r = monte_carlo(h)
        self.assertEqual(r["capital_median"], h.capital)
        self.assertEqual(r["probabilite_perte_empirique"], 0)

    def test_monte_carlo_graine_differente(self):
        h = HypothesesMonteCarlo(jours=12, simulations=50)
        self.assertNotEqual(monte_carlo(h)["empreinte_sha256"],
                            monte_carlo(HypothesesMonteCarlo(
                                jours=12, simulations=50, graine=43))["empreinte_sha256"])

    def test_monte_carlo_rejette_parametres_invalides(self):
        with self.assertRaises(ValueError):
            HypothesesMonteCarlo(simulations=1)


if __name__ == "__main__":
    unittest.main()
