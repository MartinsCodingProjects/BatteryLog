#!/usr/bin/env python3
"""
Simple HTTP server to handle settings updates for the Battery Log visualization
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
import threading
import time

class CombinedHandler(SimpleHTTPRequestHandler):
    def normalize_keys(self, data):
        """Convert camelCase keys to snake_case."""
        def camel_to_snake(name):
            import re
            s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
            return s1.lower()

        if isinstance(data, dict):
            return {camel_to_snake(k): self.normalize_keys(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.normalize_keys(i) for i in data]
        else:
            return data

    def do_POST(self):
        if self.path == '/update_settings':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                settings_update = json.loads(post_data.decode('utf-8'))

                # Normalize keys to snake_case
                settings_update = self.normalize_keys(settings_update)

                # Load current settings
                settings_file = 'user_settings.json'
                if os.path.exists(settings_file):
                    with open(settings_file, 'r') as f:
                        current_settings = json.load(f)
                else:
                    current_settings = {"logging": {"log_interval": 60}, "visualization": {}}

                # Update visualization settings
                current_settings['visualization'].update(settings_update)

                # Save updated settings
                with open(settings_file, 'w') as f:
                    json.dump(current_settings, f, indent=4)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_error(501, "Unsupported method ('POST')")

    def do_GET(self):
        try:
            if self.path == '/':
                self.path = '/battery_log_visualization.html'  # Default to the main HTML file
            if self.path == '/get_settings':
                try:
                    settings_file = 'user_settings.json'
                    if os.path.exists(settings_file):
                        with open(settings_file, 'r') as f:
                            settings = json.load(f)
                    else:
                        settings = {"logging": {"log_interval": 60}, "visualization": {"time_range": "1h", "auto_refresh": True, "refresh_interval": 60000}}

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(settings).encode())

                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
            else:
                super().do_GET()
        except ConnectionAbortedError:
            print("Warning: Connection aborted by the client during GET request.")

def run_settings_server():
    """Run a simple HTTP server for settings updates"""
    try:
        server = HTTPServer(('localhost', 8081), CombinedHandler)
        print("Settings server running on http://localhost:8081")
        server.serve_forever()
    except Exception as e:
        print(f"Settings server error: {e}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))  # Serve files from the current directory
    run_settings_server()