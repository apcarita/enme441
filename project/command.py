import requests
import math as m
import json
import os

def fetchJson(url, save_local=False):
    fallback_path = os.path.join(os.path.dirname(__file__), '../frontend/public/positions.json')
    
    try:
        response = requests.get(url, timeout=5)
        return response.json()
    except Exception as e:
        print(f'Failed to fetch from {url}: {e}')
        # Try fallback file if it exists
        if os.path.exists(fallback_path):
            print('Using fallback local JSON file')
            with open(fallback_path, 'r') as f:
                return json.load(f)
        raise

def getMePos(json,id):
    turrets = json['turrets']
    curPos = turrets[id]
    return [curPos['r'], curPos['theta']]

def getEnemyPos(json,me):
    turrets = json['turrets']
    enemy_positions = []
    for id,pos in turrets.items():
        if id != str(me):
            enemy_positions.append([pos['r'], pos['theta'], 6.16])  
    return enemy_positions

def getGlobes(json):
    globes = json['globes']
    return [[globe['r'], globe['theta'], globe['z']] for globe in globes]

def getFiringAngles(curPos, target):
    LASER_HEIGHT = 9.911  # cm - height of laser above ground 
    
    # Convert polar coordinates to Cartesian (x, y, z)
    # x = r*cos(theta), y = r*sin(theta)
    turret_x = curPos[0] * m.cos(curPos[1])
    turret_y = curPos[0] * m.sin(curPos[1])
    turret_z = LASER_HEIGHT
    
    target_x = target[0] * m.cos(target[1])
    target_y = target[0] * m.sin(target[1])
    target_z = target[2]
    
    # Vector from turret to target
    delta_x = target_x - turret_x
    delta_y = target_y - turret_y
    delta_z = target_z - turret_z
    
    # Absolute angle from turret to target
    target_angle = m.atan2(delta_y, delta_x)
    
    # Turret's zero position points toward origin (theta + pi)
    turret_zero = curPos[1] + m.pi
    
    # Relative azimuth (turret needs to rotate from zero to target)
    azimuth = turret_zero - target_angle
    while azimuth > m.pi:
        azimuth -= 2 * m.pi
    while azimuth < -m.pi:
        azimuth += 2 * m.pi
    
    # Altitude (no reference needed, turret starts level)
    altitude = m.atan2(delta_z, m.sqrt(delta_x**2 + delta_y**2))
    
    return azimuth, altitude


if __name__ == "__main__":
    # For testing, load local JSON file instead of remote fetch
    #with open('frontend/public/positions.json', 'r') as f:
       # positions_data = json.load(f)

    positions_data = fetchJson("http://192.168.1.254:8000/positions.json")

    print("current location: ")
    print(getMePos(positions_data, '13'))

    print("\n emmnies at: ")
    print(getEnemyPos(positions_data, '13'))

    # Compute firing angles for each enemy
    me_pos = getMePos(positions_data, '13')
    enemies = getEnemyPos(positions_data, '13')
    for i, enemy in enumerate(enemies):
        theta, phi = getFiringAngles(me_pos, enemy)
        print(f"Angles to enemy {i+1}: theta={theta}, phi={phi}")


