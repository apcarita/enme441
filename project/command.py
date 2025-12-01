import requests
import math as m
import json 

def fetchJson(url):
    response = requests.get(url)
    return response.json()

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
    # theata and phi angle between cur x,y,z and delta
    theata = m.atan2(delta[1], delta[0])
    phi = m.atan2(m.sqrt(delta[0]**2 + delta[1]**2), delta[2])
    return theata, phi


# For testing, load local JSON file instead of remote fetch
with open('frontend/public/positions.json', 'r') as f:
    positions_data = json.load(f)

print(getMePos(positions_data, '13'))
print(getEnemyPos(positions_data, '13'))

# Compute firing angles for each enemy
me_pos = getMePos(positions_data, '13')
enemies = getEnemyPos(positions_data, '13')
for i, enemy in enumerate(enemies):
    theta, phi = getFiringAngles(me_pos, enemy)
    print(f"Angles to enemy {i+1}: theta={theta}, phi={phi}")


