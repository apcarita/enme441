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
    zLaser = .9911
    cur = [curPos[0] * m.cos(curPos[1]), curPos[0] * m.sin(curPos[1]), .9911]

    target = [target[0] * m.cos(target[1]), target[0] * m.sin(target[1]), target[2]]

    delta = [target[0] - cur[0], target[1] - cur[1], target[2] - zLaser]
    
    # Azimuth: angle in horizontal plane
    azimuth = m.atan2(delta[1], delta[0])
    
    # Altitude: elevation angle from horizontal (not zenith angle)
    horizontal_dist = m.sqrt(delta[0]**2 + delta[1]**2)
    altitude = m.atan2(delta[2], horizontal_dist)  # Positive = up, negative = down
    
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


