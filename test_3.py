import cv2
import mtcnn
import concurrent.futures
import multiprocessing
import queue
import time

def decode_stream(vc, frame_queue):
    while vc.isOpened():
        ret, frame = vc.read()
        if not ret:
            print(':(')
            break
        if not frame_queue.empty():
            try:
                frame_queue.get_nowait()   # discard the previous frame
            except queue.Empty:
                pass
        frame_queue.put(frame)

def detect_faces(frame_queue, results_queue, conf_t):
    face_detector = mtcnn.MTCNN()
    while True:
        frame = frame_queue.get()
        if frame is None:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detector.detect_faces(frame_rgb)
        results_queue.put((frame, results))

def print_fps(start_time, frame_count):
    elapsed_time = time.time() - start_time
    fps = frame_count / elapsed_time
    print(f"FPS: {fps:.2f}")

if __name__ == "__main__":
    vc = cv2.VideoCapture("rtsp://admin:admin123@192.168.0.150:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif")
    frame_queue = queue.Queue(maxsize=2)
    results_queue = queue.Queue(maxsize=1)
    conf_t = 0.99

    frame_count = 0
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(decode_stream, vc, frame_queue)
        executor.submit(detect_faces, frame_queue, results_queue, conf_t)

        while vc.isOpened():
            if not results_queue.empty():
                frame, results = results_queue.get()
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

                frame_count += 1

        frame_queue.put(None)
        vc.release()
        cv2.destroyAllWindows()

    print_fps(start_time, frame_count)
