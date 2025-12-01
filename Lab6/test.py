# Shift register debugger for stepper motor testing

from shifter import Shifter
from time import sleep

# Set up the shift register
s = Shifter(data=2, latch=3, clock=4)

print("Shift Register Stepper Motor Debugger")
print("=" * 50)
print("\nThis will test both motors connected to the shift register")
print("Motor 2 should use pins Qa-Qd (bits 0-3)")
print("Motor 1 should use pins Qe-Qh (bits 4-7)")
print("\nPress Ctrl+C to exit\n")

# Stepper sequence (CCW)
seq = [0b0001, 0b0011, 0b0010, 0b0110, 0b0100, 0b1100, 0b1000, 0b1001]

try:
    while True:
        print("\n1. Test Motor 2 only (bits 0-3, pins Qa-Qd)")
        print("2. Test Motor 1 only (bits 4-7, pins Qe-Qh)")
        print("3. Test both motors together")
        print("4. All outputs ON (0xFF)")
        print("5. All outputs OFF (0x00)")
        print("6. Blink pattern")
        print("7. Rotate Motor 2 forward")
        print("8. Rotate Motor 1 forward")
        
        choice = input("\nEnter choice (1-8): ")
        
        if choice == '1':
            print("Testing Motor 2 (should be on Qa-Qd)...")
            for i in range(32):  # 4 full sequences
                for pattern in seq:
                    s.shiftByte(pattern)
                    print(f"Sent: {bin(pattern)}")
                    sleep(0.003)
            s.shiftByte(0)  # turn off
            
        elif choice == '2':
            print("Testing Motor 1 (should be on Qe-Qh)...")
            for i in range(32):  # 4 full sequences
                for pattern in seq:
                    shifted = pattern << 4
                    s.shiftByte(shifted)
                    print(f"Sent: {bin(shifted)}")
                    sleep(0.003)
            s.shiftByte(0)  # turn off
            
        elif choice == '3':
            print("Testing both motors together...")
            for i in range(32):
                for pattern in seq:
                    both = pattern | (pattern << 4)
                    s.shiftByte(both)
                    print(f"Sent: {bin(both)}")
                    sleep(0.003)
            s.shiftByte(0)  # turn off
            
        elif choice == '4':
            print("All outputs ON (should energize all coils)")
            s.shiftByte(0xFF)
            print("Sent: 0b11111111")
            input("Press Enter to turn off...")
            s.shiftByte(0)
            
        elif choice == '5':
            print("All outputs OFF")
            s.shiftByte(0x00)
            print("Sent: 0b00000000")
            
        elif choice == '6':
            print("Blinking pattern on all outputs...")
            for i in range(10):
                s.shiftByte(0xFF)
                sleep(0.2)
                s.shiftByte(0x00)
                sleep(0.2)
                
        elif choice == '7':
            steps = int(input("Enter number of steps: "))
            print(f"Rotating Motor 2 forward {steps} steps...")
            for i in range(steps):
                pattern = seq[i % 8]
                s.shiftByte(pattern)
                print(f"Step {i}: {bin(pattern)}")
                sleep(0.003)
            s.shiftByte(0)
            
        elif choice == '8':
            steps = int(input("Enter number of steps: "))
            print(f"Rotating Motor 1 forward {steps} steps...")
            for i in range(steps):
                pattern = seq[i % 8] << 4
                s.shiftByte(pattern)
                print(f"Step {i}: {bin(pattern)}")
                sleep(0.003)
            s.shiftByte(0)
            
        else:
            print("Invalid choice!")

except KeyboardInterrupt:
    print("\n\nShutting down...")
    s.shiftByte(0)  # Turn everything off
    print("All outputs turned OFF")
