import RPi.GPIO as GPIO
import time

class Shifter:
    def __init__(self, dataPin, latchPin, clockPin):
        self.dataPin = dataPin
        self.latchPin = latchPin
        self.clockPin = clockPin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dataPin, GPIO.OUT)
        GPIO.setup(self.latchPin, GPIO.OUT, initial=0)
        GPIO.setup(self.clockPin, GPIO.OUT, initial=0)

    def ping(self, p): 
        GPIO.output(p,1)
        time.sleep(0)
        GPIO.output(p,0)

    def shiftByte(self, b):
        for i in range(8):
            GPIO.output(self.dataPin, b & (1 << i))
            self.ping(self.clockPin)
        self.ping(self.latchPin)
        
    def clean(self):
        GPIO.cleanup()