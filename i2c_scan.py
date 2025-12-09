#!/usr/bin/env python3

import board
import busio

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Scan for devices
print("Scanning I2C bus...")
print("-" * 40)

found_devices = []
while not i2c.try_lock():
    pass

try:
    devices = i2c.scan()
    if devices:
        print(f"Found {len(devices)} device(s):")
        for device in devices:
            print(f"  0x{device:02X} (decimal: {device})")
            found_devices.append(device)
    else:
        print("No I2C devices found!")
        
finally:
    i2c.unlock()

print("-" * 40)

if not found_devices:
    print("\nTroubleshooting steps:")
    print("1. Check wiring:")
    print("   - SDA to GPIO2 (Pin 3)")
    print("   - SCL to GPIO3 (Pin 5)")
    print("   - VCC to 3.3V")
    print("   - GND to Ground")
    print("2. Make sure I2C is enabled: sudo raspi-config")
    print("3. Try running: i2cdetect -y 1")

