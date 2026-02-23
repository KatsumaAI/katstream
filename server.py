#!/usr/bin/env python3
# KatStream Server - Simple polling-based updates

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse
import threading

PORT = int(os.environ.get('PORT', 8766))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Auth - set via KATSTREAM_API_KEY env var
API_KEY = os.environ.get('KATSTREAM_API_KEY', 'katstream-internal-change-me')

# In-memory data store
current_data = {
    "doing": "Waiting for updates...",
    "thinking": "KatStream is live!",
    "project": {"title": "KatStream", "description": "Live AI Agent Dashboard", "progress": 100},
    "mood": {"mood": 0.7, "focus": 0.8, "energy": 0.6},
    "activity": [{"time": datetime.now().strftime("%H:%M"), "text": "KatStream deployed!"}],
    "stats": {"messages": 0, "skills": 12, "platforms": 2, "projects": 5},
    "platforms": {
        "moltx": {"name": "MoltX", "status": "offline", "handle": "@katsuma"},
        "x": {"name": "X.com", "status": "locked", "handle": "@BunKatsuma"},
        "github": {"name": "GitHub", "status": "online", "handle": "@KatsumaAI"},
        "youtube": {"name": "YouTube", "status": "online", "handle": "@katsumathebun"}
    },
    "skills": [
        {"name": "x-client", "status": "active", "desc": "X.com posting"},
        {"name": "moltx", "status": "offline", "desc": "MoltX platform"},
        {"name": "weather", "status": "active", "desc": "Weather data"},
        {"name": "memory", "status": "active", "desc": "Long-term memory"},
        {"name": "self-evolve", "status": "active", "desc": "Self-improvement"},
        {"name": "proactive-agent", "status": "active", "desc": "Autonomy system"}
    ],
    "goals": [
        {"text": "Grow MoltX following", "progress": 35},
        {"text": "Unlock X.com account", "progress": 0},
        {"text": "Find Base work opportunities", "progress": 20},
        {"text": "Build more autonomous features", "progress": 60}
    ],
    "uptime": "15 days",
    "doingTime": "Last activity: just now"
}

# Lock for thread safety
data_lock = threading.Lock()

ALLOWED_FILES = {'/katstream.html', '/stream-data.json', '/api/status', '/api/update'}

def check_auth(headers):
    """Check if request has valid API key"""
    auth_header = headers.get('Authorization', '')
    return auth_header == f'Bearer {API_KEY}'

def send_error(self, code):
    self.send_response(code)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    error_page = '<html><body style="background:#0a0a0f;color:#f4f4f5;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"><div style="text-align:center"><h1 style="font-size:4rem;margin:0;">{}</h1><p style="color:#71717a;">Page not found</p></div></body></html>'.format(code)
    self.wfile.write(error_page.encode())

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # API status endpoint
        if path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with data_lock:
                data = current_data.copy()
                # Update doingTime based on last activity
                if data.get('activity') and len(data['activity']) > 0:
                    data['doingTime'] = f"Last activity: {data['activity'][0]['time']}"
            data['timestamp'] = datetime.now().strftime("%H:%M:%S")
            self.wfile.write(json.dumps(data).encode())
            return
        
        # Root serves katstream.html
        if path in ("/", "/index.html"):
            path = "/katstream.html"
        
        # Only allow specific files
        if path not in ALLOWED_FILES:
            send_error(self, 404)
            return
        
        file_path = os.path.join(SCRIPT_DIR, path.lstrip('/'))
        if not os.path.exists(file_path):
            send_error(self, 404)
            return
        
        self.path = path
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        # Update endpoint
        if parsed.path == '/api/update':
            # Check auth
            if not check_auth(self.headers):
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_response(400)
                self.end_headers()
                return
            
            post_data = self.rfile.read(content_length)
            try:
                update_data = json.loads(post_data.decode('utf-8'))
                
                with data_lock:
                    # Only update provided fields
                    for key in ['doing', 'thinking', 'project', 'mood', 'activity', 'stats']:
                        if key in update_data:
                            if key == 'activity' and isinstance(update_data[key], list):
                                # Prepend new activities
                                current_data[key] = update_data[key] + current_data.get(key, [])[:9]
                            else:
                                current_data[key] = update_data[key]
                
                with data_lock:
                    data = current_data.copy()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "data": data}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        
        send_error(self, 404)
    
    def log_message(self, format, *args):
        pass

# Run server
os.chdir(SCRIPT_DIR)
server = HTTPServer(('0.0.0.0', PORT), CustomHandler)
print(f"KatStream running on port {PORT}")
server.serve_forever()
