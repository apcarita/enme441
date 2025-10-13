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
MICROSTEPS = 16  # MS1/MS2 floating = 16 microsteps (TMC2209 default)
ACTUAL_STEPS_PER_REV = STEPS_PER_REV * MICROSTEPS  # 3200 steps per revolution

def setup():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)
    GPIO.setwarnings(False)
    
    GPIO.output(STEP_PIN, GPIO.LOW)
    
    print("TMC2209 Stepper Motor - Raspberry Pi Zero 2 W")
    print(f"Microstepping: {MICROSTEPS}x (MS1/MS2 floating)")
    print(f"Steps per revolution: {ACTUAL_STEPS_PER_REV}")
    print("Press Ctrl+C to stop\n")

def step_once():
    """Single step with proper timing"""
    GPIO.output(STEP_PIN, GPIO.HIGH)
    time.sleep(0.0001)  # 100 microseconds HIGH (longer pulse for TMC2209)
    GPIO.output(STEP_PIN, GPIO.LOW)
    time.sleep(0.0001)  # 100 microseconds LOW

def run_motor(speed_delay=0.001):
    """Run motor continuously
    
    Args:
        speed_delay: Additional delay between steps (lower = faster)
                     With 16x microstepping (3200 steps/rev):
                     0.001 = ~18 RPM (slow, smooth)
                     0.0005 = ~35 RPM
                     0.0002 = ~90 RPM
    """
    try:
        step_count = 0
        while True:
            step_once()
            step_count += 1
            
            if step_count % ACTUAL_STEPS_PER_REV == 0:
                print(f"Revolutions: {step_count // ACTUAL_STEPS_PER_REV}")
            
            if speed_delay > 0:
                time.sleep(speed_delay)
                
    except KeyboardInterrupt:
        print("\nStopping...")
        GPIO.cleanup()
        print("Motor stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control NEMA 17 stepper motor with TMC2209')
    parser.add_argument('--speed', type=float, default=0.001,
                        help='Speed delay in seconds (lower = faster). Default: 0.001. Range: 0.0001 to 0.01')
    parser.add_argument('--rpm', type=float,
                        help='Target RPM (overrides --speed)')
    parser.add_argument('--direction', type=int, choices=[0, 1], default=1,
                        help='Direction: 1=clockwise, 0=counter-clockwise. Default: 1')
    
    args = parser.parse_args()
    
    # Calculate speed_delay from RPM if provided
    if args.rpm:
        speed_delay = (60.0 / (args.rpm * ACTUAL_STEPS_PER_REV)) - 0.0002
        speed_delay = max(0, speed_delay)  # Ensure non-negative
        print(f"Target RPM: {args.rpm}")
    else:
        speed_delay = args.speed
    
    print(f"Speed delay: {speed_delay}s")
    print(f"Direction: {'Clockwise' if args.direction else 'Counter-clockwise'}")
    
    setup()
    GPIO.output(DIR_PIN, GPIO.HIGH if args.direction else GPIO.LOW)
    time.sleep(0.5)  # Give TMC2209 time to settle direction
    run_motor(speed_delay=speed_delay)
