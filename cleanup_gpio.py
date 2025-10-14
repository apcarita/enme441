#!/usr/bin/env python3
"""
Manual GPIO cleanup script
Run this if GPIO pins get stuck busy
"""

import RPi.GPIO as GPIO
import time

def cleanup_gpio():
    """Force cleanup of all GPIO pins"""
    try:
        GPIO.cleanup()
        print("GPIO cleanup successful")
    except Exception as e:
        print(f"GPIO cleanup failed: {e}")
    
    # Try multiple times
    for i in range(3):
        try:
            GPIO.cleanup()
            time.sleep(0.1)
        except:
            pass
    
    print("GPIO cleanup completed")

if __name__ == "__main__":
    cleanup_gpio()
