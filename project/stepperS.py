import time
from shifter import Shifter

class Stepper:    
    seq = [0b0001, 0b0011, 0b0010, 0b0110, 0b0100, 0b1100, 0b1000, 0b1001]
    delay = 0.0012  #1.2ms
    steps_per_rev = 4096
    shifter_outputs = 0
    
    def __init__(self, shifter, bit_offset=4):
        self.s = shifter
        self.step_state = 0
        self.angle = 0
        self.bit_offset = bit_offset
    
    def step(self, direction=1):
        self.step_state = (self.step_state + direction) % 8
        
        Stepper.shifter_outputs &= ~(0b1111 << self.bit_offset)
        Stepper.shifter_outputs |= Stepper.seq[self.step_state] << self.bit_offset
        self.s.shiftByte(Stepper.shifter_outputs)
        
        self.angle += direction * 360 / Stepper.steps_per_rev
        self.angle %= 360
    
    def rotate(self, degrees):
        steps = int(abs(degrees) * Stepper.steps_per_rev / 360)
        direction = 1 if degrees > 0 else -1
        
        for _ in range(steps):
            self.step(direction)
            time.sleep(Stepper.delay)
    
    def off(self):
        Stepper.shifter_outputs &= ~(0b1111 << self.bit_offset)
        self.s.shiftByte(Stepper.shifter_outputs)


def interleave_rotate(motors, degrees_list):
    """
    Rotate multiple motors simultaneously by interleaving steps
    motors: list of Stepper objects
    degrees_list: list of degrees for each motor
    """
    steps_list = [int(abs(d) * Stepper.steps_per_rev / 360) for d in degrees_list]
    dirs = [1 if d > 0 else -1 for d in degrees_list]
    
    max_steps = max(steps_list)
    
    for i in range(max_steps):
        for j, motor in enumerate(motors):
            if i < steps_list[j]:
                motor.step(dirs[j])
        time.sleep(Stepper.delay)


if __name__ == '__main__':
    print("Starting stepper test...")
    
    s = Shifter(data=2, latch=3, clock=4)
    m1 = Stepper(s)  # QA-QD
    
    print("Rotating 90 degrees...")
    m1.rotate(90)
    
    print("Rotating back -90 degrees...")
    m1.rotate(-90)
    
    print("Rotating 360 degrees (1 full rev)...")
    m1.rotate(360)
    
    m1.off()
    print("Done!")
