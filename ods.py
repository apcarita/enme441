"""
TMC2209 Stepper Motor Control for Raspberry Pi
NEMA 17 (17HS19-2004S1) - 1.8deg step angle (200 steps/rev)

Install: pip3 install TMC-2209-Raspberry-Pi
"""

from TMC_2209.TMC_2209_StepperDriver import TMC_2209
import time

# Pin configuration
DIR_PIN = 2   # Direction pin (GPIO2)
STEP_PIN = 3  # Step pin (GPIO3)
EN_PIN = -1   # Enable pin is wired to ground

# Motor configuration
MOTOR_CURRENT_MA = 1200  # 1.2A (60% of 2A max for safety)
STEPS_PER_REV = 200      # 1.8 degree step angle

def main():
    """Main function to run motor continuously"""
    
    # Initialize TMC2209
    print("Initializing TMC2209...")
    tmc = TMC_2209(DIR_PIN, STEP_PIN, EN_PIN)
    
    # Configure motor
    tmc.set_motor_current(MOTOR_CURRENT_MA)
    tmc.set_direction_reg(True)  # True = clockwise
    tmc.set_interpolation(True)  # Smooth motion
    tmc.set_spreadcycle(False)   # Use StealthChop for quiet operation
    
    print(f"Motor: NEMA 17 with TMC2209")
    print(f"Current: {MOTOR_CURRENT_MA}mA")
    print(f"Starting motor - Press Ctrl+C to stop\n")
    
    try:
        # Run motor continuously at constant speed
        while True:
            # Move one revolution
            tmc.run_to_position_steps(STEPS_PER_REV)
            
    except KeyboardInterrupt:
        print("\nStopping motor...")
    finally:
        tmc.stop()
        print("Motor stopped")

if __name__ == "__main__":
    main()
