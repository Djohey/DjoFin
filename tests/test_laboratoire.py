"""Tests du laboratoire de réévaluation, sans connaissance des cours futurs."""
import unittest
from dataclasses import replace
from djofin.laboratoire import Apprentissage, rejouer
from djofin.simulator import Bar, Config


def donnees():
    # Marché alternant tendances et retournements, exclusivement fictif.
    prix = [100, 101, 102, 103, 104, 105, 104, 103, 102, 101,
            100, 99, 98, 99, 100, 101, 102, 103, 102, 101]
    return [Bar(f"2020-01-{i+1:02d}", p, p) for i, p in enumerate(prix)]


def etude():
    return Apprentissage(
        identifiant="EXP-001",
        hypothese="Une moyenne plus lente réduit les changements de position",
        justification="Hypothèse à tester, non conclusion établie",
        source="Expérimentation interne synthétique",
        date_publication="2019-01-01",
        date_integration="2026-10-31",
        limites="Résultats non généralisables sans validation externe")


class TestsLaboratoire(unittest.TestCase):
    def setUp(self):
        self.base = Config(initial_cash=1000, fast_window=2, slow_window=3)
        self.autre = Config(initial_cash=1000, fast_window=3, slow_window=5)

    def test_dossier_justifie_les_decisions_et_les_differences(self):
        d = rejouer(donnees(), self.base, self.autre, etude(), "2020-01-12")
        self.assertEqual(d["apprentissage"]["identifiant"], "EXP-001")
        self.assertTrue(d["differences_decisions"])
        self.assertTrue(all("informations_disponibles_jusqua" in x
                            for x in d["differences_decisions"]))
        self.assertIn("frais_validation", d["resultat_candidat"])

    def test_dossier_reproductible(self):
        x = rejouer(donnees(), self.base, self.autre, etude(), "2020-01-12")
        y = rejouer(donnees(), self.base, self.autre, etude(), "2020-01-12")
        self.assertEqual(x["empreinte_dossier"], y["empreinte_dossier"])

    def test_changement_futur_ne_change_pas_decisions_anterieures(self):
        origine = donnees()
        changees = origine[:15] + [Bar(b.day, 500, 500) for b in origine[15:]]
        x = rejouer(origine, self.base, self.autre, etude(), "2020-01-12")
        y = rejouer(changees, self.base, self.autre, etude(), "2020-01-12")
        self.assertEqual(
            [d for d in x["differences_decisions"] if d["date"] < "2020-01-16"],
            [d for d in y["differences_decisions"] if d["date"] < "2020-01-16"])

    def test_pas_de_validation_sans_separation(self):
        with self.assertRaises(ValueError):
            rejouer(donnees(), self.base, self.autre, etude(), "2020-01-01")
        with self.assertRaises(ValueError):
            rejouer(donnees(), self.base, self.autre, etude(), "2020-02-01")

    def test_capital_egal_obligatoire(self):
        with self.assertRaises(ValueError):
            rejouer(donnees(), self.base, replace(self.autre, initial_cash=2000),
                    etude(), "2020-01-12")

    def test_source_et_date_de_publication_obligatoires(self):
        with self.assertRaises(ValueError):
            replace(etude(), source="")
        with self.assertRaises(ValueError):
            replace(etude(), date_publication="2027-01-01")


if __name__ == "__main__":
    unittest.main()
