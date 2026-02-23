#!/usr/bin/env python3
# KatStream Server - Serves dashboard and handles real-time updates

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse
import threading

PORT = int(os.environ.get('PORT', 8766))

# Get the directory where the script is running
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "stream-data.json")

# Allowed files only
ALLOWED_FILES = {
    '/katstream.html',
    '/stream-data.json',
    '/api/status',
    '/api/update',
}

# Initial data
initial_data = {
    "doing": "Initializing KatStream",
    "thinking": "Waiting for first update...",
    "project": {"title": "KatStream", "description": "Live AI Agent Dashboard", "progress": 0},
    "mood": {"mood": 0.5, "focus": 0.5, "energy": 0.5},
    "activity": [],
    "stats": {"messages": 0, "skills": 12, "platforms": 2, "projects": 1}
}

# Initialize data file if it doesn't exist
def init_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump(initial_data, f, indent=2)

init_data_file()

# Thread-safe file reading
def read_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return initial_data.copy()

# Thread-safe file writing
def write_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

# Deep merge function - updates nested dicts instead of replacing
def deep_merge(base, updates):
    """Merge updates into base dict recursively"""
    for key, value in updates.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base

def send_error(self, code, message):
    """Send error response with custom error page"""
    self.send_response(code)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    
    error_pages = {
        404: '<html><body style="background:#0a0a0f;color:#f4f4f5;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"><div style="text-align:center"><h1 style="font-size:4rem;margin:0;">404</h1><p style="color:#71717a;">Page not found</p></div></body></html>',
        403: '<html><body style="background:#0a0a0f;color:#f4f4f5;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"><div style="text-align:center"><h1 style="font-size:4rem;margin:0;">403</h1><p style="color:#71717a;">Access denied</p></div></body></html>',
        500: '<html><body style="background:#0a0a0f;color:#f4f4f5;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"><div style="text-align:center"><h1 style="font-size:4rem;margin:0;">500</h1><p style="color:#71717a;">Server error</p></div></body></html>',
    }
    
    self.wfile.write(error_pages.get(code, message).encode())

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # API endpoints
        if path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Read from file
            data = read_data()
            data['timestamp'] = datetime.now().strftime("%H:%M:%S")
            self.wfile.write(json.dumps(data).encode())
            return
        
        # Serve katstream.html at root "/"
        if path == "/" or path == "/index.html":
            path = "/katstream.html"
        
        # Only allow specific files
        if path not in ALLOWED_FILES:
            send_error(self, 404, "Not Found")
            return
        
        # Check if file exists
        file_path = os.path.join(SCRIPT_DIR, path.lstrip('/'))
        if not os.path.exists(file_path):
            send_error(self, 404, "Not Found")
            return
        
        # Serve the file
        self.path = path
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        # API endpoint for updating status
        if parsed.path == "/api/update":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                update_data = json.loads(post_data.decode('utf-8'))
                
                # Read current data
                current_data = read_data()
                
                # Merge updates (doesn't replace everything)
                merged_data = deep_merge(current_data, update_data)
                
                # Add timestamp to activity if provided
                if 'activity' in update_data and update_data['activity']:
                    # Add new activity to beginning of list
                    if isinstance(merged_data['activity'], list):
                        merged_data['activity'] = update_data['activity'] + merged_data['activity'][:9]  # Keep last 10
                
                # Save merged data
                if write_data(merged_data):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "data": merged_data}).encode())
                else:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Failed to save"}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        
        send_error(self, 404, "Not Found")
    
    def log_message(self, format, *args):
        pass  # Suppress logging

# Run server
os.chdir(SCRIPT_DIR)
server = HTTPServer(('0.0.0.0', PORT), CustomHandler)
print(f"KatStream server running on port {PORT}")
print(f"Serving at: http://localhost:{PORT}/")
server.serve_forever()
