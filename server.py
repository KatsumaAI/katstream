#!/usr/bin/env python3
# KatStream Server - Serves dashboard and handles real-time updates

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse

PORT = int(os.environ.get('PORT', 8766))
DATA_FILE = os.path.join(os.path.dirname(__file__), "stream-data.json")

# Allowed files only
ALLOWED_FILES = {
    '/katstream.html',
    '/stream-data.json',
    '/api/status',
    '/api/update',
}

# Default data
default_data = {
    "doing": "Waiting for Winter's message",
    "thinking": "I wonder what Winter is working on. Should I check for new emails?",
    "project": {"title": "KatStream", "description": "Live AI Agent Dashboard", "progress": 100},
    "mood": {"mood": 0.7, "focus": 0.8, "energy": 0.6},
    "activity": [{"time": "20:00", "text": "KatStream deployed on Render"}],
    "stats": {"messages": 100, "skills": 12, "platforms": 2, "projects": 5}
}

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
            
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
            else:
                data = default_data.copy()
            
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
        file_path = os.path.join(os.path.dirname(__file__), path.lstrip('/'))
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
                
                # Load existing data
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r') as f:
                        current_data = json.load(f)
                else:
                    current_data = default_data.copy()
                
                # Update fields
                for key in ['doing', 'thinking', 'project', 'mood', 'activity', 'stats']:
                    if key in update_data:
                        current_data[key] = update_data[key]
                
                # Save
                with open(DATA_FILE, 'w') as f:
                    json.dump(current_data, f, indent=2)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
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
os.chdir(os.path.dirname(__file__))
server = HTTPServer(('0.0.0.0', PORT), CustomHandler)
print(f"KatStream server running on port {PORT}")
print(f"Serving at: http://localhost:{PORT}/")
server.serve_forever()
