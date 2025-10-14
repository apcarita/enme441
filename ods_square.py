#!/usr/bin/env python3
"""
TMC2209 XY Square Path Controller for Raspberry Pi Zero 2 W

Motors 2+3 control X-axis, Motor 1 controls Y-axis (inverted).
Repeats square path: [+X,+Y], [-X,+Y], [-X,-Y], [+X,-Y]

Install: pip3 install RPi.GPIO
"""

import RPi.GPIO as GPIO
import time
import argparse

# Pin configuration (DIR, STEP)
MOTOR_PINS = [
    (2, 3),     # Motor 1 (Y-axis, inverted)
    (4, 17),    # Motor 2 (X-axis)
    (27, 22),   # Motor 3 (X-axis)
]

# Motor configuration
STEPS_PER_REV = 200
MICROSTEPS = 16
ACTUAL_STEPS_PER_REV = STEPS_PER_REV * MICROSTEPS
PULSE_WIDTH = 0.0001

# Square path: [X_direction, Y_direction]
SQUARE_PATH = [
    [1, 1],   # +X, +Y
    [-1, 1],  # -X, +Y
    [-1, -1], # -X, -Y
    [1, -1],  # +X, -Y
]

def setup():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for dir_pin, step_pin in MOTOR_PINS:
        GPIO.setup(dir_pin, GPIO.OUT)
        GPIO.setup(step_pin, GPIO.OUT)
        GPIO.output(step_pin, GPIO.LOW)
        GPIO.output(dir_pin, GPIO.LOW)
    print("TMC2209 XY Square Path Controller")
    print(f"Microstepping: {MICROSTEPS}x")
    print("Press Ctrl+C to stop\n")

def safe_shutdown():
    """Drive all motor pins LOW and cleanup GPIO"""
    for dir_pin, step_pin in MOTOR_PINS:
        GPIO.output(dir_pin, GPIO.LOW)
        GPIO.output(step_pin, GPIO.LOW)
    time.sleep(0.1)
    GPIO.cleanup()

def move_segment(x_dir, y_dir, rpm, duration_sec):
    """Move motors in X and Y directions for specified duration"""
    # Set directions (Motor 1 Y-axis inverted)
    x_gpio_dir = GPIO.HIGH if x_dir > 0 else GPIO.LOW
    y_gpio_dir = GPIO.LOW if y_dir > 0 else GPIO.HIGH  # Inverted
    
    GPIO.output(MOTOR_PINS[0][0], y_gpio_dir)  # Motor 1 DIR (Y-axis)
    GPIO.output(MOTOR_PINS[1][0], x_gpio_dir)  # Motor 2 DIR (X-axis)
    GPIO.output(MOTOR_PINS[2][0], x_gpio_dir)  # Motor 3 DIR (X-axis)
    
    # Calculate step delay from RPM
    step_delay = (60.0 / (rpm * ACTUAL_STEPS_PER_REV)) - (2 * PULSE_WIDTH)
    step_delay = max(0, step_delay)
    
    # Determine which motors to pulse
    step_pins = []
    if x_dir != 0:
        step_pins.extend([MOTOR_PINS[1][1], MOTOR_PINS[2][1]])  # Motors 2+3 (X-axis)
    if y_dir != 0:
        step_pins.append(MOTOR_PINS[0][1])  # Motor 1 (Y-axis)
    
    if not step_pins:
        time.sleep(duration_sec)
        return
    
    # Run for duration
    start_time = time.time()
    while time.time() - start_time < duration_sec:
        for pin in step_pins:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(PULSE_WIDTH)
        for pin in step_pins:
            GPIO.output(pin, GPIO.LOW)
        time.sleep(PULSE_WIDTH)
        if step_delay > 0:
            time.sleep(step_delay)

def run_square_path(rpm, segment_duration):
    """Run the square path continuously"""
    try:
        lap = 0
        while True:
            for i, (x_dir, y_dir) in enumerate(SQUARE_PATH):
                print(f"Lap {lap+1} - Segment {i+1}/4: X={x_dir:+d}, Y={y_dir:+d}")
                move_segment(x_dir, y_dir, rpm, segment_duration)
            lap += 1
    except KeyboardInterrupt:
        print("\nStopping...")
        safe_shutdown()
        print("Motors stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run XY square path with TMC2209 steppers')
    parser.add_argument('--rpm', type=float, default=50,
                        help='Motor speed in RPM (default: 50)')
    parser.add_argument('--segment-sec', type=float, default=1.5,
                        help='Duration of each segment in seconds (default: 1.5)')
    
    args = parser.parse_args()
    
    print(f"RPM: {args.rpm} | Segment duration: {args.segment_sec}s")
    
    setup()
    run_square_path(args.rpm, args.segment_sec)

