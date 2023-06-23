import numpy as np
import matplotlib.pyplot as plt
import pytz as pytz
from mpl_toolkits.basemap import Basemap
from exif import Image
import PIL
import csv
import os
from skyfield.api import load, wgs84
from datetime import datetime
import pytz

stations_url = 'http://celestrak.org/NORAD/elements/stations.txt'
satellites = load.tle_file(stations_url)
by_name = {sat.name: sat for sat in satellites}
satellite = by_name['ISS (ZARYA)']
ts = load.timescale()

plt.figure(figsize=(16, 12))
m = Basemap(projection='ortho', lon_0=15, lat_0=30, resolution='c')
m.drawcoastlines()
m.bluemarble(scale=0.5);


def decimal_coords(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == 'S' or ref == 'W':
        decimal_degrees = -decimal_degrees
    return decimal_degrees


def get_time(image):
    with open(image, 'rb') as image_file:
        img = Image(image_file)
        time_str = img.get("datetime_original")
        time = datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
    return time


lats_d = []
lons_d = []
lats_n = []
lons_n = []
path = 'CDOSR/Images/02_May_2023_04h13m06s'
classification = {}
confidence = {}

with open("daynight.csv", 'r') as file:
    reader = csv.reader(file, delimiter=',')
    next(reader, None)
    for row in reader:
        classification[row[0]] = row[1]
        confidence[row[0]] = row[2]

csvlats=[]
csvlons=[]

with open('CDOSR/log02_May_2023_04h13m06s.csv', 'r') as file:
    csvreader=csv.reader(file, delimiter=',')
    next(csvreader, None)
    for row in csvreader:
        lat=float(row[2])
        lon=float(row[3])
        csvlats.append(lat)
        csvlons.append(lon)


def convert(deg):
    d, m, s = str(deg).replace('deg', '').split(" ")
    ans = float(d) + (float(m.strip("'")) / 60) + (float(s.strip('"')) / 3600)
    return ans


for file in os.listdir(path):
    t = get_time(path + '/' + file)
    utc = pytz.utc
    l = utc.localize(t)
    T = ts.from_datetime(l)
    geocentric = satellite.at(T)
    subpoint = geocentric.subpoint()
    lat = convert(subpoint.latitude)
    lon = convert(subpoint.longitude)
    if classification[file] == 'day':
        lats_d.append(lat)
        lons_d.append(lon)
    else:
        lats_n.append(lat)
        lons_n.append(lon)

xc, yc = m(csvlons, csvlats)
m.plot(xc, yc, 'o-', color='#4a4a4f', markersize=5, linewidth=1)
xd, yd = m(lons_d, lats_d)
m.plot(xd, yd, 'o-', color='#e8bb09', markersize=5, linewidth=1)
xn, yn = m(lons_n, lats_n)
#m.plot(xn, yn, 'o-', color='black', markersize=5, linewidth=1)
plt.show()
