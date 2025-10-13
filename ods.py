#!/usr/bin/env python3
"""
TMC2209 Stepper Motor Control for Raspberry Pi Zero 2 W
NEMA 17 (17HS19-2004S1) - 1.8deg step angle (200 steps/rev)

Install: pip3 install RPi.GPIO
"""

import RPi.GPIO as GPIO
import time
import argparse

# Pin configuration
DIR_PIN = 2   # Direction pin (GPIO2)
STEP_PIN = 3  # Step pin (GPIO3)

# Motor configuration
STEPS_PER_REV = 200

def setup():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)
    GPIO.setwarnings(False)
    
    GPIO.output(STEP_PIN, GPIO.LOW)
    
    print("TMC2209 Stepper Motor - Raspberry Pi Zero 2 W")
    print("Press Ctrl+C to stop\n")

def step_once():
    """Single step with proper timing"""
    GPIO.output(STEP_PIN, GPIO.HIGH)
    time.sleep(0.000005)  # 5 microseconds HIGH
    GPIO.output(STEP_PIN, GPIO.LOW)
    time.sleep(0.000005)  # 5 microseconds LOW

def run_motor(speed_delay=0.001):
    """Run motor continuously
    
    Args:
        speed_delay: Additional delay between steps (lower = faster)
                     0.001 = ~1000 steps/sec
                     0.002 = ~500 steps/sec
    """
    try:
        step_count = 0
        while True:
            step_once()
            step_count += 1
            
            if step_count % STEPS_PER_REV == 0:
                print(f"Revolutions: {step_count // STEPS_PER_REV}")
            
            if speed_delay > 0:
                time.sleep(speed_delay)
                
    except KeyboardInterrupt:
        print("\nStopping...")
        GPIO.cleanup()
        print("Motor stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control NEMA 17 stepper motor with TMC2209')
    parser.add_argument('--speed', type=float, default=0.003,
                        help='Speed delay in seconds (lower = faster). Default: 0.003. Range: 0.0001 to 0.01')
    parser.add_argument('--rpm', type=float,
                        help='Target RPM (overrides --speed)')
    parser.add_argument('--direction', type=int, choices=[0, 1], default=1,
                        help='Direction: 1=clockwise, 0=counter-clockwise. Default: 1')
    
    args = parser.parse_args()
    
    # Calculate speed_delay from RPM if provided
    if args.rpm:
        speed_delay = (60.0 / (args.rpm * STEPS_PER_REV)) - 0.00001
        speed_delay = max(0, speed_delay)  # Ensure non-negative
        print(f"Target RPM: {args.rpm}")
    else:
        speed_delay = args.speed
    
    print(f"Speed delay: {speed_delay}s")
    print(f"Direction: {'Clockwise' if args.direction else 'Counter-clockwise'}")
    
    setup()
    GPIO.output(DIR_PIN, GPIO.HIGH if args.direction else GPIO.LOW)
    time.sleep(0.1)
    run_motor(speed_delay=speed_delay)
