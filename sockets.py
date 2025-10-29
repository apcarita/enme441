import RPi.GPIO as gpio
import threading
from time import *
import socket

LED_PINS = [2, 3, 4]

led_brightness = {1: 0, 2: 0, 3: 0}

gpio.setmode(gpio.BCM)
pwm_objects = {}
for pin in LED_PINS:
    gpio.setup(pin, gpio.OUT)
    pwm_objects[pin] = gpio.PWM(pin, 1000)  # 1kHz frequency
    pwm_objects[pin].start(0)

def web_page():
    html = """
    <html><head><title>LED Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <head>
    <style>
    html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
    h1{color: #0F3376; padding: 2vh;}
    p{font-size: 1.5rem;}
    .slider-container {margin: 20px auto; width: 300px;}
    input[type="range"] {width: 100%; height: 25px;}
    .led-label {font-size: 1.2rem; margin: 10px 0;}
    </style>
    <script>
    function updateLED(ledNum) {
        var brightness = document.getElementById('slider' + ledNum).value;
        document.getElementById('value' + ledNum).textContent = brightness + '%';
        
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/', true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.send('led=' + ledNum + '&brightness=' + brightness);
    }
    </script>
    </head>
    <body>
    <h1>LED Brightness Control</h1>
    
    <div class="slider-container">
      <p class="led-label">LED 1: <span id="value1">""" + str(led_brightness[1]) + """%</span></p>
      <input type="range" id="slider1" min="0" max="100" value="""" + str(led_brightness[1]) + """" 
             oninput="updateLED(1)">
    </div>
    
    <div class="slider-container">
      <p class="led-label">LED 2: <span id="value2">""" + str(led_brightness[2]) + """%</span></p>
      <input type="range" id="slider2" min="0" max="100" value="""" + str(led_brightness[2]) + """" 
             oninput="updateLED(2)">
    </div>
    
    <div class="slider-container">
      <p class="led-label">LED 3: <span id="value3">""" + str(led_brightness[3]) + """%</span></p>
      <input type="range" id="slider3" min="0" max="100" value="""" + str(led_brightness[3]) + """" 
             oninput="updateLED(3)">
    </div>
    
    </body>
    </html>
    """
    return bytes(html, 'utf-8')

# Helper function to extract key,value pairs of POST data
def parsePOSTdata(data):
    data_dict = {}
    idx = data.find('\r\n\r\n')+4
    data = data[idx:]
    data_pairs = data.split('&')
    for pair in data_pairs:
        key_val = pair.split('=')
        if len(key_val) == 2:
            data_dict[key_val[0]] = key_val[1]
    return data_dict


def serve_web_page():
    while True:
        print("client connecting????? ")
        conn, (client_ip, client_port) = s.accept()  
        print(f'Connection from {client_ip} on client port {client_port}')
        client_message = conn.recv(2048).decode('utf-8')
        print(f'Message from client:\n{client_message}')
        data_dict = parsePOSTdata(client_message)
        
        if 'led' in data_dict.keys() and 'brightness' in data_dict.keys():
            led_num = int(data_dict["led"])
            brightness = int(data_dict["brightness"])
            led_brightness[led_num] = brightness
            # Set PWM duty cycle for the selected LED
            pwm_objects[LED_PINS[led_num-1]].ChangeDutyCycle(brightness)
            print(f'LED {led_num} set to {brightness}%')
        
        conn.send(b'HTTP/1.1 200 OK\r\n')                  # status line
        conn.send(b'Content-Type: text/html\r\n')          # headers
        conn.send(b'Connection: close\r\n\r\n')   
        try:
            conn.sendall(web_page())                       # body
        finally:
            conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # pass IP addr & socket type
s.bind(('', 80))     # bind to given port
s.listen(3)          # up to 3 queued connections

webpageTread = threading.Thread(target=serve_web_page)
webpageTread.daemon = True
webpageTread.start()

# Do whatever we want while the web server runs in a separate thread:
try:
    while True:
        pass
except:
    print('Joining webpageTread')
    webpageTread.join()
    print('Closing socket')
    s.close()
    gpio.cleanup()