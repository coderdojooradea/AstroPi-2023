import csv
import json

alt = 0
len = 0

with open("CDOSR/log02_May_2023_04h13m06s.csv", 'r') as file:
    reader = csv.reader(file, delimiter=',')
    next(reader, None)
    for row in reader:
        alt = alt + float(row[4])
        len += 1
alt = alt / len
print(alt)

with open('parameters.json', 'r') as json_file:
    data = json.load(json_file)
    data['altitude'] = alt

with open('parameters.json', 'w') as json_file:
    json.dump(data, json_file)
