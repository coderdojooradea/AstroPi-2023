import cv2
from exif import Image
from datetime import datetime
import math
import json

path = 'CDOSR/Images/02_May_2023_04h13m06s/'


def read_image(image):
    img = cv2.imread(path + image, cv2.IMREAD_COLOR)
    return img


def get_time(image):
    with open(path + image, 'rb') as image_file:
        img = Image(image_file)
        time_str = img.get("datetime_original")
        time = datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
    return time


def calculate_features(image1, image2, feature_number):
    orb = cv2.ORB_create(nfeatures=feature_number)
    keypoints_1, descriptors_1 = orb.detectAndCompute(image1, None)
    keypoints_2, descriptors_2 = orb.detectAndCompute(image2, None)
    return keypoints_1, keypoints_2, descriptors_1, descriptors_2


def calculate_matches(descriptors_1, descriptors_2):
    brute_force = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = brute_force.match(descriptors_1, descriptors_2)
    matches = sorted(matches, key=lambda x: x.distance)
    return matches


def display_matches(image1, keypoints_1, image2, keypoints_2, matches):
    match_img = cv2.drawMatches(image1, keypoints_1, image2, keypoints_2, matches[:100], None)
    resize = cv2.resize(match_img, (1014, 380), interpolation=cv2.INTER_AREA)
    cv2.imshow('matches', resize)
    cv2.waitKey(0)
    cv2.destroyWindow('matches')


def matching_coordinates(keypoints_1, keypoints_2, matches):
    coordinates_1 = []
    coordinates_2 = []
    for match in matches:
        image_1_idx = match.queryIdx
        image_2_idx = match.trainIdx
        (x1, y1) = keypoints_1[image_1_idx].pt
        (x2, y2) = keypoints_2[image_2_idx].pt
        coordinates_1.append((x1, y1))
        coordinates_2.append((x2, y2))
    return coordinates_1, coordinates_2


def calculate_distance(coordinates_1, coordinates_2):
    mean = 0
    merged_coordinates = list(zip(coordinates_1, coordinates_2))
    for coordinate in merged_coordinates:
        x_difference = coordinate[0][0] - coordinate[1][0]
        y_difference = coordinate[0][1] - coordinate[1][1]
        distance = math.hypot(x_difference, y_difference)
        mean = mean + distance
    return mean / len(merged_coordinates)


def get_speed(pixel_distance, time_difference):
    GSD = 24857.015
    distance = pixel_distance * GSD / 100000
    speed = distance / time_difference.seconds
    return speed


def main():
    image1 = input("First image  ")
    image2 = input("Second image  ")
    img1 = read_image(image1)
    img2 = read_image(image2)

    time_1 = get_time(image1)
    time_2 = get_time(image2)
    time_difference = time_2 - time_1

    keypoints_1, keypoints_2, descriptors_1, descriptors_2 = calculate_features(img1, img2, 1000)
    matches = calculate_matches(descriptors_1, descriptors_2)

    print('Press any key to close the window')
    display_matches(img1, keypoints_1, img2, keypoints_2, matches)

    coordinates_1, coordinates_2 = matching_coordinates(keypoints_1, keypoints_2, matches)
    pixel_distance = calculate_distance(coordinates_1, coordinates_2)
    iss_speed = get_speed(pixel_distance, time_difference)
    print('{} km/s'.format(round(iss_speed, 2)))
    with open('parameters.json') as json_file:
        data = json.load(json_file)
        data['velocity'] = iss_speed
    with open('parameters.json', 'w') as json_file:
        json.dump(data, json_file)


if __name__ == '__main__':
    main()
