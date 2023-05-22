import cv2 as cv
import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from mtcnn.mtcnn import MTCNN
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

img = cv.imread("dataset/person1_1.png")

# check if image was successfully read
if img is None:
    print('Could not open or find the image')
else:
    # opencv BGR channel format and plt reads images as RGB channel format
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    plt.imshow(img)  # RGB


detector = MTCNN()
results = detector.detect_faces(img)
x,y,w,h = results[0]['box']
img = cv.rectangle(img, (x,y), (x+w, y+h), (0,0,255), 30)
plt.imshow(img)
plt.show()
