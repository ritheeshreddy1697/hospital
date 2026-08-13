import unittest
import os
import json
from rag_engine import HospilotRAGEngine
from seed_data import init_db

class TestHospilotRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Re-initialize DB to clean state
        init_db()
        cls.engine = HospilotRAGEngine()

    def test_example_1_simple_count(self):
        query = "How many ICU beds are available right now?"
        res = self.engine.generate_sql_and_answer(query)
        print("\n=== TEST 1: Simple Count ===")
        print("Question:", res["question"])
        print("SQL Generated:", res["reasoning_sql"])
        print("Answer:\n", res["answer"])

        self.assertTrue(res["is_answerable"])
        self.assertIn("SELECT COUNT(*)", res["reasoning_sql"])
        self.assertIn("6 ICU beds", res["answer"])

    def test_example_2_occupancy_ranking(self):
        query = "Which wards have the highest bed occupancy right now?"
        res = self.engine.generate_sql_and_answer(query)
        print("\n=== TEST 2: Occupancy Ranking ===")
        print("Question:", res["question"])
        print("SQL Generated:", res["reasoning_sql"])
        print("Answer:\n", res["answer"])

        self.assertTrue(res["is_answerable"])
        self.assertIn("occupancy_percent", res["reasoning_sql"])
        self.assertIn("Semi-Private", res["answer"])
        self.assertIn("50.0%", res["answer"])

    def test_example_3_ambiguous_summary(self):
        query = "how are beds doing?"
        res = self.engine.generate_sql_and_answer(query)
        print("\n=== TEST 3: Ambiguous Summary ===")
        print("Question:", res["question"])
        print("SQL Generated:", res["reasoning_sql"])
        print("Answer:\n", res["answer"])

        self.assertTrue(res["is_answerable"])
        self.assertIn("GROUP BY ward, status", res["reasoning_sql"])
        self.assertIn("Available", res["answer"])

    def test_example_4_unanswerable_refusal(self):
        query = "What is our average patient satisfaction rating this month?"
        res = self.engine.generate_sql_and_answer(query)
        print("\n=== TEST 4: Unanswerable Refusal ===")
        print("Question:", res["question"])
        print("SQL Generated:", res["reasoning_sql"])
        print("Answer:\n", res["answer"])

        self.assertFalse(res["is_answerable"])
        self.assertIsNone(res["reasoning_sql"])
        self.assertIn("I don't have access to satisfaction data", res["answer"])

    def test_rephrased_queries(self):
        query = "Are there any open ICU beds tonight?"
        res = self.engine.generate_sql_and_answer(query)
        self.assertTrue(res["is_answerable"])
        self.assertIn("6 ICU beds", res["answer"])

if __name__ == "__main__":
    unittest.main()
