"""
Comprehensive Unit Tests for College Result Analysis Agent.
Verifies query parsing, SQL generation, execution, formatters, and security checks.
"""

import unittest
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.query_engine import ResultAnalysisAgent
from agent.safety import sanitize_and_validate_sql
from database.db import execute_safe_query

class TestResultAnalysisAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = ResultAnalysisAgent()

    def test_overall_pass_percentage(self):
        """Test overall college pass percentage calculation."""
        res = self.agent.process_query("What is the overall pass percentage of the college?")
        self.assertTrue(res['success'])
        self.assertIn("Overall College Pass Percentage", res['answer'])
        self.assertIsNotNone(res['chart'])
        self.assertIn("Overall Pass Rate", res['kpis'])
        self.assertGreater(len(res['data']), 0)
        self.assertGreater(res['data'][0]['pass_percentage'], 70.0)

    def test_department_pass_percentage(self):
        """Test department pass percentage and comparison."""
        res = self.agent.process_query("Compare pass percentage of all departments")
        self.assertTrue(res['success'])
        self.assertIn("Department Performance Overview", res['answer'])
        self.assertIsNotNone(res['chart'])
        self.assertEqual(len(res['data']), 4)  # 4 departments: CSE, IT, ECE, MECH

    def test_single_department_pass_percentage(self):
        """Test specific department pass percentage (e.g. CSE)."""
        res = self.agent.process_query("What is the pass percentage of Computer Science?")
        self.assertTrue(res['success'])
        self.assertEqual(len(res['data']), 1)
        self.assertEqual(res['data'][0]['dept_code'], 'CSE')

    def test_subject_wise_performance(self):
        """Test subject-wise performance analytics."""
        res = self.agent.process_query("Show subject-wise performance of semester 4")
        self.assertTrue(res['success'])
        self.assertIn("Subject-Wise Performance Analysis", res['answer'])
        self.assertIsNotNone(res['chart'])
        self.assertGreater(len(res['data']), 5)

    def test_single_subject_query(self):
        """Test single subject DBMS statistics."""
        res = self.agent.process_query("What is the pass percentage in Database Management Systems?")
        self.assertTrue(res['success'])
        self.assertIn("Database Management Systems", res['answer'])
        self.assertIn("Pass Rate", res['kpis'])
        self.assertEqual(res['data'][0]['subject_code'], 'CS401')

    def test_toughest_subject_query(self):
        """Test hardest / lowest pass percentage subject detection."""
        res = self.agent.process_query("Which subject has the lowest pass percentage?")
        self.assertTrue(res['success'])
        self.assertIn("Challenging", res['answer'])
        self.assertLessEqual(len(res['data']), 5)

    def test_student_roll_number_marksheet(self):
        """Test individual student report card by roll number."""
        res = self.agent.process_query("Show complete report card for roll CS24-001")
        self.assertTrue(res['success'])
        self.assertIn("Student Academic Report Card", res['answer'])
        self.assertIsNotNone(res['chart'])
        self.assertEqual(res['chart']['type'], 'radar')
        self.assertGreater(len(res['data']), 0)

    def test_rank_list_toppers(self):
        """Test top rankers retrieval."""
        res = self.agent.process_query("Show top 5 students in Computer Science")
        self.assertTrue(res['success'])
        self.assertIn("Academic Rank List", res['answer'])
        self.assertLessEqual(len(res['data']), 5)
        self.assertIn("College Topper", res['kpis'])

    def test_subject_topper(self):
        """Test highest scorer in a specific subject."""
        res = self.agent.process_query("Who scored the highest marks in Operating Systems?")
        self.assertTrue(res['success'])
        self.assertIn("Top Scorer", res['answer'])
        self.assertIn("Topper", res['kpis'])

    def test_backlog_students(self):
        """Test students who failed or have backlogs."""
        res = self.agent.process_query("List all students who failed")
        self.assertTrue(res['success'])
        self.assertIn("Backlog / Failure Report", res['answer'])

    def test_grade_distribution(self):
        """Test overall grade / division distribution."""
        res = self.agent.process_query("What is the grade distribution?")
        self.assertTrue(res['success'])
        self.assertIn("Result & Grade Classification", res['answer'])
        self.assertIsNotNone(res['chart'])

    def test_section_comparison(self):
        """Test Section A vs Section B comparison."""
        res = self.agent.process_query("Compare performance of Section A vs Section B")
        self.assertTrue(res['success'])
        self.assertIn("Section-Wise Academic Comparison", res['answer'])

    def test_sql_injection_prevention(self):
        """Test that malicious or destructive SQL is strictly blocked."""
        malicious_inputs = [
            "DROP TABLE students",
            "DELETE FROM marks WHERE 1=1",
            "UPDATE students SET name = 'Hacked'",
            "INSERT INTO students VALUES (999, 'HACK', 'HACK', 'Hacker', 'Male', 'h@h.com', 1, 4, 'A', '2024')",
            "SELECT * FROM students; DROP TABLE marks;"
        ]
        for query in malicious_inputs:
            is_valid, _, error = sanitize_and_validate_sql(query)
            self.assertFalse(is_valid, f"Failed to block: {query}")
            self.assertIn("forbidden", error.lower() if error else "")

if __name__ == '__main__':
    unittest.main()
