# -*- coding: utf-8 -*-

# AstroPi Mission Lab 2023
# CoderDojo Oradea
# Team: CDOSR 
# TeamID: CDOSR
# Coordinating mentor: Daniel Erzse

# Libraries import
from logging import WARNING, INFO, DEBUG
import os, sys, datetime
from logzero import logger, logfile, loglevel
from sense_hat import SenseHat
from math import degrees, radians
from orbit import ISS
from skyfield.api import load, load_file, Loader, wgs84, EarthSatellite
from picamera import PiCamera
import csv
from pathlib import Path
from skyfield.api import load, Topos
from skyfield import almanac
import dateutil.parser

# Create a SenseHat instance
sh = SenseHat()
sh.clear()

# Create a PiCamera instance
cam = PiCamera()
cam.resolution = (2028,1520) #(1920,1080)

# Programm constants
loglevel(level = WARNING)
startTime = datetime.datetime.now()
currentTime = datetime.datetime.now()
lastPhotoTime = datetime.datetime.now()
runningTime = 180*60 #180*60 seconds
photodelay = 5
ph_counter = 1

# Reading the current directory and creating local directories
# base_folder = Path(__file__).parent.resolve()
dir_path = os.path.dirname(os.path.realpath(__file__))
# print("base folder: {}\nDirtpath: {}\n---".format(base_folder, dir_path))
cdosr_dir = dir_path + "/CDOSR"    # CDOSR is CoderDojo Oradea Space Robotics log folder
if not os.path.exists(cdosr_dir):
    os.mkdir(cdosr_dir)
cdosr_imgdir = cdosr_dir + "/Images"
if not os.path.exists(cdosr_imgdir):
    os.mkdir(cdosr_imgdir)
imgFolder = cdosr_imgdir + "/{}".format(startTime.strftime("%d_%b_%Y_%Hh%Mm%Ss"))
if not os.path.exists(imgFolder):
    os.mkdir(imgFolder)
logfilename = cdosr_dir + "/log{}.csv".format(startTime.strftime("%d_%b_%Y_%Hh%Mm%Ss"))
errorfile = cdosr_dir + "/errors_{}".format(startTime.strftime("%d_%b_%Y_%Hh%Mm%Ss"))
eventfile = cdosr_dir + "/events.log"
#print(eventfile)
logfile(eventfile, maxBytes=1000000, backupCount=3, loglevel=INFO)

# Download ephemeris
try: 
    ephem_dir = dir_path + "/Ephem"
    if not os.path.exists(ephem_dir):
        os.mkdir(ephem_dir)
    ephem_path = '/home/sandbox/de421.bsp'
    if os.path.exists(ephem_path):
        ephemeris= load_file(ephem_path)  # ephemeris DE421
    else:
        load = Loader(ephem_dir)
        ephemeris = load('/home/sandbox/de421.bsp')
    #print(ISS.coordinates())

except Exception as e:
    with open(errorfile, 'w') as f:
        f.write('Mission error: ' + str(e))

def create_csv(data_file):
    """
    Creates the csv file
    """
    with open(data_file, 'w', buffering=1) as f:
        writer = csv.writer(f)
        header = ("Timestamp","Daylight", "Latitude","Longitude","Height", "Pressure","Temp_hum","Temp_pres","Humidity","AccelX","AccelY","AccelZ","Pitch","Roll","Yaw","GyroX","GyroY","GyroZ","North","CompassX","CompassY","CompassZ")
        writer.writerow(header)
    # except Exception as e: # (FileNotFoundError, PermissionError) as e:
    #     print(f'{e.__class__.__name__}: {e})')
    #     logger.error(f'{e.__class__.__name__}: {e})')


def add_csv_data(data_file, data):
    """
    Add 'data' to 'datafile' csv
    """
    with open(data_file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)

def convert(angle):
    """
    Convert a `skyfield` Angle to an EXIF-appropriate representation (rationals)
    e.g. 98° 34' 58.7 to "98/1,34/1,587/10"
    Return a tuple containing a boolean and the converted angle,
    with the boolean indicating if the angle is negative.
    """
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = '{:.0f}/1,{:.0f}/1,{:.0f}/10'.format(degrees, minutes, seconds*10)
    return sign < 0, exif_angle

# Retrieve ISS position and write lat/long to EXIF data for photographs
def isstrack():
    # Obtain the current time `t`
    t = load.timescale().now()

    # Compute where the ISS is at time `t`
    position = ISS.at(t)

    # Compute the coordinates of the Earth location directly beneath the ISS
    location = position.subpoint()

    lon = round(location.longitude.degrees, 6)
    lat = round(location.latitude.degrees, 6)
    height = round(location.elevation.m, 3)

    # Convert the latitude and longitude to EXIF-appropriate representations
    south, exif_latitude = convert(location.latitude)
    west, exif_longitude = convert(location.longitude)

    # Set the EXIF tags specifying the current location
    cam.exif_tags['GPS.GPSLatitude'] = exif_latitude
    cam.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    cam.exif_tags['GPS.GPSLongitude'] = exif_longitude
    cam.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

    return lat, lon, height


def sun_position(eph): 
    '''
    The function computes the current position of the International Space Station (ISS) and creates 
    an observer at that position to determine whether it is day or night at that location. 
    It does this by checking the altitude of the Sun relative to the observer's position. If the 
    altitude is above the horizon, then it is day, and if it is below the horizon, then it is night.
    '''
    try:
        ts = load.timescale()
        ISStime = ts.now()
        sun_up = True

        # TLE data for ISS          
        line1 = '1 25544U 98067A   23055.16561388  .00016938  00000+0  31182-3 0  9997'
        line2 = '2 25544  51.6388 168.3534 0005337  21.8259  55.3377 15.49277264384268'


        # Get the position of the ISS at the current time
        iss = EarthSatellite(line1, line2)
        iss_position = iss.at(ISStime)

        # Compute the coordinates of the Earth location directly beneath the ISS
        observer = iss_position.subpoint()

        # Get the longitude and latitude of the observer
        lon = round(observer.longitude.degrees, 6)
        lat = round(observer.latitude.degrees, 6)
        height = round(observer.elevation.m, 3)

        # Convert the latitude and longitude to EXIF-appropriate representations
        south, exif_latitude = convert(observer.latitude)
        west, exif_longitude = convert(observer.longitude)

        # Set the EXIF tags specifying the current location
        cam.exif_tags['GPS.GPSLatitude'] = exif_latitude
        cam.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
        cam.exif_tags['GPS.GPSLongitude'] = exif_longitude
        cam.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"


        # Compute the sunrise and sunset times for the observer
        topos = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m = height)
        t0 = ts.utc(ISStime.utc_datetime().year, ISStime.utc_datetime().month, ISStime.utc_datetime().day)
        
        # t1 is t0 plus one day
        t1 = ts.utc(t0.utc_datetime() + datetime.timedelta(days=1))

        # Get the sunrise and sunset times as Python datetime objects
        time, moment = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(eph, observer))
        sunrise = None
        for t, is_sunrise in zip(time, moment):
            if is_sunrise:
                sunrise = dateutil.parser.parse(t.utc_iso())
            else:
                sunset = dateutil.parser.parse(t.utc_iso())

        now=ts.now().utc_datetime()
        tsr = sunrise - now
        tss = sunset - now
        
        return [[sunrise, tsr], [sunset, tss], ISStime, [lat, lon, height]]
        
    except AttributeError:
        print(AttributeError)


def sun_up_30(sun_rise_set): 
    '''
    The function checks whether the current time is within 30 minutes of either the next sunrise or 
    sunset time by calculating a time delta of 30 minutes and comparing it to the current time. It 
    returns True if the current time is within 30 minutes of either the sunrise or sunset time and 
    False otherwise.
    '''
    try:
        # Check if the current time is within 30 minutes of the sunrise or sunset time
        delta = datetime.timedelta(minutes=30)
        sunrise = sun_rise_set[0][0]
        srt = sun_rise_set[0][1]
        sunset = sun_rise_set[1][0]
        sst = sun_rise_set[1][1]
        ISStime = sun_rise_set[2]
        if sunset < sunrise:
            sunset = sunset + datetime.timedelta(days=1)
        if sunrise - delta <= ISStime.utc_datetime() <= sunrise + delta or sunset - delta <= ISStime.utc_datetime() <= sunset + delta:
            return True
        else:
            return False
    
    except AttributeError:
        print(AttributeError)

def sun_up(sun_rise_set): 
    '''
    The function checks whether the current time is during daylight hours or not by comparing the 
    current time with the sunrise and sunset times. It first adjusts the sunset time by adding one 
    day if the sunset time is earlier than the sunrise time (which can happen if the ISS location 
    is close to the North or South Pole). It then checks if the current time is between the sunrise 
    and sunset times, inclusive. It returns True if the current time is during daylight hours and 
    False otherwise.
    '''
    try:
        # Check if the current time is within 30 minutes of the sunrise or sunset time
        sunrise = sun_rise_set[0][0]
        srt = sun_rise_set[0][1]
        sunset = sun_rise_set[1][0]
        sst = sun_rise_set[1][1]
        ISStime = sun_rise_set[2]
        if sunset < sunrise:
            sunset = sunset + datetime.timedelta(days=1)
        if sunrise <= ISStime.utc_datetime() <= sunset:
            return True
        else:
            return False
    
    except AttributeError:
        print(AttributeError)


# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{:" + str(decimals+4) + "." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('{} |{}| {}% {}'.format(prefix, bar, percent, suffix), flush=True)
    sys.stdout.flush()

    # Print New Line on Complete
    if iteration == total: 
        print()

  
# Main program
print("CoderDojo Oradea Space Lab Mission")
print("  Team: CDOSR")
print("  Mission started at:      {}".format(startTime))
create_csv(logfilename)
step, counter = 0, 1
while currentTime <= startTime + datetime.timedelta(seconds=runningTime):
    try:
        # Reading sensor data from the SenseHat
        #lat, lon, height = isstrack()
        sun_moments = sun_position(ephemeris)
        lat, lon, height = sun_moments[3] 
        sunup = sun_up(sun_moments)
        sunup30 = sun_up_30(sun_moments)
        # print("Sunup: {}, Sun30 {}, Lat {}, Lon {}".format(sunup, sunup30, lat, lon))
        pressure  = round(sh.get_pressure(), 2)
        temp_hum  = round(sh.get_temperature_from_humidity(), 2)
        temp_pres = round(sh.get_temperature_from_pressure(), 2)
        humidity  = round(sh.get_humidity(), 2)
        acceleration = sh.get_accelerometer_raw()
        accelX = round(acceleration['x'], 4)
        accelY = round(acceleration['y'], 4)
        accelZ = round(acceleration['z'], 4)

        gyro_only = sh.get_gyroscope()
        gyro_raw  = sh.get_gyroscope_raw()
        pitch = round(gyro_only['pitch'],3)
        roll  = round(gyro_only['roll'],3)
        yaw   = round(gyro_only['yaw'],3)
        gyroX = round(gyro_raw['x'], 3)
        gyroY = round(gyro_raw['y'], 3)
        gyroZ = round(gyro_raw['z'], 3)
        north = round(sh.get_compass(), 3)
        compass_raw = sh.get_compass_raw()
        compassX    = round(compass_raw['x'], 2)
        compassY    = round(compass_raw['y'], 2)
        compassZ    = round(compass_raw['z'], 2)
        day = "night"


        # Gather all tha data in one variable
        rawdata = (currentTime, day, lat, lon, height, pressure, temp_hum, temp_pres, humidity, accelX, accelY, accelZ, pitch, roll, yaw, gyroX, gyroY, gyroZ, north, compassX, compassY, compassZ)
        add_csv_data(logfilename, rawdata)

        if sunup:
            photodelay = 5
            day = "day"
        if sunup30:
            photodelay = 0.5
            day = "twilight"
        # Image capture and saving
        if currentTime > lastPhotoTime + datetime.timedelta(seconds = photodelay) and (sunup or sunup30):
            cam.capture(imgFolder + "/CDOSR_{:%H%M%S}_{:04d}.jpg".format(currentTime, ph_counter))
            lastPhotoTime = currentTime
            ph_counter += 1
                
        # Get the new current time
        currentTime = datetime.datetime.now()
        # print(currentTime, day, lat, lon, height, pressure, temp_hum, temp_pres, humidity, accelX, accelY, accelZ, pitch, roll, yaw, gyroX, gyroY, gyroZ, north, compassX, compassY, compassZ)
        logger.info("Iteration {:04d} done".format(counter))
        counter +=1 
        laststep = step
        step = (currentTime - startTime).seconds
        if step != laststep:
            printProgressBar(step, runningTime, prefix = '  Progress:', suffix = 'Complete', length = 40)

    except Exception as e:
        logger.error(f'{e.__class__.__name__}: {e})')
        with open(errorfile, 'w') as f:
            f.write('Mission error: ' + str(e))


print("  Mission ended at:        {}".format(currentTime))
print("  End transmission.")
