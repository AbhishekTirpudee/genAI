"""Built-in Web Server for the Multi-Agent Technical Reporting Studio."""

from __future__ import annotations
import json
import logging
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any

from tech_reporter.config import AppConfig
from tech_reporter.orchestrator import MultiAgentOrchestrator
from tech_reporter.models import AgentEvent

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).parent / "static"


class StudioRequestHandler(BaseHTTPRequestHandler):
    """Handles static files, API execution, and reporting dashboard."""

    config: AppConfig = AppConfig.from_env()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            index_path = STATIC_DIR / "index.html"
            if index_path.exists():
                self._send_file(index_path, "text/html; charset=utf-8")
            else:
                self._send_text("404 Dashboard HTML Not Found", 404)
        elif path.startswith("/reports/"):
            filename = path.replace("/reports/", "").strip("/")
            file_path = self.config.output_dir / filename
            if file_path.exists() and file_path.is_file():
                mime = "text/html" if filename.endswith(".html") else "text/markdown"
                self._send_file(file_path, mime)
            else:
                self._send_text("Report Not Found", 404)
        elif path == "/api/status":
            self._send_json({"status": "ready", "provider": self.config.llm_provider})
        else:
            self._send_text("Not Found", 404)

    def do_POST(self):
        if self.path == "/api/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")

            try:
                payload = json.loads(post_data)
                technology = payload.get("technology", "").strip()
                focus_areas = payload.get("focus_areas", [])
                audience = payload.get("target_audience", "Principal Engineers & Systems Architects")
                documents = payload.get("documents", None)

                if not technology:
                    self._send_json({"error": "Technology name is required"}, status=400)
                    return

                collected_events = []
                def on_event(ev: AgentEvent):
                    collected_events.append(ev.to_dict())

                orchestrator = MultiAgentOrchestrator(
                    config=self.config,
                    event_callback=on_event
                )

                report = orchestrator.run(
                    technology=technology,
                    focus_areas=focus_areas,
                    target_audience=audience,
                    documents=documents
                )

                response_data = {
                    "status": "success",
                    "events": collected_events,
                    "report": report.to_dict()
                }
                self._send_json(response_data)

            except Exception as e:
                logger.exception("Error processing report generation")
                self._send_json({"error": str(e)}, status=500)
        else:
            self._send_text("Not Found", 404)

    def _send_file(self, filepath: Path, content_type: str):
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_text(f"Error reading file: {e}", 500)

    def _send_text(self, text: str, status: int = 200):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, data: Dict[str, Any], status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress noisy standard HTTP logs unless debugging
        return


def start_server(host: str = "127.0.0.1", port: int = 8080, config: Optional[AppConfig] = None):
    """Starts the Web Studio HTTP Server."""
    if config:
        StudioRequestHandler.config = config
    server_address = (host, port)
    httpd = HTTPServer(server_address, StudioRequestHandler)
    print(f"\n=======================================================")
    print(f" 🌐 Multi-Agent Technical Report Studio Started")
    print(f" URL: http://{host}:{port}")
    print(f" Output Directory: {StudioRequestHandler.config.output_dir.resolve()}")
    print(f" Press Ctrl+C to terminate the server.")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Studio Server...")
        httpd.server_close()
