from Shifter import Shifter 
from Bug import Bug
import RPi.GPIO as GPIO
import time

shifts = Shifter(2, 3, 4)
bug = Bug(shifts)

s = [17, 27, 22]
GPIO.setmode(GPIO.BCM)

def on(c):
    if GPIO.input(s[0]):
        bug.start()
    else:
        bug.stop()

def toggleWrap(c):
    bug.isWrapOn = not bug.isWrapOn

def threeSpeed(c):
    if GPIO.input(s[2]):
        bug.timestep = bug.timestep/3
    else:
        bug.timestep = bug.timestep*3
    


GPIO.setup(s[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(s[0], GPIO.BOTH, callback=on, bouncetime=600)

GPIO.setup(s[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(s[1], GPIO.BOTH, callback=toggleWrap, bouncetime=600)

GPIO.setup(s[2], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(s[2], GPIO.BOTH, callback=threeSpeed, bouncetime=600)

try:
    while(1):
        time.sleep(0)

except:
    bug.stop()
    shifts.clean()
    GPIO.cleanup()