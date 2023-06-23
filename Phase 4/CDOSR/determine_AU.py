import json
import numpy as np

with open('parameters.json') as json_file:
    data = json.load(json_file)
    v = data['velocity']
    t = data['time']
    h = data['altitude']

h = h / 1000
r = 6371  # Earth's radius
alpha = np.arccos(r / (r + h))*180/np.pi - v * t * 180 / (np.pi * (r + h))
beta = 90 - alpha
AU = r / (np.cos(beta*np.pi/180))

print('The distance between the Sun and Earth (1 AU) is approximately: {} km'.format(AU))
