#!/usr/bin/env python3
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
import multiprocessing
from stepper_class_shiftregister_multiprocessing import Stepper
from shifter import Shifter
import math
try:
    from RPi import GPIO
except (ImportError, RuntimeError):
    import mock_gpio as GPIO
    print("MOCK MODE - Running without hardware")
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
        
        # Initialize hardware with multiprocessing steppers
        self.shifter = Shifter(data=17, latch=27, clock=4)
        
        # Create multiprocessing locks (one per motor)
        self.motor_lock_alt = multiprocessing.Lock()
        self.motor_lock_az = multiprocessing.Lock()
        
        # Motors - order matters! First gets bits 0-3, second gets bits 4-7
        self.altitude_motor = Stepper(self.shifter, self.motor_lock_alt)  # QA-QD (bits 0-3)
        self.azimuth_motor = Stepper(self.shifter, self.motor_lock_az)    # QE-QH (bits 4-7)
        
        # Zero motors at start and turn off coils
        self.altitude_motor.zero()
        self.azimuth_motor.zero()
        self.shifter.shiftByte(0)  # motors off by default
        
        # Start continuous movement thread for manual control
        self.running = True
        self.movement_thread = threading.Thread(target=self._movement_loop, daemon=True)
        self.movement_thread.start()
    
    def set_velocity(self, azimuth_vel, altitude_vel):
        with self.lock:
            self.azimuth_velocity = max(-1, min(1, azimuth_vel))
            self.altitude_velocity = max(-1, min(1, altitude_vel))
    
    def motors_off(self):
        """Turn off all motor coils to prevent overheating"""
        # Wait for any pending movements to complete, then send 0 directly
        time.sleep(0.05)
        with Stepper.shifter_outputs.get_lock():
            Stepper.shifter_outputs.value = 0
            self.shifter.shiftByte(0)
    
    def _movement_loop(self):
        """Manual velocity control - queues small movements to multiprocessing steppers"""
        STEP_DEG = 1.15  # ~0.02 radians per movement chunk
        was_moving = False
        
        while self.running:
            with self.lock:
                az_vel = self.azimuth_velocity
                alt_vel = self.altitude_velocity
            
            if az_vel != 0 or alt_vel != 0:
                was_moving = True
                # Queue movements to the motor worker processes
                if az_vel != 0:
                    self.azimuth_motor.rotate(-STEP_DEG * az_vel)  # negate for direction
                if alt_vel != 0:
                    self.altitude_motor.rotate(STEP_DEG * alt_vel)
                
                # Update position tracking
                with self.lock:
                    self.azimuth = max(-3.14, min(3.14, self.azimuth + 0.02 * az_vel))
                    self.altitude = max(-1.57, min(1.57, self.altitude + 0.02 * alt_vel))
                
                # Wait for movement to complete before queuing more
                time.sleep(0.02)
            else:
                if was_moving:
                    # Just stopped - wait for queued movements to finish then turn off
                    time.sleep(0.15)  # wait for any queued commands to complete
                    self.motors_off()
                    was_moving = False
                time.sleep(0.05) 
    
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
        # Also zero the motor's internal tracking
        self.azimuth_motor.zero()
        self.altitude_motor.zero()
        print("Calibrated: current position set to zero")
    
    def move_to_position(self, target_azimuth, target_altitude):
        """Move to absolute position - queues full movement to multiprocessing steppers"""
        self.set_velocity(0, 0)
        time.sleep(0.1)  # let velocity loop settle
        
        with self.lock:
            current_az = self.azimuth
            current_alt = self.altitude
        
        # Calculate deltas
        delta_az = target_azimuth - current_az
        delta_alt = target_altitude - current_alt
        
        # Convert to degrees for motors
        delta_az_deg = -math.degrees(delta_az)  # negate for direction
        delta_alt_deg = math.degrees(delta_alt)
        
        # Queue rotations to worker processes (they execute in parallel)
        if abs(delta_az_deg) > 0.1:
            self.azimuth_motor.rotate(delta_az_deg)
        if abs(delta_alt_deg) > 0.1:
            self.altitude_motor.rotate(delta_alt_deg)
        
        # Wait for movement to complete
        # steps = degrees * (4096 steps/rev) / 360 deg/rev
        # time = steps * 1200us delay
        steps_az = abs(delta_az_deg) * 4096 / 360
        steps_alt = abs(delta_alt_deg) * 4096 / 360
        max_steps = max(steps_az, steps_alt)
        wait_time = max_steps * 0.0012 + 0.3  # step_delay * steps + buffer
        time.sleep(wait_time)
        
        # Update position tracking
        with self.lock:
            self.azimuth = target_azimuth
            self.altitude = target_altitude
        
        # Turn off coils to prevent overheating
        self.motors_off()
    
    def shutdown(self):
        print("Shutting down turret...")
        self.running = False
        self.set_velocity(0, 0)
        self.set_laser(False)
        
        # Turn off motors
        self.motors_off()
        time.sleep(0.1)
        
        # Terminate motor worker processes
        if hasattr(self.azimuth_motor, 'worker'):
            self.azimuth_motor.worker.terminate()
        if hasattr(self.altitude_motor, 'worker'):
            self.altitude_motor.worker.terminate()
        
        # Clear shift register directly (workers are terminated)
        self.shifter.shiftByte(0)
        
        # Set GPIO pins low before cleanup
        GPIO.output(LASER_PIN, GPIO.LOW)
        time.sleep(0.1)
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
    global auto_target_running, position_data
    auto_target_running = True
    
    try:
        # Fetch position data
        print(f"Fetching JSON from {JSON_URL}")
        position_data = fetchJson(JSON_URL)
            
        my_pos = getMePos(position_data, TEAM_NUMBER)
        print(f"Current position: r={my_pos[0]:.1f}cm, theta={my_pos[1]:.3f}rad")
            
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

