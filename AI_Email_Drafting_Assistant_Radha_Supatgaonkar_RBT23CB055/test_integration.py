"""
Integration test for AI Email Drafting Assistant.
Starts a lightweight local HTTP mock on port 11434 conforming to Ollama API specs
(/api/tags and /api/generate) to verify end-to-end communication, prompt handling,
and email output formatting.
"""

import http.server
import socketserver
import threading
import json
import requests
import time
import sys
import os

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import construct_prompt, generate_email_with_ollama, check_ollama_status

PORT = 11434

class MockOllamaHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/tags":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response_data = {
                "models": [
                    {"name": "llama3.2:1b", "size": 1300000000},
                    {"name": "llama3:latest", "size": 4700000000}
                ]
            }
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            model = data.get("model", "")
            prompt = data.get("prompt", "")
            stream = data.get("stream", False)

            if model != "llama3.2:1b":
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"model '{model}' not found"}).encode("utf-8"))
                return

            # Simulate LLM response strictly fulfilling the prompt
            generated_email = (
                "Subject: Request for Leave\n\n"
                "Dear Professor Sharma,\n\n"
                "I am writing to formally request your permission for one day of leave tomorrow "
                "due to some personal work that requires my immediate attention. Consequently, "
                "I will be unable to attend college for the day.\n\n"
                "I will make sure to catch up on all missed class notes and assignments as soon as I return. "
                "Thank you for your understanding and consideration.\n\n"
                "Sincerely,\n"
                "[Your Name]"
            )

            response_data = {
                "model": "llama3.2:1b",
                "created_at": "2026-11-02T10:00:00Z",
                "response": generated_email,
                "done": True
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress standard logging to keep test output clean
        pass


def run_integration_test():
    print("=" * 60)
    print("Starting Mock Ollama Server on http://localhost:11434...")
    print("=" * 60)

    try:
        # Bind to 127.0.0.1 on port 11434
        server = socketserver.TCPServer(("127.0.0.1", PORT), MockOllamaHandler)
    except OSError as e:
        print(f"Could not bind to port {PORT}: {e}")
        return False

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(1)

    try:
        # Step 1: Verify Ollama Service Status
        print("\n[Step 1] Checking Ollama Status and Available Models...")
        is_online, models = check_ollama_status()
        print(f"  -> Ollama Online: {is_online}")
        print(f"  -> Detected Models: {models}")
        assert is_online is True, "Ollama should be online!"
        assert any("llama3.2:1b" in m for m in models), "llama3.2:1b should be present!"
        print("  [OK] Ollama status check passed.")

        # Step 2: Test Prompt Construction with Test Case
        print("\n[Step 2] Constructing Prompt with Test Case...")
        subject = "Request for Leave"
        recipient = "Professor Sharma"
        tone = "Formal"
        key_points = (
            "- I am unable to attend college tomorrow.\n"
            "- I have some personal work.\n"
            "- Request permission for one day of leave."
        )

        prompt = construct_prompt(subject, key_points, tone, recipient)
        print("Constructed Prompt Preview:\n---")
        print(prompt[:250] + "...\n---")
        assert "Professor Sharma" in prompt
        assert "Formal" in prompt
        assert "Request for Leave" in prompt
        print("  [OK] Prompt construction verified.")

        # Step 3: Test Email Generation via /api/generate
        print("\n[Step 3] Sending Generation Request to Ollama API...")
        success, email_text = generate_email_with_ollama(prompt, model="llama3.2:1b")
        print(f"  -> Request Success: {success}")
        print("\nGenerated Email Output:\n" + "=" * 50)
        print(email_text)
        print("=" * 50)

        assert success is True, "Generation should succeed!"
        assert "Dear Professor Sharma" in email_text
        assert "Request for Leave" in email_text
        assert "Sincerely" in email_text
        print("  [OK] Email generation and formatting verified.")

        # Step 4: Test Model Not Found (404 error handling)
        print("\n[Step 4] Testing Error Handling for Missing Model...")
        err_success, err_msg = generate_email_with_ollama(prompt, model="non_existent_model:latest")
        print(f"  -> Handled Gracefully: {not err_success}")
        print(f"  -> Error Message:\n{err_msg}")
        assert err_success is False
        assert "was not found" in err_msg
        print("  [OK] Missing model error handling verified.")

        print("\n" + "=" * 60)
        print("ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        return True

    finally:
        print("\nShutting down Mock Ollama Server...")
        server.shutdown()
        server.server_close()
        print("Server stopped cleanly.")


if __name__ == "__main__":
    success = run_integration_test()
    if not success:
        sys.exit(1)
