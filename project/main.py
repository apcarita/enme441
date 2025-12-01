#!/usr/bin/env python3
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
from stepperS import Stepper, interleave_rotate
from shifter import Shifter
import math

# Configuration
PORT = 8080
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '../frontend/dist')
DEV_MODE = not os.path.exists(FRONTEND_DIR)  # If dist doesn't exist, assume dev mode

# Motor state
class TurretState:
    def __init__(self):
        self.azimuth = 0.0  # radians - current position
        self.altitude = 0.0  # radians - current position
        self.laser_on = False
        self.lock = threading.Lock()
        
        # Movement velocity (set by commands)
        self.azimuth_velocity = 0.0  # -1, 0, or 1
        self.altitude_velocity = 0.0  # -1, 0, or 1
        
        # Initialize hardware
        self.shifter = Shifter(data=2, latch=3, clock=4)
        self.azimuth_motor = Stepper(self.shifter, bit_offset=4)  # QE-QH
        self.altitude_motor = Stepper(self.shifter, bit_offset=0)  # QA-QD
        
        # Start continuous movement thread
        self.running = True
        self.movement_thread = threading.Thread(target=self._movement_loop, daemon=True)
        self.movement_thread.start()
    
    def set_velocity(self, azimuth_vel, altitude_vel):
        """Set movement velocity (-1, 0, or 1 for each axis)"""
        with self.lock:
            self.azimuth_velocity = max(-1, min(1, azimuth_vel))
            self.altitude_velocity = max(-1, min(1, altitude_vel))
    
    def _movement_loop(self):
        """Continuously move motors based on velocity"""
        STEP_SIZE = 0.02  # radians per step
        
        while self.running:
            with self.lock:
                az_vel = self.azimuth_velocity
                alt_vel = self.altitude_velocity
            
            # Calculate movement
            if az_vel != 0 or alt_vel != 0:
                az_move = STEP_SIZE * az_vel
                alt_move = STEP_SIZE * alt_vel
                
                # Apply movement
                new_az = self.azimuth + az_move
                new_alt = self.altitude + alt_move
                
                # Clamp to limits
                new_az = max(-3.14, min(3.14, new_az))
                new_alt = max(-1.57, min(1.57, new_alt))
                
                # Move motors
                az_deg = math.degrees(new_az - self.azimuth)
                alt_deg = math.degrees(new_alt - self.altitude)
                
                if az_deg != 0 or alt_deg != 0:
                    interleave_rotate(
                        [self.azimuth_motor, self.altitude_motor],
                        [az_deg, alt_deg]
                    )
                    
                    with self.lock:
                        self.azimuth = new_az
                        self.altitude = new_alt
            
            # Small delay to control movement speed
            time.sleep(0.01)  # 100Hz movement loop
    
    def get_position(self):
        """Get current position"""
        with self.lock:
            return {
                'azimuth': self.azimuth,
                'altitude': self.altitude,
                'laser': self.laser_on
            }
    
    def set_laser(self, state):
        """Control laser state"""
        with self.lock:
            self.laser_on = state
            # TODO: Implement actual laser GPIO control here
            # GPIO.output(LASER_PIN, GPIO.HIGH if state else GPIO.LOW)
    
    def calibrate(self):
        """Reset position to zero"""
        with self.lock:
            self.azimuth = 0.0
            self.altitude = 0.0
            # Motors stay in current physical position, just reset the reference

# Global state
turret_state = TurretState()

class TurretHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        
        # API endpoints
        if parsed.path == '/api/position':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            position = turret_state.get_position()
            self.wfile.write(json.dumps(position).encode())
            return
        
        # Serve static files for frontend
        self.serve_static_file(parsed.path)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON')
            return
        
        # Motor velocity control
        if parsed.path == '/api/move':
            azimuth_vel = float(data.get('azimuth', 0))
            altitude_vel = -float(data.get('altitude', 0))
            
            turret_state.set_velocity(azimuth_vel, altitude_vel)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            return
        
        # Laser control
        elif parsed.path == '/api/laser':
            laser_state = bool(data.get('laser', False))
            turret_state.set_laser(laser_state)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'laser': laser_state}).encode())
            return
        
        # Calibration
        elif parsed.path == '/api/calibrate':
            turret_state.calibrate()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'message': 'Calibrated to zero'}).encode())
            return
        
        self.send_error(404, 'Endpoint not found')
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def serve_static_file(self, path):
        """Serve static files from frontend dist directory"""
        # In dev mode, frontend is served by Vite on a different port
        if DEV_MODE:
            self.send_error(404, 'Dev mode: Use Vite dev server on port 5173')
            return
        
        if path == '/':
            path = '/index.html'
        
        file_path = os.path.join(FRONTEND_DIR, path.lstrip('/'))
        
        # Security: prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(FRONTEND_DIR)):
            self.send_error(403, 'Forbidden')
            return
        
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_error(404, 'File not found')
            return
        
        # Determine content type
        content_type = 'text/html'
        if file_path.endswith('.js'):
            content_type = 'application/javascript'
        elif file_path.endswith('.css'):
            content_type = 'text/css'
        elif file_path.endswith('.json'):
            content_type = 'application/json'
        elif file_path.endswith('.png'):
            content_type = 'image/png'
        elif file_path.endswith('.svg'):
            content_type = 'image/svg+xml'
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f'Error reading file: {str(e)}')
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.date_time_string()}] {format % args}")

def run_server():
    """Start the HTTP server"""
    server = HTTPServer(('0.0.0.0', PORT), TurretHandler)
    print(f"Turret control server starting on port {PORT}")
    print(f"Mode: {'Development' if DEV_MODE else 'Production'}")
    
    if DEV_MODE:
        print(f"\nDEV MODE:")
        print(f"  1. Start backend: python3 project/main.py")
        print(f"  2. Start frontend: cd frontend && npm run dev")
        print(f"  3. Access frontend at http://localhost:5173")
    else:
        print(f"Frontend directory: {FRONTEND_DIR}")
        print(f"Access at http://localhost:{PORT}")
    
    print(f"\nAPI Endpoints:")
    print(f"  POST /api/move - Set velocity (azimuth: -1/0/1, altitude: -1/0/1)")
    print(f"  POST /api/laser - Control laser")
    print(f"  POST /api/calibrate - Calibrate to zero")
    print(f"  GET  /api/position - Get current position (polled at 10Hz)")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == '__main__':
    run_server()

