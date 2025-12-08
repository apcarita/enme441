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
            enemy_positions.append([pos['r'], pos['theta'], 8])
    return enemy_positions

def getGlobes(json):
    globes = json['globes']
    return [[globe['r'], globe['theta'], globe['z']] for globe in globes]

def getFiringAngles(curPos, target):
    """
    Calculate firing angles relative to turret's local frame.
    Assumes turret's zero azimuth points toward field center (theta=0).
    """
    zLaser = 0.9911  # Laser height in cm
    
    # Convert polar to Cartesian
    cur_x = curPos[0] * m.cos(curPos[1])
    cur_y = curPos[0] * m.sin(curPos[1])
    
    target_x = target[0] * m.cos(target[1])
    target_y = target[0] * m.sin(target[1])
    target_z = target[2]
    
    # Delta in global frame
    delta_x = target_x - cur_x
    delta_y = target_y - cur_y
    delta_z = target_z - zLaser
    
    # Calculate angle in global frame
    global_azimuth = m.atan2(delta_y, delta_x)
    
    # Convert to turret's local frame
    # Assuming turret's zero points toward field center (at angle = turret_theta + pi)
    turret_facing = curPos[1] + m.pi  # Turret faces outward from center
    azimuth = global_azimuth - turret_facing
    
    # Normalize to [-pi, pi]
    while azimuth > m.pi:
        azimuth -= 2 * m.pi
    while azimuth < -m.pi:
        azimuth += 2 * m.pi
    
    # Altitude: elevation angle from horizontal
    horizontal_dist = m.sqrt(delta_x**2 + delta_y**2)
    altitude = m.atan2(delta_z, horizontal_dist)
    
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


