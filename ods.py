#!/usr/bin/env python3
"""
Basic TMC2209 Stepper Motor Control for Raspberry Pi
NEMA 17 (17HS19-2004S1) - 1.8deg step angle (200 steps/rev)
"""

import RPi.GPIO as GPIO
import time

# Pin configuration
DIR_PIN = 2   # Direction pin
STEP_PIN = 3  # Step pin

# Motor configuration
STEPS_PER_REV = 200  # 1.8 degree step angle = 200 steps per revolution
STEP_DELAY = 0.002   # Delay for each pulse state (seconds) - adjust for speed

def setup():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)
    
    # Set initial direction (HIGH = clockwise, LOW = counter-clockwise)
    GPIO.output(DIR_PIN, GPIO.HIGH)
    GPIO.output(STEP_PIN, GPIO.LOW)
    print("GPIO initialized")

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
    """Run motor continuously at full speed"""
    print("Starting motor - Press Ctrl+C to stop")
    try:
        while True:
            step_motor(STEPS_PER_REV)
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

