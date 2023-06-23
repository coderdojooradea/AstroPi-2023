import csv
import json

from exif import Image
from datetime import datetime

path = 'CDOSR/Images/02_May_2023_04h13m06s/'
cls = []
point1 = []
point2 = []
name = []
offset = 0.04


def get_time(image):
    with open(path + image, 'rb') as image_file:
        img = Image(image_file)
        time_str = img.get("datetime_original")
        time = datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
    return time


with open("daynight.csv", 'r') as file:
    reader = csv.reader(file, delimiter=',')
    next(reader, None)
    for row in reader:
        cls.append(row[1])
        name.append(row[0])

for i in range(len(cls)):
    if cls[i] == 'day' and cls[i + 1] == 'night':
        point1.append(name[i - 1])

cls.clear()
name.clear()

with open("in_earths_shadow.csv", 'r') as file:
    reader = csv.reader(file, delimiter=',')
    next(reader, None)
    for row in reader:
        cls.append(row[1])
        name.append(row[0])

for i in range(len(cls)):
    if cls[i] == "in earth's shadow" and cls[i - 1] == 'sunlit':
        point2.append(name[i])

print('Available points:')

for i in range(min(len(point1), len(point2))):
    print(str(i + 1) + '. ' + point1[i] + " and " + point2[i])

Set = input('Chosen set: ')

t2 = get_time(point2[int(Set) - 1])
t1 = get_time(point1[int(Set) - 1])

time_difference = (t2 - t1).seconds + offset

print(str(time_difference) + ' seconds')

with open('parameters.json') as json_file:
    data = json.load(json_file)
    data['time'] = time_difference
with open('parameters.json', 'w') as json_file:
    json.dump(data, json_file)
