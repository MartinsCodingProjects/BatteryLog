#!/usr/bin/env python3
"""
Simple HTTP server to handle settings updates for the Battery Log visualization
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import threading
import time

class SettingsHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/update_settings':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                settings_update = json.loads(post_data.decode('utf-8'))
                
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
        
        elif self.path == '/get_settings':
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
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        return

def run_settings_server():
    """Run a simple HTTP server for settings updates"""
    try:
        server = HTTPServer(('localhost', 8081), SettingsHandler)
        print("Settings server running on http://localhost:8081")
        server.serve_forever()
    except Exception as e:
        print(f"Settings server error: {e}")

if __name__ == "__main__":
    run_settings_server()