#!/usr/bin/env python3

import time
import board

# Try VL53L1X first, then VL53L0X
sensor_type = None
vl53 = None

try:
    import adafruit_vl53l1x
    i2c = board.I2C()
    vl53 = adafruit_vl53l1x.VL53L1X(i2c)
    vl53.start_ranging()
    sensor_type = "VL53L1X"
    print("VL53L1X sensor detected")
except (ImportError, ValueError) as e:
    try:
        import adafruit_vl53l0x
        i2c = board.I2C()
        vl53 = adafruit_vl53l0x.VL53L0X(i2c)
        sensor_type = "VL53L0X"
        print("VL53L0X sensor detected")
    except (ImportError, ValueError) as e:
        print(f"Error: Could not initialize sensor - {e}")
        print("\nRun 'python3 i2c_scan.py' to check if sensor is detected")
        exit(1)

print(f"{sensor_type} Distance Sensor")
print("Reading distance... (Ctrl+C to exit)")
print("-" * 40)

try:
    while True:
        if sensor_type == "VL53L1X":
            if vl53.data_ready:
                distance = vl53.distance
                if distance is not None:
                    print(f"Distance: {distance:6.1f} cm")
                else:
                    print("Distance: Out of range")
                vl53.clear_interrupt()
        else:  # VL53L0X
            distance = vl53.range
            print(f"Distance: {distance:6.1f} mm")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping measurements...")
finally:
    if sensor_type == "VL53L1X":
        vl53.stop_ranging()
    print("Sensor stopped.")

