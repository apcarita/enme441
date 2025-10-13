#!/usr/bin/env python3
"""
TMC2209 Motor Diagnostics - Test different speeds and check wiring
"""

import RPi.GPIO as GPIO
import time

DIR_PIN = 2
STEP_PIN = 3

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)
    GPIO.setwarnings(False)
    GPIO.output(STEP_PIN, GPIO.LOW)
    GPIO.output(DIR_PIN, GPIO.HIGH)
    time.sleep(0.5)

def step_once():
    GPIO.output(STEP_PIN, GPIO.HIGH)
    time.sleep(0.0002)
    GPIO.output(STEP_PIN, GPIO.LOW)
    time.sleep(0.0002)

def test_very_slow():
    """Test at very slow speed - should be smooth"""
    print("\n=== TEST 1: VERY SLOW (10 RPM) ===")
    print("Motor should turn VERY slowly and SMOOTHLY")
    print("If shaking: wiring issue or power problem")
    print("Running for 5 seconds...\n")
    
    delay = 0.003  # Very slow
    start = time.time()
    step_count = 0
    
    while time.time() - start < 5:
        step_once()
        time.sleep(delay)
        step_count += 1
    
    print(f"Completed {step_count} steps")
    time.sleep(1)

def test_medium():
    """Test at medium speed"""
    print("\n=== TEST 2: MEDIUM SPEED (30 RPM) ===")
    print("Should turn smoothly, faster than test 1")
    print("Running for 5 seconds...\n")
    
    delay = 0.001
    start = time.time()
    step_count = 0
    
    while time.time() - start < 5:
        step_once()
        time.sleep(delay)
        step_count += 1
    
    print(f"Completed {step_count} steps")
    time.sleep(1)

def test_fast():
    """Test at faster speed"""
    print("\n=== TEST 3: FASTER (60 RPM) ===")
    print("Should turn faster, may start to shake if not enough current")
    print("Running for 5 seconds...\n")
    
    delay = 0.0005
    start = time.time()
    step_count = 0
    
    while time.time() - start < 5:
        step_once()
        time.sleep(delay)
        step_count += 1
    
    print(f"Completed {step_count} steps")
    time.sleep(1)

def test_direction():
    """Test direction change"""
    print("\n=== TEST 4: DIRECTION TEST ===")
    print("Motor will rotate CW, then CCW")
    
    # Clockwise
    print("Clockwise for 3 seconds...")
    GPIO.output(DIR_PIN, GPIO.HIGH)
    time.sleep(0.5)
    
    start = time.time()
    while time.time() - start < 3:
        step_once()
        time.sleep(0.001)
    
    time.sleep(0.5)
    
    # Counter-clockwise
    print("Counter-clockwise for 3 seconds...")
    GPIO.output(DIR_PIN, GPIO.LOW)
    time.sleep(0.5)
    
    start = time.time()
    while time.time() - start < 3:
        step_once()
        time.sleep(0.001)
    
    print("Direction test complete")

def main():
    print("=" * 50)
    print("TMC2209 MOTOR DIAGNOSTIC TEST")
    print("=" * 50)
    print("\nHardware checklist:")
    print("✓ DIR -> GPIO2, STEP -> GPIO3")
    print("✓ EN -> GND (or leave floating)")
    print("✓ VDD -> 3.3V, GND -> Pi GND")
    print("✓ VM -> 12V+, Motor GND -> 12V-")
    print("✓ Motor: Black->2A, Green->1A, Red->2B, Blue->1B")
    print("\nPress Ctrl+C at any time to stop\n")
    
    input("Press Enter to start tests...")
    
    setup()
    
    try:
        test_very_slow()
        test_medium()
        test_fast()
        test_direction()
        
        print("\n" + "=" * 50)
        print("DIAGNOSTICS:")
        print("=" * 50)
        print("\nIf motor shakes at SLOW speed:")
        print("  → Check motor coil wiring (swap A coil or B coil)")
        print("  → Increase Vref (turn potentiometer clockwise)")
        print("  → Verify 12V power supply is adequate (2A+)")
        print("\nIf motor runs smooth at slow but shakes at fast:")
        print("  → This is normal - try intermediate speeds")
        print("  → Increase motor current (Vref)")
        print("\nIf motor doesn't move at all:")
        print("  → Check EN pin (should be GND or floating)")
        print("  → Verify power supply voltage")
        print("\n" + "=" * 50)
        
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up")

if __name__ == "__main__":
    main()

