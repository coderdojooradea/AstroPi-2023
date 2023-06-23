from keras.models import load_model  # TensorFlow is required for Keras to work
from PIL import Image, ImageOps  # Install pillow instead of PIL
import numpy as np
import csv
import os

# Disable scientific notation for clarity
np.set_printoptions(suppress=True)

# Load the model
model = load_model("keras_Model.h5", compile=False)

# Load the labels
class_names = open("labels.txt", "r").readlines()

# Create the array of the right shape to feed into the keras model
# The 'length' or number of images you can put into the array is
# determined by the first position in the shape tuple, in this case 1
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

csvfile = open('daynight.csv', 'w', newline='')
fieldnames = ['file_name', 'class', 'confidence']
writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
writer.writeheader()


def classify(path, img):
    image = Image.open(path + '/' + img).convert("RGB")

    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)

    image_array = np.asarray(image)

    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

    data[0] = normalized_image_array

    prediction = model.predict(data)
    index = np.argmax(prediction)
    class_name = class_names[index]
    class_name=class_name[:-1]
    confidence_score = prediction[0][index]

    print("Class:", class_name[2:])
    print("Confidence Score:", confidence_score)
    writer.writerow({'file_name': img, 'class': class_name[2:], 'confidence': confidence_score})


path = 'CDOSR/Images/02_May_2023_04h13m06s'

for file in os.listdir(path):
    classify(path, file)
