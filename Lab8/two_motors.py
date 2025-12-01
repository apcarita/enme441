from stepperS import Stepper, interleave_rotate
from shifter import Shifter

s = Shifter(data=2, latch=3, clock=4)

m1 = Stepper(s, bit_offset=4)  # QA-QD
m2 = Stepper(s, bit_offset=0)  # QE-QH

print("Moving both motors simultaneously...")
interleave_rotate([m1, m2], [360, -180])

print(f"m1 angle: {m1.angle}, m2 angle: {m2.angle}")

m1.off()
m2.off()
print("Done!")

