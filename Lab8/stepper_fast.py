import time
from shifter import Shifter

class StepperFast:
    """Stepper motor with speed modes and acceleration"""
    
    # Full-step: 4 steps/cycle, faster but less smooth
    seq_full = [0b0001, 0b0010, 0b0100, 0b1000]
    
    # Half-step: 8 steps/cycle, smoother but slower
    seq_half = [0b0001, 0b0011, 0b0010, 0b0110, 0b0100, 0b1100, 0b1000, 0b1001]
    
    shifter_outputs = 0
    
    def __init__(self, shifter, bit_offset=4):
        self.s = shifter
        self.bit_offset = bit_offset
        self.step_state = 0
        self.angle = 0
        self.mode = 'half'  # 'full' or 'half'
    
    def step(self, direction=1, delay=0.0012):
        """Take one step with custom delay"""
        seq = self.seq_full if self.mode == 'full' else self.seq_half
        
        self.step_state = (self.step_state + direction) % len(seq)
        
        StepperFast.shifter_outputs &= ~(0b1111 << self.bit_offset)
        StepperFast.shifter_outputs |= seq[self.step_state] << self.bit_offset
        self.s.shiftByte(StepperFast.shifter_outputs)
        
        time.sleep(delay)
    
    def rotate(self, degrees, speed='medium'):
        """
        Rotate with speed modes:
        'slow': 0.0015s/step (~10 RPM)
        'medium': 0.0012s/step (~12 RPM)
        'fast': 0.0008s/step (~18 RPM)
        'max': 0.0005s/step (~29 RPM) - may skip steps under load
        """
        delays = {'slow': 0.0015, 'medium': 0.0012, 'fast': 0.0008, 'max': 0.0005}
        delay = delays.get(speed, 0.0012)
        
        steps_per_rev = 4096 if self.mode == 'half' else 2048
        steps = int(abs(degrees) * steps_per_rev / 360)
        direction = 1 if degrees > 0 else -1
        
        for _ in range(steps):
            self.step(direction, delay)
        
        self.angle = (self.angle + degrees) % 360
    
    def rotate_smart(self, degrees, fast_threshold=10):
        """
        Smart rotation: use full-step for big moves, half-step for precision
        fast_threshold: switch to half-step within this many degrees of target
        """
        direction = 1 if degrees > 0 else -1
        remaining = abs(degrees)
        
        # Fast phase - full steps
        if remaining > fast_threshold:
            self.mode = 'full'
            fast_degrees = remaining - fast_threshold
            print(f"Fast mode: {fast_degrees:.1f}° at full-step")
            self.rotate(direction * fast_degrees, speed='fast')
            remaining = fast_threshold
        
        # Precision phase - half steps
        self.mode = 'half'
        print(f"Precision mode: {remaining:.1f}° at half-step")
        self.rotate(direction * remaining, speed='medium')
    
    def off(self):
        StepperFast.shifter_outputs &= ~(0b1111 << self.bit_offset)
        self.s.shiftByte(StepperFast.shifter_outputs)


if __name__ == '__main__':
    s = Shifter(data=2, latch=3, clock=4)
    m = StepperFast(s, bit_offset=4)
    
    print("=== Speed Comparison ===\n")
    
    # Test different speeds
    print("Slow (10 RPM)...")
    start = time.time()
    m.rotate(90, speed='slow')
    print(f"  Took {time.time()-start:.2f}s\n")
    
    print("Medium (12 RPM)...")
    start = time.time()
    m.rotate(90, speed='medium')
    print(f"  Took {time.time()-start:.2f}s\n")
    
    print("Fast (18 RPM)...")
    start = time.time()
    m.rotate(90, speed='fast')
    print(f"  Took {time.time()-start:.2f}s\n")
    
    print("=== Full-step vs Half-step ===\n")
    
    print("Full-step mode (faster, less smooth)...")
    m.mode = 'full'
    start = time.time()
    m.rotate(360, speed='medium')
    print(f"  1 revolution: {time.time()-start:.2f}s\n")
    
    print("Half-step mode (slower, smoother)...")
    m.mode = 'half'
    start = time.time()
    m.rotate(360, speed='medium')
    print(f"  1 revolution: {time.time()-start:.2f}s\n")
    
    print("=== Smart Rotation (180°) ===")
    m.rotate_smart(180, fast_threshold=20)
    
    m.off()
    print("\nDone!")

