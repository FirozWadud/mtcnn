import threading
import queue
import mtcnn
import cv2

def detect_faces(frame_queue, results_queue, conf_t):
    face_detector = mtcnn.MTCNN()
    while True:
        frame = frame_queue.get()
        if frame is None:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detector.detect_faces(frame_rgb)
        results_queue.put(results)

vc = cv2.VideoCapture("rtsp://admin:admin123@192.168.0.150:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif")
frame_queue = queue.Queue(maxsize=1)
results_queue = queue.Queue(maxsize=1)
conf_t = 0.99

face_thread = threading.Thread(target=detect_faces, args=(frame_queue, results_queue, conf_t))
face_thread.start()

while vc.isOpened():
    ret, frame = vc.read()
    if not ret:
        print(':(')
        break
    if frame_queue.full():
        frame_queue.get()
    frame_queue.put(frame)

    if not results_queue.empty():
        results = results_queue.get()
        for res in results:
            x1, y1, width, height = res['box']
            x1, y1 = abs(x1), abs(y1)
            x2, y2 = x1 + width, y1 + height

            confidence = res['confidence']
            if confidence < conf_t:
                continue
            key_points = res['keypoints'].values()

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), thickness=2)
            cv2.putText(frame, f'conf: {confidence:.3f}', (x1, y1), cv2.FONT_ITALIC, 1, (0, 0, 255), 1)

            for point in key_points:
                cv2.circle(frame, point, 5, (0, 255, 0), thickness=-1)

    cv2.imshow('friends', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

frame_queue.put(None)
face_thread.join()
vc.release()
cv2.destroyAllWindows()