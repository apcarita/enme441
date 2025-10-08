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
    pwm.append(p_obj)

f = 0.2
phi = m.pi/11

try:
    while 1:
        t = time()
        for ii in range(len(p)):
            B = (m.sin(2*m.pi*f*t - phi*ii))**2 
            pwm[ii].ChangeDutyCycle(B*100) # set duty cycle


except KeyboardInterrupt: # stop gracefully on ctrl-C
    print('\nExiting')
    for i in pwm:
        i.stop()
    GPIO.cleanup()