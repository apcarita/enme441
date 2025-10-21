import time
from Shifter import Shifter
import random as r
import RPi.GPIO as GPIO

shifts = Shifter(2,3,4)

pattern = 0b00100000

try:
    while 1:

        dir = r.randint(0,1) -1
        print(f"moving {dir}")

        if(dir):
            pattern >> 1
        else:
            pattern << 1
        
        shifts.shiftByte(pattern)
        time.sleep(0.5)


except:
    shifts.clean()
    GPIO.cleanup()