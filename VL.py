#!/usr/bin/env python3

import time
import board
import adafruit_vl53l1x

# Initialize I2C bus
i2c = board.I2C()

# Initialize VL53L1X sensor
vl53 = adafruit_vl53l1x.VL53L1X(i2c)

# Start ranging
vl53.start_ranging()

print("VL53L1X Distance Sensor")
print("Reading distance... (Ctrl+C to exit)")
print("-" * 40)

try:
    while True:
        # Check if data is ready
        if vl53.data_ready:
            distance = vl53.distance
            
            # Print distance in cm
            if distance is not None:
                print(f"Distance: {distance:6.1f} cm")
            else:
                print("Distance: Out of range")
            
            # Clear interrupt
            vl53.clear_interrupt()
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping measurements...")
finally:
    # Stop ranging
    vl53.stop_ranging()
    print("Sensor stopped.")

