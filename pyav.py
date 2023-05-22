import sys
import av
import cv2
from mtcnn import MTCNN


from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QGridLayout, QScrollArea, QSizePolicy
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPalette
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QEvent, QObject, QRect
from PyQt5 import QtCore


class CaptureIpCameraFramesWorker(QThread):


    # Signal emitted when a new image or a new frame is ready.
    ImageUpdated = pyqtSignal(QImage)

    def __init__(self, url):
        super().__init__()
        self.detector = MTCNN()
        self.url = url
        self.__thread_active = True
        self.fps = 0
        self.__thread_pause = False

    def run(self):
        container = av.open(self.url)
        stream = container.streams.video[0]

        while self.__thread_active:
            for packet in container.demux(stream):
                for frame in packet.decode():
                    frame = frame.to_rgb().to_ndarray()
                    img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                    qt_rgb_image_scaled = img.scaled(1280, 720, Qt.KeepAspectRatio)  # 720p

                    # detections = self.detector.detect_faces(framex)
                    # for detection in detections:
                    #     x, y, w, h = detection['box']
                    #     cv2.rectangle(framex, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    # #img = QImage(qt_rgb_image_scaled, qt_rgb_image_scaled.shape[1], qt_rgb_image_scaled.shape[0], QImage.Format_RGB888)
                    # img = QImage(framex, framex.shape[1], framex.shape[0], QImage.Format_RGB888)

                    self.ImageUpdated.emit(qt_rgb_image_scaled)

                    if not self.__thread_active:
                        break

                if not self.__thread_active:
                    break

        container.close()

    def stop(self):
        self.__thread_active = False


class CameraWidget(QWidget):
    def __init__(self, url):
        super().__init__()

        self.camera_label = QLabel(self)
        self.camera_label.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.camera_label.setScaledContents(True)
        self.camera_label.setObjectName("Camera")
        self.camera_label.installEventFilter(self)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.camera_label)

        self.setLayout(QGridLayout())
        self.layout().addWidget(self.scroll_area)

        self.worker = CaptureIpCameraFramesWorker(url)
        self.worker.ImageUpdated.connect(self.update_image)
        self.worker.start()

    def __del__(self):
        self.worker.stop()
        self.worker.wait()

    def update_image(self, frame):
        self.camera_label.setPixmap(QPixmap.fromImage(frame))

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonDblClick:
            if self.parent().maximized_camera:
                self.parent().maximized_camera.scroll_area.show()
                self.parent().maximized_camera = None
            else:
                self.parent().maximized_camera = self
                self.parent().layout().addWidget(self, 0, 0, 2, 2)
                self.scroll_area.hide()

            return True

        return super().eventFilter(source, event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super(MainWindow, self).__init__()

        self.urls = [
            "rtsp://admin:admin123@192.168.0.21:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",
            "rtsp://admin:admin123@192.168.0.150:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",
            "rtsp://admin:admin123@192.168.0.21:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",
            "rtsp://admin:admin123@192.168.0.21:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",
            "rtsp://admin:admin123@192.168.0.150:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",
        ]

        self.cameras = []
        self.camera_widgets = []
        self.camera_states = {}
        self.camera_workers = []

        for i in range(len(self.urls)):
            camera = QLabel()
            camera.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            camera.setScaledContents(True)
            camera.installEventFilter(self)
            camera.setObjectName(f"Camera_{i + 1}")
            self.cameras.append(camera)
            self.camera_states[f"Camera_{i + 1}"] = "Normal"

            scroll_area = QScrollArea()
            scroll_area.setBackgroundRole(QPalette.Dark)
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(camera)
            self.camera_widgets.append(scroll_area)

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(self.camera_widgets[0], 0, 0)
        grid_layout.addWidget(self.camera_widgets[1], 0, 1)
        grid_layout.addWidget(self.camera_widgets[2], 1, 0)
        grid_layout.addWidget(self.camera_widgets[3], 1, 1)

        self.widget = QWidget(self)
        self.widget.setLayout(grid_layout)
        self.setCentralWidget(self.widget)

        for url, camera in zip(self.urls, self.cameras):
            worker = CaptureIpCameraFramesWorker(url)
            worker.ImageUpdated.connect(
                lambda image, camera=camera: self.ShowCamera(image, camera))
            worker.start()
            self.camera_workers.append(worker)

        # Connect the aboutToQuit signal to stop the threads
        QApplication.instance().aboutToQuit.connect(self.stop_workers)

    def stop_workers(self):
        for worker in self.camera_workers:
            worker.stop()
            worker.wait()

        self.__SetupUI()

    def __SetupUI(self) -> None:
        self.setMinimumSize(800, 600)
        self.showMaximized()
        self.setStyleSheet("QMainWindow {background: 'black';}")
        self.setWindowIcon(QIcon(QPixmap("camera_2.png")))
        self.setWindowTitle("IP Camera System")

    @QtCore.pyqtSlot()
    def ShowCamera(self, frame: QImage, camera: QLabel) -> None:
        camera.setPixmap(QPixmap.fromImage(frame))

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            for i, camera_widget in enumerate(self.camera_widgets):
                if source.objectName() == f"Camera_{i + 1}":
                    if self.camera_states[f"Camera_{i + 1}"] == "Normal":
                        for widget in self.camera_widgets:
                            if widget != camera_widget:
                                widget.hide()
                        self.camera_states[f"Camera_{i + 1}"] = "Maximized"
                    else:
                        for widget in self.camera_widgets:
                            widget.show()
                        self.camera_states[f"Camera_{i + 1}"] = "Normal"
                    return True

        return super(MainWindow, self).eventFilter(source, event)

    def closeEvent(self, event) -> None:
        for widget in self.camera_widgets:
            if widget.widget():
                widget.widget().stop()
                widget.widget().wait()
        event.accept()


def main() -> None:
    # Create a QApplication object.
    app = QApplication(sys.argv)
    # Create an instance of the class MainWindow.
    window = MainWindow()
    # Show the window.
    window.show()
    # Start Qt event loop.
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
