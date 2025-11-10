import RPi.GPIO as GPIO
import time


GPIO.setmode(GPIO.BCM)

try:
    while True:
        GPIO.output(2, GPIO.LOW)
        time.sleep(100)
        GPIO.output(2, GPIO.HIGH)
except:
    GPIO.cleanup()