#!/usr/bin/env python3
"""
TMC2209 control using RpiMotorLib (STEP/DIR) on Raspberry Pi Zero 2 W

Install dependencies:
  pip3 install RpiMotorLib RPi.GPIO

Wiring (board from your photo):
  VM  -> 12V+
  GND -> 12V-
  VIO -> 3.3V (Pi)
  GND -> GND (Pi)
  STEP -> GPIO pin (default 17)
  DIR  -> GPIO pin (default 27)
  EN   -> GND or floating
  MS1/MS2 -> GND for full step during bring-up (recommended), else floating = 16x

Run examples:
  python3 ods_lib.py --rpm 30
  python3 ods_lib.py --rpm 60 --direction 0
  python3 ods_lib.py --rpm 120 --microsteps 16
"""

import argparse
import time
from RpiMotorLib import RpiMotorLib
import RPi.GPIO as GPIO


def rpm_to_delay(rpm: float, steps_per_rev: int) -> float:
    # steps per second = rpm * steps_rev / 60
    sps = max(1.0, (rpm * steps_per_rev) / 60.0)
    # RpiMotorLib expects step delay (seconds between edges)
    return 1.0 / sps


def main():
    parser = argparse.ArgumentParser(description="Drive TMC2209 via RpiMotorLib")
    parser.add_argument("--step", type=int, default=17, help="GPIO pin for STEP (BCM). Default: 17")
    parser.add_argument("--dir", type=int, default=27, help="GPIO pin for DIR (BCM). Default: 27")
    parser.add_argument("--rpm", type=float, default=30.0, help="Target RPM. Default: 30")
    parser.add_argument("--direction", type=int, choices=[0, 1], default=1, help="1=CW, 0=CCW. Default: 1")
    parser.add_argument("--microsteps", type=int, default=1, help="Microsteps (1,2,4,8,16). Match MS1/MS2 wiring. Default: 1")
    parser.add_argument("--revs", type=float, default=5.0, help="How many revolutions to move. Default: 5")
    args = parser.parse_args()

    full_steps = 200
    steps_per_rev = full_steps * max(1, args.microsteps)
    step_delay = rpm_to_delay(args.rpm, steps_per_rev)

    # RpiMotorLib stepper instance (A4988-like, works for TMC2209 STEP/DIR)
    stepper = RpiMotorLib.A4988Nema(
        direction_pin=args.dir,
        step_pin=args.step,
        mode_pins=(None, None, None),  # We control MS1/MS2 in hardware wiring, not via GPIO
        motor_type="NEMA"
    )

    # Set DIR line explicitly before motion
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(args.dir, GPIO.OUT)
    GPIO.output(args.dir, GPIO.HIGH if args.direction == 1 else GPIO.LOW)
    time.sleep(0.2)

    total_steps = int(steps_per_rev * args.revs)
    print(f"DIR pin={args.dir}, STEP pin={args.step}")
    print(f"RPM={args.rpm}, microsteps={args.microsteps}, steps/rev={steps_per_rev}")
    print(f"Step delay≈{step_delay:.6f}s, total steps={total_steps}")

    # Move the requested number of steps at the computed speed
    # RpiMotorLib: .motor_go(clockwise, steptype, steps, stepdelay, verbose, initdelay)
    clockwise = True if args.direction == 1 else False
    stepper.motor_go(clockwise, "Full", total_steps, step_delay, False, 0.05)

    GPIO.cleanup()
    print("Done.")


if __name__ == "__main__":
    main()
