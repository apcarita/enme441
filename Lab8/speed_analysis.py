"""
Analysis of stepper motor speed vs precision tradeoffs
"""

print("=" * 60)
print("28BYJ-48 STEPPER MOTOR SPEED ANALYSIS")
print("=" * 60)

print("\n### HALF-STEP MODE (current) ###")
print("Steps per revolution: 4096")
print("Resolution: 360°/4096 = 0.088° per step")
print()
print("Delay (ms) | Steps/sec | RPM   | Time for 360°")
print("-" * 50)
delays_half = [2.0, 1.5, 1.2, 1.0, 0.8, 0.5]
for d in delays_half:
    steps_per_sec = 1000 / d
    rpm = (steps_per_sec * 60) / 4096
    time_360 = 4096 * (d / 1000)
    print(f"{d:5.1f}      | {steps_per_sec:7.0f}   | {rpm:5.1f} | {time_360:5.2f}s")

print("\n### FULL-STEP MODE ###")
print("Steps per revolution: 2048")
print("Resolution: 360°/2048 = 0.176° per step (HALF the precision)")
print()
print("Delay (ms) | Steps/sec | RPM   | Time for 360°")
print("-" * 50)
delays_full = [2.0, 1.5, 1.2, 1.0, 0.8, 0.5]
for d in delays_full:
    steps_per_sec = 1000 / d
    rpm = (steps_per_sec * 60) / 2048
    time_360 = 2048 * (d / 1000)
    print(f"{d:5.1f}      | {steps_per_sec:7.0f}   | {rpm:5.1f} | {time_360:5.2f}s")

print("\n### SMART STRATEGY ###")
print("For a 180° move with 20° precision window:")
print()
print("All half-step (slow):")
print("  - 180° @ 1.2ms/step = 2048 steps = 2.46s")
print()
print("Smart (full→half):")
print("  - 160° full-step @ 0.8ms/step = 910 steps = 0.73s")
print("  - 20° half-step @ 1.2ms/step = 228 steps = 0.27s")
print("  - Total: 1.00s (2.5x FASTER!)")
print()
print("Precision loss: ZERO (ends in half-step mode)")

print("\n### PRACTICAL LIMITS ###")
print("28BYJ-48 typical max: ~800 steps/sec (may vary with load)")
print("Below 0.8ms/step: Risk of skipping steps or stalling")
print("Recommendation: 0.8-1.2ms for reliable operation")

print("\n### SHIFT REGISTER SPEED ###")
print("74HC595 @ 5V: ~25 MHz clock")
print("8 bits @ 1MHz = 8µs to shift one byte")
print("Conclusion: Shift register is NOT the bottleneck")
print("            Motor mechanics limit the speed")

print("\n" + "=" * 60)

