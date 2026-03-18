import cv2
import time
import threading
from typing import Optional, Tuple
import mediapipe as mp
import numpy as np


class DroidCam:
    def __init__(
            self,
            url: str = "http://192.168.178.112:4747/video",
            width: int = 640,
            height: int = 480,
            fps: int = 30,
            buffer_size: int = 1
    ):
        self.url = url
        self.width = width
        self.height = height
        self.fps = fps
        self.buffer_size = buffer_size

        self.cap: Optional[cv2.VideoCapture] = None
        self.frame = None
        self.running = False
        self.thread = None

        self._connect()

    def _connect(self) -> bool:
        try:
            if self.cap is not None:
                self.cap.release()

            print(f"[DroidCam] Connecting to {self.url}")
            self.cap = cv2.VideoCapture(self.url)

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

            ret, test = self.cap.read()
            if ret:
                print(f"[DroidCam] Connected successfully — frame size: {test.shape[1]}×{test.shape[0]}")
                return True
            else:
                print("[DroidCam] Failed to read test frame")
                return False

        except Exception as e:
            print(f"[DroidCam] Connection error: {e}")
            return False

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        time.sleep(0.8)  # give thread time to stabilize

    def _update(self):
        while self.running:
            if not self.cap or not self.cap.isOpened():
                print("[DroidCam] Reconnecting...")
                time.sleep(1.5)
                self._connect()
                continue

            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
            else:
                print("[DroidCam] Read failed → reconnecting...")
                self.cap.release()
                self.cap = None
                time.sleep(2)

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self.frame is None:
            return False, None
        return True, self.frame.copy()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.5)
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[DroidCam] Stopped")

    def is_opened(self) -> bool:
        return self.cap is not None and self.cap.isOpened()


mp_objectron = mp.solutions.objectron
mp_drawing = mp.solutions.drawing_utils

SELECTED_CATEGORY = "cup"  # ← change to "chair", "sneakers", "camera" etc.

MODEL_PATHS = {
    "sneakers": "mediapipe/modules/objectron/object_detection_3d_sneakers.tflite",
    "chair": "mediapipe/modules/objectron/object_detection_3d_chair.tflite",
    "cup": "mediapipe/modules/objectron/object_detection_3d_cup.tflite",
    "camera": "mediapipe/modules/objectron/object_detection_3d_camera.tflite",
}

if SELECTED_CATEGORY not in MODEL_PATHS:
    raise ValueError(f"Unknown category. Choose from: {list(MODEL_PATHS.keys())}")


def main():
    cam = DroidCam(
        url="http://192.168.178.112:4747/video",
        width=640,
        height=480,
        fps=30,
        buffer_size=1
    )

    cam.start()

    # Objectron config
    objectron = mp_objectron.Objectron(
        static_image_mode=False,
        max_num_objects=5,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.4,
        model_name=SELECTED_CATEGORY,
    )

    print(f"[Objectron] Initialized for category: {SELECTED_CATEGORY.upper()}")

    try:
        while True:
            ret, frame = cam.read()
            if not ret:
                time.sleep(0.05)
                continue

            # RGB for MediaPipe
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_rgb.flags.writeable = False

            # Process with Objectron
            results = objectron.process(image_rgb)

            image_rgb.flags.writeable = True
            annotated = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

            if results.detected_objects:
                for detected_object in results.detected_objects:
                    mp_drawing.draw_landmarks(
                        annotated,
                        detected_object.landmarks_2d,
                        mp_objectron.BOX_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
                        mp_drawing.DrawingSpec(color=(255, 0, 255), circle_radius=4)
                    )

                    mp_drawing.draw_axis(
                        annotated,
                        detected_object.rotation,
                        detected_object.translation,
                        size=0.1  # scale of axis visualization
                    )

                    translation = detected_object.translation  # [tx, ty, tz]
                    rotation = detected_object.rotation  # 3×3 rotation matrix

                    print(f"[3D] Category: {SELECTED_CATEGORY} | "
                          f"Translation: {translation} | "
                          f"Rotation det: {np.linalg.det(rotation):.4f}")

            # FPS & status overlay
            fps_text = f"FPS: {1 / (time.time() - start_time + 1e-6):.1f}" if 'start_time' in globals() else "FPS: --"
            cv2.putText(annotated, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.putText(annotated, f"Objectron ({SELECTED_CATEGORY})", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 180, 0), 2)

            cv2.imshow("DroidCam + MediaPipe Objectron 3D", annotated)

            start_time = time.time()  # for next FPS

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        cam.stop()
        objectron.close()
        cv2.destroyAllWindows()
        print("[Main] Clean shutdown")


if __name__ == "__main__":
    main()