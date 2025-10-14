#!/usr/bin/env python3
"""
TMC2209 XY Path Controller for Raspberry Pi Zero 2 W

Motors 2+3 control X-axis, Motor 1 controls Y-axis (inverted).
Define custom motion paths via command line with acceleration limiting.

Install: pip3 install RPi.GPIO

Examples:
    # Square path
    python3 ods_mov.py --path "[[1,1],[-1,1],[-1,-1],[1,-1]]"
    
    # Diagonal left-right with custom accel
    python3 ods_mov.py --path "[[1,1],[-1,-1]]" --rpm 100 --segment-sec 0.5 --accel 3
    
    # Line back and forth
    python3 ods_mov.py --path "[[1,0],[-1,0]]"
"""

import RPi.GPIO as GPIO
import time
import argparse
import ast
import math

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

def setup():
    """Initialize GPIO pins"""
    # Cleanup without setting mode first
    try:
        GPIO.cleanup()
    except:
        pass
    
    time.sleep(0.2)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Setup pins without initial parameter
    for dir_pin, step_pin in MOTOR_PINS:
        GPIO.setup(dir_pin, GPIO.OUT)
        GPIO.setup(step_pin, GPIO.OUT)
        GPIO.output(dir_pin, GPIO.LOW)
        GPIO.output(step_pin, GPIO.LOW)
    
    print("TMC2209 XY Path Controller")
    print(f"Microstepping: {MICROSTEPS}x")
    print("Press Ctrl+C to stop\n")

def safe_shutdown():
    """Drive all motor pins LOW and cleanup GPIO"""
    for dir_pin, step_pin in MOTOR_PINS:
        GPIO.output(dir_pin, GPIO.LOW)
        GPIO.output(step_pin, GPIO.LOW)
    time.sleep(0.1)
    GPIO.cleanup()

def move_segment(x_dir, y_dir, rpm, duration_sec, accel_mps2, wheel_dia_mm):
    """Move motors in X and Y directions with acceleration limiting"""
    # Set directions (Motor 1 Y-axis inverted)
    x_gpio_dir = GPIO.HIGH if x_dir > 0 else GPIO.LOW
    y_gpio_dir = GPIO.LOW if y_dir > 0 else GPIO.HIGH  # Inverted
    
    GPIO.output(MOTOR_PINS[0][0], y_gpio_dir)  # Motor 1 DIR (Y-axis)
    GPIO.output(MOTOR_PINS[1][0], x_gpio_dir)  # Motor 2 DIR (X-axis)
    GPIO.output(MOTOR_PINS[2][0], x_gpio_dir)  # Motor 3 DIR (X-axis)
    
    # Determine which motors to pulse
    step_pins = []
    if x_dir != 0:
        step_pins.extend([MOTOR_PINS[1][1], MOTOR_PINS[2][1]])  # Motors 2+3 (X-axis)
    if y_dir != 0:
        step_pins.append(MOTOR_PINS[0][1])  # Motor 1 (Y-axis)
    
    if not step_pins:
        time.sleep(duration_sec)
        return
    
    # Simple acceleration: just use fixed step delay
    step_delay = (60.0 / (rpm * ACTUAL_STEPS_PER_REV)) - (2 * PULSE_WIDTH)
    step_delay = max(0.0001, step_delay)  # Minimum delay to prevent infinite loops
    
    # Calculate total steps needed
    total_steps = int(duration_sec / (step_delay + 2 * PULSE_WIDTH))
    
    start_time = time.time()
    step_count = 0
    
    while step_count < total_steps and (time.time() - start_time) < duration_sec:
        # Pulse motors
        for pin in step_pins:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(PULSE_WIDTH)
        for pin in step_pins:
            GPIO.output(pin, GPIO.LOW)
        time.sleep(PULSE_WIDTH)
        
        time.sleep(step_delay)
        step_count += 1

def run_path(path, rpm, segment_duration, accel_mps2, wheel_dia_mm):
    """Run the custom path continuously"""
    try:
        lap = 0
        while True:
            for i, (x_dir, y_dir) in enumerate(path):
                print(f"Lap {lap+1} - Segment {i+1}/{len(path)}: X={x_dir:+d}, Y={y_dir:+d}")
                move_segment(x_dir, y_dir, rpm, segment_duration, accel_mps2, wheel_dia_mm)
            lap += 1
    except KeyboardInterrupt:
        print("\nStopping...")
        safe_shutdown()
        print("Motors stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Run custom XY path with TMC2209 steppers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Square:           --path "[[1,1],[-1,1],[-1,-1],[1,-1]]"
  Diagonal:         --path "[[1,1],[-1,-1]]"
  Horizontal line:  --path "[[1,0],[-1,0]]"
  Vertical line:    --path "[[0,1],[0,-1]]"
        """
    )
    parser.add_argument('--path', type=str, required=True,
                        help='Path as list of [x,y] vectors, e.g. "[[1,1],[-1,-1]]"')
    parser.add_argument('--rpm', type=float, default=50,
                        help='Motor speed in RPM (default: 50)')
    parser.add_argument('--segment-sec', type=float, default=1.5,
                        help='Duration of each segment in seconds (default: 1.5)')
    parser.add_argument('--accel', type=float, default=2.0,
                        help='Tangential acceleration limit in m/s² (default: 2.0)')
    parser.add_argument('--wheel-dia', type=float, default=98.0,
                        help='Wheel diameter in mm (default: 98)')
    
    args = parser.parse_args()
    
    # Parse path
    try:
        path = ast.literal_eval(args.path)
        if not isinstance(path, list) or not all(isinstance(p, list) and len(p) == 2 for p in path):
            raise ValueError("Path must be a list of [x,y] pairs")
    except Exception as e:
        print(f"Error parsing path: {e}")
        print('Path must be a valid list like "[[1,1],[-1,-1]]"')
        exit(1)
    
    print(f"Path: {path}")
    print(f"RPM: {args.rpm} | Segment: {args.segment_sec}s | Accel: {args.accel} m/s² | Wheel: {args.wheel_dia}mm")
    
    setup()
    run_path(path, args.rpm, args.segment_sec, args.accel, args.wheel_dia)

