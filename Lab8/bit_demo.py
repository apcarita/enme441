"""
Demonstration of how bit shifting works for stepper motor control
"""

# The sequence pattern (4 bits control 4 coils)
seq = [0b0001, 0b0011, 0b0010, 0b0110, 0b0100, 0b1100, 0b1000, 0b1001]

print("=== Understanding the Coil Sequence ===\n")
for i, pattern in enumerate(seq):
    coils = ""
    if pattern & 0b0001: coils += "A "
    if pattern & 0b0010: coils += "B "
    if pattern & 0b0100: coils += "C "
    if pattern & 0b1000: coils += "D "
    print(f"Step {i}: {bin(pattern):>8s} = coils {coils}")

print("\n=== Why We Need Bit Shifting ===\n")

# Simulate two motors on one shift register
shifter_outputs = 0b00000000  # 8-bit shift register output

# Motor 1: uses bits 7-4 (QA-QD), bit_offset=4
# Motor 2: uses bits 3-0 (QE-QH), bit_offset=0

print("Initial state: {:08b}".format(shifter_outputs))
print("                DCBADCBA  (D=bit7, A=bit0)")
print("                ^^^^----  Motor 1 (QA-QD)")
print("                    ^^^^  Motor 2 (QE-QH)\n")

# Motor 1 takes step 3 (pattern 0b0110 = coils B+C)
step_pattern = seq[3]  # 0b0110
bit_offset = 4

print(f"Motor 1 step 3: pattern = {bin(step_pattern)}")
print(f"Shift left by {bit_offset}: {bin(step_pattern << bit_offset)}")

# Clear motor 1's bits
shifter_outputs &= ~(0b1111 << bit_offset)
print(f"After clearing motor 1 bits: {bin(shifter_outputs):>8s}")

# Set motor 1's new pattern
shifter_outputs |= step_pattern << bit_offset
print(f"After setting motor 1: {bin(shifter_outputs):>8s}  (bits 6,5 on = coils B+C)\n")

# Motor 2 takes step 1 (pattern 0b0011 = coils A+B)
step_pattern = seq[1]
bit_offset = 0

print(f"Motor 2 step 1: pattern = {bin(step_pattern)}")
print(f"Shift left by {bit_offset}: {bin(step_pattern << bit_offset)}")

# Clear motor 2's bits
shifter_outputs &= ~(0b1111 << bit_offset)
print(f"After clearing motor 2 bits: {bin(shifter_outputs):>8s}")

# Set motor 2's new pattern
shifter_outputs |= step_pattern << bit_offset
print(f"After setting motor 2: {bin(shifter_outputs):>8s}  (bits 1,0 on = coils A+B)")

print("\nFinal output: {:08b}".format(shifter_outputs))
print("              01100011")
print("              ^^^^----  Motor 1: coils B+C energized")
print("                  ^^^^  Motor 2: coils A+B energized")

print("\n=== Bit Operator Summary ===\n")
print("& (AND):  Used with ~mask to clear specific bits")
print("| (OR):   Used to set specific bits to 1")
print("<< (SHIFT): Moves bits left to position them correctly")
print("~ (NOT):  Inverts bits (1→0, 0→1) to make a clearing mask")

