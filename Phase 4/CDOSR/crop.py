from PIL import Image
import os

path = 'CDOSR/Images/02_May_2023_04h13m06s'
path_cropped = 'CDOSR/Images/Cropped'

for Img in os.listdir(path):
    BaseImg = Image.open(path + '/' + Img)
    CroppedImg = BaseImg.crop((0, 832, 575, 1407))
    CroppedImg.save(path_cropped + '/' + Img)
