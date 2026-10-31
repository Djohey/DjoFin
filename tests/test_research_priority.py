import unittest
from djofin.research_priority import classify

class ResearchPriorityTests(unittest.TestCase):
    def test_unknown_is_explored(self):
        row = classify({"id":"1","title":"Unexpected new field of research"})
        self.assertEqual(row["priority"],"review")
        self.assertTrue(row["unknown_topic"])
    def test_unknown_without_trigger(self):
        row = classify({"id":"2","title":"Novel observation in deep ocean"})
        self.assertEqual(row["priority"],"explore")
    def test_macro(self):
        row = classify({"id":"3","title":"Central bank inflation forecast"})
        self.assertIn("macro",row["domains"])
        self.assertFalse(row["investment_signal"])
    def test_word_boundaries(self):
        row = classify({"id":"4","title":"Brainstorming in creative teams"})
        self.assertNotIn("technology",row["domains"])

if __name__ == "__main__":
    unittest.main()
