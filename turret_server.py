#!/usr/bin/env python3
"""
ENME441 Laser Turret Backend Server
Web interface for controlling stepper motors and laser
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

# TODO: Import your stepper motor control code
# from stepper import StepperMotor

# TODO: Import RPi.GPIO if running on Pi
# import RPi.GPIO as GPIO

class TurretController:
    """Controls the laser turret hardware"""
    
    def __init__(self):
        self.laser_on = False
        self.azimuth = 0.0  # radians
        self.altitude = 0.0  # radians
        self.laser_timer = None
        
        # TODO: Initialize GPIO pins
        # GPIO.setmode(GPIO.BCM)
        # self.LASER_PIN = 17  # Example GPIO pin
        # GPIO.setup(self.LASER_PIN, GPIO.OUT)
        # GPIO.output(self.LASER_PIN, GPIO.LOW)
        
        # TODO: Initialize stepper motors through shift register
        # self.azimuth_motor = StepperMotor(...)
        # self.altitude_motor = StepperMotor(...)
        
        print("✅ Turret Controller initialized")
    
    def set_laser(self, state):
        """
        Turn laser on/off with 3-second auto-shutoff
        
        Args:
            state (bool): True for on, False for off
        """
        self.laser_on = state
        
        # TODO: Control actual GPIO pin
        # GPIO.output(self.LASER_PIN, GPIO.HIGH if state else GPIO.LOW)
        
        if state:
            print("🔴 LASER ON")
            
            # Cancel any existing timer
            if self.laser_timer:
                self.laser_timer.cancel()
            
            # Auto-shutoff after 3 seconds (competition rule)
            self.laser_timer = threading.Timer(3.0, self._auto_shutoff_laser)
            self.laser_timer.start()
        else:
            print("⚫ LASER OFF")
            if self.laser_timer:
                self.laser_timer.cancel()
                self.laser_timer = None
    
    def _auto_shutoff_laser(self):
        """Automatically turn off laser after 3 seconds"""
        print("⏰ Laser auto-shutoff (3 second limit)")
        self.set_laser(False)
    
    def set_angles(self, azimuth, altitude):
        """
        Set motor angles in radians
        
        Args:
            azimuth (float): Azimuth angle in radians
            altitude (float): Altitude angle in radians
        """
        self.azimuth = azimuth
        self.altitude = altitude
        
        print(f"🎯 Setting angles: azimuth={azimuth:.3f} rad, altitude={altitude:.3f} rad")
        
        # TODO: Convert radians to motor steps and move motors
        # azimuth_steps = self.radians_to_steps(azimuth)
        # altitude_steps = self.radians_to_steps(altitude)
        # self.azimuth_motor.move_to(azimuth_steps)
        # self.altitude_motor.move_to(altitude_steps)
    
    def calibrate(self):
        """Set current position as zero reference"""
        print("🔧 Calibrating - setting zero position")
        self.azimuth = 0.0
        self.altitude = 0.0
        
        # TODO: Reset motor step counters
        # self.azimuth_motor.reset()
        # self.altitude_motor.reset()
    
    def cleanup(self):
        """Clean up GPIO resources"""
        print("🧹 Cleaning up...")
        self.set_laser(False)
        # TODO: GPIO.cleanup()


class TurretHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for turret control API"""
    
    turret = None  # Will be set to TurretController instance
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests - serve static files"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Turret Control API</h1><p>Use POST to /api/* endpoints</p>')
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests - control turret"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        # CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        
        # Route handling
        if self.path == '/api/laser':
            # Control laser
            laser_state = data.get('laser', False)
            self.turret.set_laser(laser_state)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'success': True, 'laser': laser_state}
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/api/motors':
            # Control motors
            azimuth = data.get('azimuth', 0.0)
            altitude = data.get('altitude', 0.0)
            self.turret.set_angles(azimuth, altitude)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'success': True, 'azimuth': azimuth, 'altitude': altitude}
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/api/calibrate':
            # Calibrate (set zero)
            self.turret.calibrate()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'success': True}
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    """Start the turret control server"""
    HOST = '0.0.0.0'  # Listen on all interfaces
    PORT = 8080
    
    # Initialize turret controller
    turret = TurretController()
    TurretHTTPHandler.turret = turret
    
    # Start HTTP server
    server = HTTPServer((HOST, PORT), TurretHTTPHandler)
    
    print(f"🚀 Turret Control Server running on http://{HOST}:{PORT}")
    print(f"📡 Access from other devices at http://<pi-ip-address>:{PORT}")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⚠️  Server stopping...")
        turret.cleanup()
        server.shutdown()
        print("✅ Server stopped")


if __name__ == '__main__':
    main()

