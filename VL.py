#!/usr/bin/env python3

import time
import board
import adafruit_vl53l0x

# Initialize I2C and VL53L0X sensor
i2c = board.I2C()
vl53 = adafruit_vl53l0x.VL53L0X(i2c)

print("VL53L0X Distance Sensor")
print("Reading distance... (Ctrl+C to exit)")
print("-" * 40)

try:
    while True:
        distance_mm = vl53.range
        distance_cm = distance_mm / 10.0
        
        print(f"Distance: {distance_cm:6.1f} cm ({distance_mm:4.0f} mm)")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping measurements...")
finally:
    print("Sensor stopped.")

