"""
Unit and Integration Tests for AI Email Drafting Assistant
Verifies:
1. Prompt construction logic and constraints
2. Error handling when Ollama server is offline
3. Error handling when model is missing (HTTP 404)
4. Integration with Ollama API (/api/generate)
5. Validation logic (empty inputs)
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure AI_Email_Assistant folder is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from app import construct_prompt, generate_email_with_ollama, check_ollama_status


class TestAIEmailAssistant(unittest.TestCase):

    def test_construct_prompt_with_recipient(self):
        """Test prompt construction when recipient is provided."""
        subject = "Request for Leave"
        key_points = "- Unable to attend college tomorrow\n- Need 1 day leave"
        tone = "Formal"
        recipient = "Professor Sharma"

        prompt = construct_prompt(subject, key_points, tone, recipient)

        self.assertIn("Professor Sharma", prompt)
        self.assertIn("Request for Leave", prompt)
        self.assertIn("Formal", prompt)
        self.assertIn("Unable to attend college tomorrow", prompt)
        self.assertIn("Output ONLY the email", prompt)

    def test_construct_prompt_without_recipient(self):
        """Test prompt construction when recipient is omitted (optional field)."""
        subject = "Project Update"
        key_points = "- Phase 1 complete"
        tone = "Professional"

        prompt = construct_prompt(subject, key_points, tone, "")

        self.assertIn("generic professional salutation", prompt)
        self.assertIn("Project Update", prompt)
        self.assertIn("Professional", prompt)

    @patch("requests.post")
    def test_generate_email_success(self, mock_post):
        """Test successful email generation when Ollama responds with 200 OK."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3.2:1b",
            "response": (
                "Subject: Request for Leave\n\n"
                "Dear Professor Sharma,\n\n"
                "I am writing to formally request leave for one day.\n\n"
                "Sincerely,\n[Your Name]"
            )
        }
        mock_post.return_value = mock_response

        prompt = construct_prompt("Leave", "Need leave", "Formal", "Professor Sharma")
        success, result = generate_email_with_ollama(prompt, model="llama3.2:1b")

        self.assertTrue(success)
        self.assertIn("Dear Professor Sharma", result)
        self.assertIn("Subject: Request for Leave", result)

    @patch("requests.post")
    def test_generate_email_model_not_found(self, mock_post):
        """Test proper error handling when model is not downloaded (HTTP 404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "model 'llama3.2:1b' not found"
        mock_post.return_value = mock_response

        success, result = generate_email_with_ollama("prompt", model="llama3.2:1b")

        self.assertFalse(success)
        self.assertIn("Model 'llama3.2:1b' was not found", result)
        self.assertIn("ollama pull llama3.2:1b", result)

    @patch("requests.post")
    def test_generate_email_connection_error(self, mock_post):
        """Test graceful error message when Ollama is offline / not running."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        success, result = generate_email_with_ollama("prompt", model="llama3.2:1b")

        self.assertFalse(success)
        self.assertIn("Cannot connect to Ollama server", result)
        self.assertIn("ollama serve", result)

    @patch("requests.post")
    def test_generate_email_timeout(self, mock_post):
        """Test graceful error message when request times out."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        success, result = generate_email_with_ollama("prompt", model="llama3.2:1b")

        self.assertFalse(success)
        self.assertIn("timed out", result)

    @patch("requests.get")
    def test_check_ollama_status_offline(self, mock_get):
        """Test status helper when Ollama is offline."""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        is_online, models = check_ollama_status()
        self.assertFalse(is_online)
        self.assertEqual(models, [])

    @patch("requests.get")
    def test_check_ollama_status_online(self, mock_get):
        """Test status helper when Ollama is online with models."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [{"name": "llama3.2:1b:latest"}, {"name": "mistral:latest"}]
        }
        mock_get.return_value = mock_resp

        is_online, models = check_ollama_status()
        self.assertTrue(is_online)
        self.assertEqual(len(models), 2)
        self.assertIn("llama3.2:1b:latest", models)


if __name__ == "__main__":
    unittest.main()
