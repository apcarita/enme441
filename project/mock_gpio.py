"""Mock GPIO for testing on non-Raspberry Pi systems"""

# Pin modes
BCM = 'BCM'
OUT = 'OUT'
IN = 'IN'
HIGH = 1
LOW = 0

def setmode(mode):
    pass

def setup(pin, mode):
    pass

def output(pin, state):
    pass

def cleanup():
    pass

