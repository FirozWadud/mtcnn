import time
import sys
import av
import mtcnn
import numpy as np
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class VideoWindow(QMainWindow):
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)

        self.face_detector = mtcnn.MTCNN()
        self.conf_t = 0.99

        self.container = av.open("rtsp://192.168.1.130:8080/h264_ulaw.sdp",options={'buffer_size': '500000'})

        print("Container opened.")

        self.label = QLabel(self)
        self.setCentralWidget(self.label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        self.frame_count = 0
        self.start_time = time.time()

    def calculate_fps(self):
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        fps = self.frame_count / elapsed_time
        return fps

    def update_frame(self, ):
        fps = self.calculate_fps()
        print("FPS: ", fps)

        frame_av = next(self.container.decode(video=0))
        frame = np.array(frame_av.to_image())

        # 1. Reduce frame resolution
        # scale_percent = 50  # percentage of original size
        # width = int(frame.shape[1] * scale_percent / 100)
        # height = int(frame.shape[0] * scale_percent / 100)
        # dim = (width, height)
        # frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        #
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 2. Process every nth frame
        n = 10
        if self.frame_count % n == 0:
            results = self.face_detector.detect_faces(frame_rgb)
        else:
            results = []

        for res in results:
            x1, y1, width, height = res['box']
            x1, y1 = abs(x1), abs(y1)
            x2, y2 = x1 + width, y1 + height

            confidence = res['confidence']
            if confidence < self.conf_t:
                continue
            key_points = res['keypoints'].values()

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), thickness=2)
            cv2.putText(frame, f'conf: {confidence:.3f}', (x1, y1), cv2.FONT_ITALIC, 1, (0, 0, 255), 1)

            for point in key_points:
                cv2.circle(frame, point, 5, (0, 255, 0), thickness=-1)

        cv2.putText(frame, f'FPS: {fps:.2f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        height, width, channel = frame.shape
        bytes_per_line = channel * width
        qimage = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

        self.label.setPixmap(QPixmap.fromImage(qimage))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = VideoWindow()
    main_win.show()
    sys.exit(app.exec_())
