"""Independent audit regression checks for candidate v0.2 (NOT out-of-sample validation)."""
import unittest
from djofin.research_priority_v02 import TriageError, classify, normalise, RULES_SHA256

CASES = [
("US imposes new sanctions on Russia",["geopolitics"],"routine"),
("Tariffs on Chinese goods rise",["geopolitics"],"routine"),
("ECB keeps interest rates unchanged",["macro"],"routine"),
("Moderna vaccines shipped to Europe",["pharma"],"routine"),
("Mergers surge in Q3",["finance"],"routine"),
("Pfizer acquires Seagen",["finance"],"routine"),
("Novavax withdraws guidance",["finance"],"review"),
("Company withdrew its filing",[],"review"),
("La BCE relève ses taux directeurs",["macro"],"routine"),
("Résultats annuels de Sanofi en hausse",["finance"],"routine"),
("Sanctions américaines contre l'Iran",["geopolitics"],"routine"),
("Fed raises rates by 25 bp",["macro"],"routine"),
("AI boom lifts Nvidia",["technology"],"routine"),
("Blue-chip stocks rally on Wall Street",[],"explore"),
("Weather forecast: storm expected",[],"explore"),
("CEO resigns over conflict of interest",[],"explore"),
("Board approval of annual dividend",["finance"],"routine"),
("No emergency, says regulator",[],"explore"),
("Pfizer trial results due next week",["pharma"],"routine"),
("Nvidia raises revenue forecast",["finance"],"routine"),
("Phase-3 data for new drug",["pharma"],"routine"),
("Phase III trial of CureVac",["pharma"],"routine"),
("FDA GRANTS EMERGENCY USE",["pharma"],"review"),
("Quarterly earnings beat estimates",["finance"],"routine"),
]

class AuditRegression(unittest.TestCase):
    def test_24_titles(self):
        for title, domains, priority in CASES:
            with self.subTest(title=title):
                r=classify({"id":"x","title":title})
                self.assertEqual(r["domains"],domains)
                self.assertEqual(r["priority"],priority)
    def test_invalid_inputs(self):
        for item in ({"title":"earnings"},{"id":"","title":"x"},{"id":3,"title":"x"},
                     {"id":"x","title":42},{"id":"x","summary":["list"]},"text",None):
            with self.subTest(item=item),self.assertRaises(TriageError):
                classify(item)
    def test_empty(self):
        for item in ({"id":"x"},{"id":"x","title":None},{"id":"x","title":"  "}):
            self.assertTrue(classify(item)["empty_text"])
    def test_summary(self):
        r=classify({"id":"x","title":"Breaking","summary":"FDA rejects application"})
        self.assertEqual(r["priority"],"review")
        self.assertIn("pharma",r["domains"])
    def test_case_sensitive_acronyms(self):
        self.assertEqual(classify({"id":"x","title":"J'ai vu le marché monter"})["domains"],[])
        self.assertEqual(classify({"id":"x","title":"Les fed-ex livrent"})["domains"],[])
    def test_negation(self):
        r=classify({"id":"x","title":"Regulator says no emergency approval needed"})
        self.assertEqual(r["triggers"],[])
        self.assertEqual(r["negated_triggers"],["approval","emergency"])
    def test_single_domain(self):
        self.assertEqual(classify({"id":"x","title":"Nvidia raises revenue forecast"})["domains"],["finance"])
    def test_matches(self):
        self.assertEqual(classify({"id":"x","title":"ECB keeps interest rates unchanged"})["matched_terms"],{"macro":["interest rates","ECB"]})
    def test_determinism(self):
        item={"id":"x","title":"Tariffs on chips"}
        self.assertEqual(classify(item),classify(item))
        self.assertEqual(len(RULES_SHA256),64)
        self.assertFalse(classify(item)["investment_signal"])
    def test_normalise(self):
        self.assertEqual(normalise("Résultats  semi-annuels l’été"),"resultats semi annuels l ete")

if __name__=="__main__":
    unittest.main()
