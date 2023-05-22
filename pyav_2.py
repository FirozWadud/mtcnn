import av
import cv2
import numpy as np
from mtcnn.mtcnn import MTCNN
from concurrent.futures import ThreadPoolExecutor
import time
from PyQt5 import QtWidgets, QtGui

# Custom QLabel to display video stream with face detection and FPS
class VideoStreamWindow(QtWidgets.QLabel):
    def __init__(self, rtsp_link, index, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Face Detection - {index}")
        self.rtsp_link = rtsp_link
        self.detector = MTCNN()
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()

    # Function to process frames and detect faces using MTCNN
    def process_frame(self, frame):
        faces = self.detector.detect_faces(frame)
        for face in faces:
            x, y, w, h = face['box']
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        return frame

    # Function to update the QLabel with a new frame, process it, and display the FPS
    def update_image(self, frame):
        self.frame_count += 1
        print(f"Processing frame {self.frame_count}")
        elapsed_time = time.time() - self.start_time
        self.fps = self.frame_count / elapsed_time

        processed_frame = self.process_frame(frame)
        height, width, channel = processed_frame.shape
        bytes_per_line = 3 * width
        qimage = QtGui.QImage(processed_frame.data, width, height, bytes_per_line,
                              QtGui.QImage.Format_RGB888).rgbSwapped()

        painter = QtGui.QPainter(qimage)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 255), 2))
        painter.setFont(QtGui.QFont("Arial", 20))
        painter.drawText(10, 30, f"FPS: {self.fps:.2f}")
        painter.end()

        pixmap = QtGui.QPixmap.fromImage(qimage)
        self.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())  # Resize the window


# Function to decode RTSP stream and invoke a callback with the decoded frame
def decode_stream(url, callback):
    try:
        container = av.open(url)
        video_stream = next(s for s in container.streams if s.type == 'video')
        for frame in container.decode(video_stream):
            frame_image = cv2.cvtColor(np.array(frame.to_image()), cv2.COLOR_RGB2BGR)
            print(f"Received frame {frame.pts} with size {frame_image.shape}")
            callback(frame_image)
    except av.AVError as e:
        print(f"Error opening RTSP stream: {e}")
        return


# Function to process an RTSP link using a VideoStreamWindow instance
def process_rtsp_link(index, link):
    window = VideoStreamWindow(link, index)
    window.show()

    def update_image_wrapper(frame):
        window.update_image(frame)

    decode_stream(link, update_image_wrapper)
    return window

def main():
    rtsp_links = [
        "rtsp://admin:admin123@192.168.0.150:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
        # Add more links as needed
    ]

    # Initialize PyQt5 application
    app = QtWidgets.QApplication([])
    windows = []

    # Use ThreadPoolExecutor to process each RTSP link concurrently
    with ThreadPoolExecutor(max_workers=len(rtsp_links) * 2) as executor:
        future_windows = [executor.submit(process_rtsp_link, i, link) for i, link in enumerate(rtsp_links)]
        windows = [future.result() for future in future_windows]

    # Run the PyQt5 application event loop
    app.exec_()

if __name__ == "__main__":
    main()
