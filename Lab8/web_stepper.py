from flask import Flask, request, jsonify
from stepperS import Stepper, interleave_rotate
from shifter import Shifter
import threading

app = Flask(__name__)

s = Shifter(data=2, latch=3, clock=4)
m1 = Stepper(s, bit_offset=4)

motor_lock = threading.Lock()

@app.route('/rotate', methods=['POST'])
def rotate():
    """Rotate motor by degrees. POST with {"degrees": 90}"""
    data = request.get_json()
    degrees = float(data.get('degrees', 0))
    
    def do_rotate():
        with motor_lock:
            m1.rotate(degrees)
    
    threading.Thread(target=do_rotate).start()
    return jsonify({"status": "rotating", "degrees": degrees})

@app.route('/angle', methods=['GET'])
def get_angle():
    """Get current angle"""
    return jsonify({"angle": m1.angle})

@app.route('/off', methods=['POST'])
def motor_off():
    """Turn off motor"""
    m1.off()
    return jsonify({"status": "off"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

