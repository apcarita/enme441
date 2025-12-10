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
try:
    from RPi import GPIO
except (ImportError, RuntimeError):
    import mock_gpio as GPIO
    print("⚠️  MOCK MODE - Running without hardware")
from command import *
import signal
import sys

PORT = 8080
LASER_PIN = 22
TEAM_NUMBER = '13' 
JSON_URL = 'http://192.168.1.254:8000/positions.json'

# Position data - load local file on startup for testing
position_data = None
try:
    fallback_path = os.path.join(os.path.dirname(__file__), '../frontend/public/positions.json')
    if os.path.exists(fallback_path):
        import json as json_module
        with open(fallback_path, 'r') as f:
            position_data = json_module.load(f)
        print(f"Loaded local positions.json for testing")
except Exception as e:
    print(f"Could not load local positions.json: {e}")

# Setup laser pin
GPIO.setup(LASER_PIN, GPIO.OUT)
GPIO.output(LASER_PIN, GPIO.LOW)

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
        self.shifter = Shifter(data=17, latch=27, clock=4)
        self.azimuth_motor = Stepper(self.shifter, bit_offset=4)  # QE-QH
        self.altitude_motor = Stepper(self.shifter, bit_offset=0)  # QA-QD
        
        # Start continuous movement thread
        self.running = True
        self.movement_thread = threading.Thread(target=self._movement_loop, daemon=True)
        self.movement_thread.start()
    
    def set_velocity(self, azimuth_vel, altitude_vel):
        with self.lock:
            self.azimuth_velocity = max(-1, min(1, azimuth_vel))
            self.altitude_velocity = max(-1, min(1, altitude_vel))
    
    def _movement_loop(self):
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
                az_deg = -math.degrees(new_az - self.azimuth)  # Negate for correct direction
                alt_deg = math.degrees(new_alt - self.altitude)
                
                if az_deg != 0 or alt_deg != 0:
                    interleave_rotate(
                        [self.azimuth_motor, self.altitude_motor],
                        [az_deg, alt_deg]
                    )
                    
                    with self.lock:
                        self.azimuth = new_az
                        self.altitude = new_alt
            else:
                # Turn off motors when not moving
                self.azimuth_motor.off()
                self.altitude_motor.off()
            
            time.sleep(0.01)  #100Hz 
    
    def get_position(self):
        with self.lock:
            return {
                'azimuth': self.azimuth,
                'altitude': self.altitude,
                'laser': self.laser_on
            }
    
    def set_laser(self, state):
        with self.lock:
            self.laser_on = state
            GPIO.output(LASER_PIN, GPIO.HIGH if state else GPIO.LOW)
    
    def calibrate(self):
        """Set current position as zero reference (doesn't move turret)"""
        with self.lock:
            self.azimuth = 0.0
            self.altitude = 0.0
        print("Calibrated: current position set to zero")
    
    def move_to_position(self, target_azimuth, target_altitude):
        """Move to absolute position (blocking call)"""
        # Stop any velocity-based movement
        self.set_velocity(0, 0)
        
        with self.lock:
            current_az = self.azimuth
            current_alt = self.altitude
        
        # Calculate movement needed
        delta_az = target_azimuth - current_az
        delta_alt = target_altitude - current_alt
        
        # Convert to degrees
        az_deg = -math.degrees(delta_az)  # Negate for correct direction
        alt_deg = math.degrees(delta_alt)
        
        # Execute movement
        if az_deg != 0 or alt_deg != 0:
            interleave_rotate(
                [self.azimuth_motor, self.altitude_motor],
                [az_deg, alt_deg]
            )
            
            # Wait for last step to complete before de-energizing
            time.sleep(Stepper.delay * 2)
            
            self.azimuth_motor.off()
            self.altitude_motor.off()
            
            with self.lock:
                self.azimuth = target_azimuth
                self.altitude = target_altitude
    
    def shutdown(self):
        print("Shutting down turret...")
        self.running = False
        self.set_velocity(0, 0)
        self.set_laser(False)
        time.sleep(0.1)
        self.azimuth_motor.off()
        self.altitude_motor.off()
        # Set GPIO pins low before cleanup
        GPIO.output(LASER_PIN, GPIO.LOW)
        GPIO.cleanup()
        print("Turret shutdown complete")

# Global state
turret_state = TurretState()
auto_target_running = False
server_instance = None

def signal_handler(sig, frame):
    """Handle shutdown signals (SIGINT, SIGTERM)"""
    print(f"\nReceived signal {sig}, shutting down...")
    if turret_state:
        turret_state.shutdown()
    if server_instance:
        server_instance.shutdown()
    sys.exit(0)

def auto_target_sequence():
    global auto_target_running
    auto_target_running = True
    
    try:
        # Fetch position data
        print(f"Fetching JSON from {JSON_URL}")
        position_data = fetchJson(JSON_URL)
            
        my_pos = getMePos(position_data, TEAM_NUMBER)
        print(f"✓ current position: r={my_pos[0]:.1f}cm, theta={my_pos[1]:.3f}rad")
            
        enemies = getEnemyPos(position_data, TEAM_NUMBER)
        globes = getGlobes(position_data)
        all_targets = globes + enemies 
            
        print(f"{len(enemies)} enemy turrets and {len(globes)} globe found")
        print(f"  Total targets: {len(all_targets)}")
            
        for i, target in enumerate(all_targets):
            if not auto_target_running:
                print("\nAuto-targeting STOPPED by user")
                break
                
            target_type = "Globe" if i < len(globes) else "Enemy"
            print(f"\n[{i+1}/{len(all_targets)}] Targeting {target_type}...")
            print(f"  Position: r={target[0]:.1f}cm, theta={target[1]:.3f}rad, z={target[2]:.1f}cm")
                
            azimuth, altitude = getFiringAngles(my_pos, target)
            print(f"  azimuth={azimuth:.3f}rad, altitude={altitude:.3f}rad")
                    
            turret_state.move_to_position(azimuth, altitude)
                
            time.sleep(0.5)
            
            if not auto_target_running:
                break
                
            print(f"  LASER ON")
            turret_state.set_laser(True)
            time.sleep(3.0)
            turret_state.set_laser(False)
            print(f"  Laser off")
            time.sleep(0.5)
            
        print("Targeting complete" if auto_target_running else "Targeting stopped")
    finally:
        auto_target_running = False
        turret_state.set_laser(False)
        
   

class TurretHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        
        # API endpoints - send ALL data (turret + enemies + globes)
        if parsed.path == '/api/position':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            turret_pos = turret_state.get_position()
            response = {'turret': turret_pos, 'enemies': [], 'globes': [], 'my_position': None}
            
            global position_data
            if position_data:
                try:
                    my_pos = getMePos(position_data, TEAM_NUMBER)
                    # Convert to Cartesian (Three.js uses Y as up, XZ as ground plane)
                    my_x = my_pos[0] * math.cos(my_pos[1])
                    my_z = my_pos[0] * math.sin(my_pos[1])
                    response['my_position'] = {'x': my_x, 'z': my_z, 'angle_to_origin': math.atan2(-my_z, -my_x)}
                    
                    response['enemies'] = [
                        {'x': e[0] * math.cos(e[1]), 'z': e[0] * math.sin(e[1]), 'y': e[2]}
                        for e in getEnemyPos(position_data, TEAM_NUMBER)
                    ]
                    response['globes'] = [
                        {'x': g[0] * math.cos(g[1]), 'z': g[0] * math.sin(g[1]), 'y': g[2]}
                        for g in getGlobes(position_data)
                    ]
                except Exception as e:
                    print(f"Error parsing positions: {e}")
            
            self.wfile.write(json.dumps(response).encode())
            return
        
        self.send_error(404, 'Not found')
    
    def do_POST(self):
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
            azimuth_vel = -float(data.get('azimuth', 0))  # Invert for correct direction
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
            turret_state.set_laser(bool(data.get('laser', False)))
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            return
        
        # Calibration
        elif parsed.path == '/api/calibrate':
            turret_state.calibrate()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            return
        
        # Auto-targeting sequence
        elif parsed.path == '/api/auto-target':
            threading.Thread(target=auto_target_sequence, daemon=True).start()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            return
        
        # Stop auto-targeting
        elif parsed.path == '/api/stop-target':
            global auto_target_running
            auto_target_running = False
            turret_state.set_velocity(0, 0)
            turret_state.set_laser(False)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            return
        
        # Fetch JSON - manual refresh
        elif parsed.path == '/api/fetch-json':
            global position_data
            try:
                position_data = fetchJson(JSON_URL, save_local=False)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode())
            except Exception as e:
                self.send_error(500, f'Failed to fetch: {str(e)}')
            return
        
        self.send_error(404, 'Endpoint not found')
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format - suppress position polling spam"""
        message = format % args
        # Don't log position polling requests
        if '/api/position' not in message:
            print(f"[{self.date_time_string()}] {message}")

def run_server():
    """Start the HTTP server"""
    global server_instance
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server = HTTPServer(('0.0.0.0', PORT), TurretHandler)
    server_instance = server
    
    print(f"API Server: http://localhost:{PORT}")
    print(f"Frontend: http://localhost:5173 (run: cd frontend && npm run dev)")
    
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass  # Handled by signal_handler
    finally:
        # Cleanup in case signal handler didn't run
        if turret_state:
            try:
                turret_state.shutdown()
            except Exception as e:
                print(f"Error during turret shutdown: {e}")

if __name__ == '__main__':
    run_server()

