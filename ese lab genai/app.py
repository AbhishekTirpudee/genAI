#!/usr/bin/env python3
"""
Electronic Component Catalogue RAG Web Server
=============================================
Runs on Python 3 standard library (no pip installs needed to launch).
Serves the modern frontend and handles RAG queries via REST API.
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import tempfile

# Configure UTF-8 encoding for Windows console compatibility
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from rag_engine import ComponentRAGEngine

PORT = 8501
rag_engine = None

class RAGRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for easy local API testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # API: Get catalogue components
        if parsed.path == '/api/components':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(rag_engine.components).encode('utf-8'))
            return
            
        # API: Search components directly
        if parsed.path == '/api/search':
            params = urllib.parse.parse_qs(parsed.query)
            q = params.get('q', [''])[0]
            top_k = int(params.get('top_k', [5])[0])
            results = rag_engine.search(q, top_k=top_k)
            payload = [{
                "part_number": c["part_number"],
                "category": c["category"],
                "page": c["page_number"],
                "score": round(score, 3),
                "data": c["component_data"]
            } for c, score in results]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))
            return

        # Default: Serve static files
        return super().do_GET()

    def do_POST(self):
        global rag_engine
        parsed = urllib.parse.urlparse(self.path)
        
        # API: RAG Query Endpoint
        if parsed.path == '/api/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_length)
            try:
                data = json.loads(post_body.decode('utf-8'))
                query = data.get('query', '')
                api_key = data.get('api_key', None)
                
                if not query:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Empty query"}).encode('utf-8'))
                    return

                # Execute RAG query
                result = rag_engine.generate_response(query, api_key=api_key)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

        # API: Upload custom JSON/CSV catalogue
        if parsed.path == '/api/upload':
            content_length = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_length)
            temporary_path = None
            try:
                data = json.loads(post_body.decode('utf-8'))
                custom_components = data.get('components', [])
                if not isinstance(custom_components, list) or not custom_components:
                    raise ValueError("Catalogue must contain at least one component.")
                if any(not isinstance(component, dict) or not component.get("part_number") for component in custom_components):
                    raise ValueError("Every component must be an object with a part_number.")

                catalogue_path = rag_engine.catalogue_path
                catalogue_dir = os.path.dirname(os.path.abspath(catalogue_path))
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=catalogue_dir, suffix=".json", delete=False
                ) as temporary_file:
                    temporary_path = temporary_file.name
                    json.dump(custom_components, temporary_file, indent=2)

                updated_engine = ComponentRAGEngine(temporary_path)
                os.replace(temporary_path, catalogue_path)
                temporary_path = None
                updated_engine.catalogue_path = catalogue_path
                rag_engine = updated_engine

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "count": len(custom_components),
                    "message": f"Successfully indexed {len(custom_components)} components into RAG vector store!"
                }).encode('utf-8'))
                return
            except Exception as e:
                if temporary_path and os.path.exists(temporary_path):
                    os.remove(temporary_path)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

def main():
    global rag_engine
    print("[*] Initializing Electronic Component RAG Hybrid Index...")
    rag_engine = ComponentRAGEngine("electronic_components_catalogue.json")
    print(f"[*] Indexed {len(rag_engine.components)} electronic components successfully!")
    
    # Allow port reuse to prevent 'Address already in use' errors
    socketserver.TCPServer.allow_reuse_address = True
    
    server_address = ('', PORT)
    try:
        with socketserver.TCPServer(server_address, RAGRequestHandler) as httpd:
            print("="*60)
            print(">> Electronic Component Catalogue RAG Chatbot is RUNNING")
            print(f">> Local Access URL: http://localhost:{PORT}")
            print(f">> Workspace: {os.getcwd()}")
            print("="*60 + "\n")
            httpd.serve_forever()
    except OSError as e:
        alt_port = 8502
        print(f"[!] Port {PORT} busy, attempting Port {alt_port}...")
        with socketserver.TCPServer(('', alt_port), RAGRequestHandler) as httpd:
            print(f">> Electronic Component RAG Chatbot is RUNNING at: http://localhost:{alt_port}")
            httpd.serve_forever()

if __name__ == "__main__":
    main()
