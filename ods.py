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
MICROSTEPS = 1        # Set to 1 since MS1/MS2 floating - we'll just send more pulses
PULSE_WIDTH = 0.00001 # Pulse HIGH time (10 microseconds minimum for TMC2208)
STEP_DELAY = 0.002    # Delay between steps (slower for testing)

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
    print(f"Steps per rev: {STEPS_PER_REV * MICROSTEPS}")
    print(f"Speed: {1.0/(STEP_DELAY + PULSE_WIDTH):.1f} steps/sec")
    time.sleep(0.2)  # Let pins settle and direction setup

def step_motor(steps, delay=STEP_DELAY):
    """
    Move motor by specified number of steps
    
    Args:
        steps: Number of steps to move
        delay: Delay between steps in seconds (lower = faster)
    """
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(PULSE_WIDTH)  # Short pulse
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)  # Longer delay before next step

def run_continuous():
    """Run motor continuously at constant speed"""
    print("\nStarting motor - Press Ctrl+C to stop")
    print("Motor should be turning now...\n")
    
    try:
        step_count = 0
        while True:
            step_motor(STEPS_PER_REV * MICROSTEPS)
            step_count += STEPS_PER_REV * MICROSTEPS
            if step_count % 1000 == 0:
                print(f"Steps completed: {step_count}")
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

