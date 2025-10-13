#!/usr/bin/env python3
"""
TMC2208 Stepper Motor Control for Raspberry Pi
NEMA 17 (17HS19-2004S1) - 1.8deg step angle (200 steps/rev)

Install: pip3 install RPi.GPIO
"""

import RPi.GPIO as GPIO
import time

# Pin configuration
DIR_PIN = 2   # Direction pin (GPIO2)
STEP_PIN = 3  # Step pin (GPIO3)

# Motor configuration
STEPS_PER_REV = 200   # 1.8 degree step angle = 200 full steps per revolution
MICROSTEPS = 8        # TMC2208 default is often 8 or 16 microsteps
STEP_DELAY = 0.001    # Delay between pulses (seconds)

def setup():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)
    
    # Set initial direction (HIGH = clockwise, LOW = counter-clockwise)
    GPIO.output(DIR_PIN, GPIO.HIGH)
    GPIO.output(STEP_PIN, GPIO.LOW)
    
    print("GPIO initialized")
    print(f"Motor: NEMA 17 with TMC2208")
    print(f"Steps per rev: {STEPS_PER_REV * MICROSTEPS} (with {MICROSTEPS}x microstepping)")
    time.sleep(0.1)  # Let pins settle

def step_motor(steps, delay=STEP_DELAY):
    """
    Move motor by specified number of steps
    
    Args:
        steps: Number of steps to move
        delay: Delay between pulse states in seconds (lower = faster)
    """
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)

def run_continuous():
    """Run motor continuously"""
    print("Starting motor - Press Ctrl+C to stop")
    print("If motor just buzzes, try adjusting STEP_DELAY or MICROSTEPS in the code\n")
    
    try:
        rev_count = 0
        while True:
            # Account for microstepping
            step_motor(STEPS_PER_REV * MICROSTEPS)
            rev_count += 1
            if rev_count % 10 == 0:
                print(f"Completed {rev_count} revolutions")
    except KeyboardInterrupt:
        print("\nStopping motor...")
        cleanup()

def cleanup():
    """Clean up GPIO on exit"""
    GPIO.cleanup()
    print("GPIO cleaned up")

if __name__ == "__main__":
    setup()
    run_continuous()

