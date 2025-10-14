#!/usr/bin/env python3
"""
TMC2209 Stepper Motor Control for Raspberry Pi Zero 2 W
Drive THREE steppers via STEP/DIR (no UART).

Pairs (DIR, STEP):
- Motor 1: (2, 3)
- Motor 2: (4, 17)
- Motor 3: (27, 22)

Notes:
- MS1/MS2 floating typically = 16× microstepping
- For bring-up, grounding MS1+MS2 (1×) can add torque
- Motor wiring: Black->2A, Green->1A, Red->2B, Blue->1B
- Provide VM=12V and Pi 3.3V to VIO; grounds common

Install: pip3 install RPi.GPIO
"""

import RPi.GPIO as GPIO
import time
import argparse

# Pin configuration (DIR, STEP) for three drivers
MOTOR_PINS = [
    (2, 3),     # Motor 1
    (4, 17),    # Motor 2
    (27, 22),   # Motor 3
]

# Motor configuration
STEPS_PER_REV = 200
MICROSTEPS = 16  # If MS1/MS2 floating. Set to 1 if tied to GND.
ACTUAL_STEPS_PER_REV = STEPS_PER_REV * MICROSTEPS
PULSE_WIDTH = 0.0001  # 100 µs HIGH/LOW

def setup():
    """Initialize GPIO pins for all motors"""
    try:
        GPIO.cleanup()
    except:
        pass
    
    time.sleep(0.2)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for dir_pin, step_pin in MOTOR_PINS:
        GPIO.setup(dir_pin, GPIO.OUT)
        GPIO.setup(step_pin, GPIO.OUT)
        GPIO.output(dir_pin, GPIO.LOW)
        GPIO.output(step_pin, GPIO.LOW)

    print("TMC2209 - Triple motor control (Pi Zero 2 W)")
    print(f"Microstepping: {MICROSTEPS}x, steps/rev: {ACTUAL_STEPS_PER_REV}")
    print("Motors: (DIR,STEP) -> (2,3), (4,17), (27,22)")
    print("Press Ctrl+C to stop\n")

def pulse_all(step_pins):
    """Issue one step pulse to all provided STEP pins in sync"""
    for pin in step_pins:
        GPIO.output(pin, GPIO.HIGH)
    time.sleep(PULSE_WIDTH)
    for pin in step_pins:
        GPIO.output(pin, GPIO.LOW)
    time.sleep(PULSE_WIDTH)

def safe_shutdown():
    """Drive all motor pins LOW and cleanup GPIO"""
    for dir_pin, step_pin in MOTOR_PINS:
        GPIO.output(dir_pin, GPIO.LOW)
        GPIO.output(step_pin, GPIO.LOW)
    time.sleep(0.1)
    GPIO.cleanup()

def run_motors(speed_delay=0.001, direction=1):
    """Run all motors continuously at the same speed and direction"""
    # Set directions
    for dir_pin, _ in MOTOR_PINS:
        GPIO.output(dir_pin, GPIO.HIGH if direction else GPIO.LOW)
    time.sleep(0.3)

    step_pins = [step for _, step in MOTOR_PINS]

    try:
        step_count = 0
        while True:
            pulse_all(step_pins)
            step_count += 1
            if step_count % ACTUAL_STEPS_PER_REV == 0:
                print(f"Revolutions: {step_count // ACTUAL_STEPS_PER_REV}")
            if speed_delay > 0:
                time.sleep(speed_delay)
    except KeyboardInterrupt:
        print("\nStopping...")
        safe_shutdown()
        print("Motors stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control THREE NEMA 17 steppers with TMC2209 (STEP/DIR)')
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
    
    print(f"Speed delay: {speed_delay}s | Direction: {'CW' if args.direction else 'CCW'}")

    setup()
    run_motors(speed_delay=speed_delay, direction=args.direction)
