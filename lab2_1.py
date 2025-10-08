import RPi.GPIO as GPIO
from time import time
import math as m

GPIO.setmode(GPIO.BCM)
p = [4, 17, 27, 22, 10, 9, 11, 5, 6, 14]

pwm = []
for i in p:
    GPIO.setup(i, GPIO.OUT)
    pp = GPIO.PWM(i, 500)
    pp.start(0)
    pwm.append(pp)

dir = 1
f = 0.2
phi = m.pi/11

def flip_dir(pin):
    global dir
    dir *= -1   
    print(f"dir: {dir}")

GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(26, GPIO.RISING, callback=flip_dir, bouncetime=600)

try:
    while 1:
        t = time()
        for ii in range(len(p)):
            
            B = (m.sin(2*m.pi*f*t - dir*phi*ii))**2 
            pwm[ii].ChangeDutyCycle(B*100) # set duty cycle


except KeyboardInterrupt: # stop gracefully on ctrl-C
    print('\nExiting')
    for ppp in pwm:
        ppp.stop()
    pwm.clear() 
    GPIO.cleanup()