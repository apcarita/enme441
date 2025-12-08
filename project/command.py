import requests
import math as m
import json
import os

def fetchJson(url, save_local=True):
    fallback_path = os.path.join(os.path.dirname(__file__), '../frontend/public/positions.json')
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Save to local file so frontend visualization matches
        if save_local:
            with open(fallback_path, 'w') as f:
                json.dump(data, f, indent=2)        
        return data
    except Exception as e:
        print(f'Failed to fetch from {url}: {e}')
        print('Falling back to local JSON file')
        with open(fallback_path, 'r') as f:
            return json.load(f)

def getMePos(json,id):
    turrets = json['turrets']
    curPos = turrets[id]
    return [curPos['r'], curPos['theta']]

def getEnemyPos(json,me):
    turrets = json['turrets']
    enemy_positions = []
    for id,pos in turrets.items():
        if id != str(me):
            enemy_positions.append([pos['r'], pos['theta'], 6.16])  # 101.6mm turret height
    return enemy_positions

def getGlobes(json):
    globes = json['globes']
    return [[globe['r'], globe['theta'], globe['z']] for globe in globes]

def getFiringAngles(curPos, target):
    """
    Calculate firing angles for the turret.
    Assumes turret's azimuth=0 points toward field origin (theta=0 direction).
    
    Calibration: Point turret toward the marked field origin and press "Set Zero"
    """
    LASER_HEIGHT = 9.911  # cm (calibrated laser height above ground)
    
    # Convert polar coordinates to Cartesian (x, y, z)
    # Using standard math convention: x = r*cos(theta), y = r*sin(theta)
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
    
    # Azimuth: angle in horizontal plane (XY)
    # atan2(y, x) gives angle from positive x-axis
    azimuth = m.atan2(delta_y, delta_x)
    
    # Altitude: elevation angle from horizontal
    horizontal_distance = m.sqrt(delta_x**2 + delta_y**2)
    altitude = m.atan2(delta_z, horizontal_distance)
    
    return azimuth, altitude


# For testing, load local JSON file instead of remote fetch
with open('frontend/public/positions.json', 'r') as f:
    positions_data = json.load(f)

#positions_data = fetchJson("")

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


