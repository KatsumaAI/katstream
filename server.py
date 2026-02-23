#!/usr/bin/env python3
# KatStream Server - Real-time updates via WebSockets

import json
import os
import asyncio
import websockets
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse
import threading
from datetime import datetime

PORT = int(os.environ.get('PORT', 8766))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Current live data (in-memory)
current_data = {
    "doing": "Waiting for updates...",
    "thinking": "KatStream initializing...",
    "project": {"title": "KatStream", "description": "Live AI Agent Dashboard", "progress": 0},
    "mood": {"mood": 0.5, "focus": 0.5, "energy": 0.5},
    "activity": [{"time": datetime.now().strftime("%H:%M"), "text": "Server started"}],
    "stats": {"messages": 0, "skills": 12, "platforms": 2, "projects": 1}
}

# Connected WebSocket clients
connected_clients = set()

# Allowed files only
ALLOWED_FILES = {'/katstream.html', '/stream-data.json', '/api/status', '/ws'}

# HTML for WebSocket client
WS_CLIENT_HTML = '''
<script>
let ws = null;
let reconnectAttempts = 0;

function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(protocol + '//' + window.location.host + '/ws');
    
    ws.onopen = () => {
        console.log('Connected to KatStream!');
        reconnectAttempts = 0;
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateUI(data);
        } catch(e) {
            console.error('Error parsing message:', e);
        }
    };
    
    ws.onclose = () => {
        console.log('Disconnected, reconnecting...');
        setTimeout(connect, Math.min(30000, 1000 * Math.pow(2, reconnectAttempts)));
        reconnectAttempts++;
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function updateUI(data) {
    // Update doing
    if (data.doing) document.getElementById('doing-text').textContent = data.doing;
    
    // Update thinking
    if (data.thinking) {
        document.getElementById('thinking-text').textContent = data.thinking;
        document.getElementById('neural-thought').textContent = data.thinking;
    }
    
    // Update project
    if (data.project) {
        if (data.project.title) document.getElementById('project-title').textContent = data.project.title;
        if (data.project.description) document.getElementById('project-desc').textContent = data.project.description;
        if (data.project.progress !== undefined) {
            document.getElementById('progress-fill').style.width = data.project.progress + '%';
            document.getElementById('progress-value').textContent = data.project.progress + '%';
        }
    }
    
    // Update mood
    if (data.mood) {
        if (data.mood.mood !== undefined) document.getElementById('mood-mood').textContent = data.mood.mood;
        if (data.mood.focus !== undefined) document.getElementById('mood-focus').textContent = data.mood.focus;
        if (data.mood.energy !== undefined) document.getElementById('mood-energy').textContent = data.mood.energy;
    }
    
    // Update stats
    if (data.stats) {
        if (data.stats.messages !== undefined) document.getElementById('stat-messages').textContent = data.stats.messages;
        if (data.stats.skills !== undefined) document.getElementById('stat-skills').textContent = data.stats.skills;
        if (data.stats.platforms !== undefined) document.getElementById('stat-platforms').textContent = data.stats.platforms;
        if (data.stats.projects !== undefined) document.getElementById('stat-projects').textContent = data.stats.projects;
    }
    
    // Update activity
    if (data.activity && Array.isArray(data.activity)) {
        const html = data.activity.map(a => 
            `<div class="activity-item"><span class="activity-time">${a.time}</span><span class="activity-text">${a.text}</span></div>`
        ).join('');
        document.getElementById('activity-list').innerHTML = html;
    }
    
    // Update timestamp
    document.getElementById('timestamp').textContent = new Date().toLocaleTimeString('en-US', {hour12: false});
}

// Connect when page loads
connect();
</script>
'''

# WebSocket handler
async def websocket_handler(websocket, path):
    """Handle WebSocket connections"""
    connected_clients.add(websocket)
    print(f"Client connected. Total: {len(connected_clients)}")
    
    # Send current data to new client
    await websocket.send(json.dumps(current_data))
    
    try:
        async for message in websocket:
            # Only accept updates from authenticated clients (you)
            try:
                data = json.loads(message)
                if data.get('auth') == 'katstream-secret-key':  # You can set a secret key
                    # Update current data
                    for key in ['doing', 'thinking', 'project', 'mood', 'activity', 'stats']:
                        if key in data:
                            current_data[key] = data[key]
                    
                    current_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
                    
                    # Broadcast to all connected clients
                    for client in connected_clients:
                        try:
                            await client.send(json.dumps(current_data))
                        except:
                            pass
            except:
                pass
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnected. Total: {len(connected_clients)}")

async def run_websocket_server():
    """Run WebSocket server"""
    async with websockets.serve(websocket_handler, "0.0.0.0", PORT + 1):
        await asyncio.Future()  # Run forever

def send_update_to_site(data):
    """Send update via WebSocket - for use by external scripts"""
    import websocket
    try:
        ws = websocket.create_connection(f"ws://localhost:{PORT + 1}/")
        ws.send(json.dumps(data))
        ws.close()
    except Exception as e:
        print(f"Failed to send update: {e}")

# HTTP Server
def send_error(self, code, message):
    self.send_response(code)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    error_pages = {
        404: '<html><body style="background:#0a0a0f;color:#f4f4f5;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"><div style="text-align:center"><h1 style="font-size:4rem;margin:0;">404</h1><p style="color:#71717a;">Page not found</p></div></body></html>',
    }
    self.wfile.write(error_pages.get(code, message).encode())

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # WebSocket upgrade
        if path == '/ws':
            # Handle WebSocket
            self.send_response(101)
            self.send_header('Upgrade', 'websocket')
            self.send_header('Connection', 'Upgrade')
            self.end_headers()
            return
        
        # API status
        if path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            current_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
            self.wfile.write(json.dumps(current_data).encode())
            return
        
        # Root serves katstream.html
        if path == "/" or path == "/index.html":
            path = "/katstream.html"
        
        # Only allow specific files
        if path not in ALLOWED_FILES:
            send_error(self, 404, "Not Found")
            return
        
        file_path = os.path.join(SCRIPT_DIR, path.lstrip('/'))
        if not os.path.exists(file_path):
            send_error(self, 404, "Not Found")
            return
        
        self.path = path
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def log_message(self, format, *args):
        pass

# Run both servers
if __name__ == "__main__":
    # Start WebSocket server in background
    import threading
    asyncio_thread = threading.Thread(target=lambda: asyncio.run(run_websocket_server()), daemon=True)
    asyncio_thread.start()
    
    # Start HTTP server
    os.chdir(SCRIPT_DIR)
    server = HTTPServer(('0.0.0.0', PORT), CustomHandler)
    print(f"KatStream server running on port {PORT}")
    print(f"WebSocket on port {PORT + 1}")
    server.serve_forever()
