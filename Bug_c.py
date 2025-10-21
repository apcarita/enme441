import time
from Shifter import Shifter
import random as r
import RPi.GPIO as GPIO
import threading

class Bug():
    def __init__(self,  shifter, timestep=0.1, isWrapOn=False, x=3):
        self.timestep = timestep
        self.isWrapOn = isWrapOn
        self.__shifter = shifter
        self.x = x
        self.go = False
        self.thread = None
    
    def _run(self):
        while(self.go):
            dir = r.randint(0,1) 

            if(dir):
                self.x = self.x >> 1
                if(self.x <= 0):
                    if(self.isWrapOn):
                        self.x = 128
                    else:
                        self.x=1
            else:
                self.x = self.x << 1
                if(self.x >= 128):
                    if(self.isWrapOn):
                        self.x = 1
                    else:
                        self.x=128
            
            self.__shifter.shiftByte(self.x)
            time.sleep(self.timestep)

    def start(self):
        if(not self.go):
            self.go = True
            self.thread = threading.Thread(target=self._run)
            self.thread.start()

    def stop(self):
        self.go = False
        if self.thread:
            self.thread.join()
        self.__shifter.shiftByte(0)

    
    
