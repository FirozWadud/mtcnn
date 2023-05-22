import time
import os
import sys
import av
import mtcnn
import numpy as np
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class FaceDetectionThread(QThread):

    faces_detected = pyqtSignal(list)

    def __init__(self, parent=None):
        super(FaceDetectionThread, self).__init__(parent)
        self.frame = None
        self.face_detector = mtcnn.MTCNN()
        self.conf_t = 0.99

    def run(self):
        while True:
            if self.frame is not None:
                results = self.face_detector.detect_faces(self.frame)
                self.faces_detected.emit(results)
                self.frame = None


class VideoWindow(QMainWindow):
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)

        self.init_face_detection_thread()
        self.init_video_container()
        self.init_label()

        self.frame_count = 0
        self.start_time = time.time()
        self.current_faces = []
        self.target_fps = 30
        self.process_video()

    def init_face_detection_thread(self):
        self.face_detection_thread = FaceDetectionThread()
        self.face_detection_thread.faces_detected.connect(self.update_faces)
        self.face_detection_thread.start()

    def init_video_container(self):
        self.container = av.open(
            "rtsp://admin:admin123@192.168.0.150:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",
            options={'buffer_size': '200000'})
        print("Container opened.")

    def init_label(self):
        self.label = QLabel(self)
        self.setCentralWidget(self.label)

    def update_faces(self, faces):
        self.current_faces = faces

    def process_video(self):
        while True:
            start_time = time.time()

            frame_av = next(self.container.decode(video=0))
            frame = np.array(frame_av.to_image())
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if self.frame_count % 3 == 0:
                self.face_detection_thread.frame = frame_rgb.copy()

            self.update_frame(frame_rgb)

            elapsed_time = time.time() - start_time
            sleep_time = max(1 / self.target_fps - elapsed_time, 0)
            time.sleep(sleep_time)
            self.frame_count += 1

    def update_frame(self, frame_rgb):
        print("yes2")
        if self.current_faces:
            frame_rgb = self.resize_frame(frame_rgb)
            self.draw_faces(frame_rgb)

        self.show_frame(frame_rgb)

    def resize_frame(self, frame):
        scale_percent = 50
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

    def draw_faces(self, frame):
        print("yes1")
        for res in self.current_faces:
            x1, y1, width, height = res['box']
            x1, y1 = abs(x1), abs(y1)
            x2, y2 = x1 + width, y1 + height

            confidence = res['confidence']
            if confidence < self.face_detection_thread.conf_t:
                continue
            key_points = res['keypoints'].values()

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), thickness=2)
            cv2.putText(frame, f'conf: {confidence:.3f}', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            for point in key_points:
                cv2.circle(frame, point, 5, (0, 255, 0), thickness=-1)

    def show_frame(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = channel * width
        qimage = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qimage))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = VideoWindow()
    main_win.show()
    sys.exit(app.exec_())
