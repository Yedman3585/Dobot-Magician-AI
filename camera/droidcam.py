import cv2
import time
import threading
from typing import Optional, Tuple

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

            print(f"[DroidCam] connecting  {self.url}")
            self.cap = cv2.VideoCapture(self.url)

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

            ret, test = self.cap.read()
            if ret:
                print(f"[DroidCam] success, quality: {test.shape[1]}×{test.shape[0]}")
                return True
            else:
                print("[DroidCam] NO ")
                return False
        except Exception as e:
            print(f"[DroidCam] error: {e}")
            return False

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        time.sleep(1)

    def _update(self):
        while self.running:
            if not self.cap or not self.cap.isOpened():
                print("[DroidCam] reconnection ")
                time.sleep(2)
                self._connect()
                continue

            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
            else:
                print("[DroidCam] reconnection...")
                self.cap.release()
                self.cap = None
                time.sleep(2)

    def read(self) -> Tuple[bool, Optional[cv2.Mat]]:
        if self.frame is None:
            return False, None
        return True, self.frame.copy()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[DroidCam] stop")

    def is_opened(self) -> bool:
        return self.cap is not None and self.cap.isOpened()


if __name__ == "__main__":
    cam = DroidCam(
        url="http://192.168.178.112:4747/video",
        width=600,
        height=480,
        fps=30,
        buffer_size=1
    )
    cam.start()

    try:
        while True:
            ret, frame = cam.read()
            if ret:
                cv2.putText(frame, "DroidCam OK", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow("DroidCam → OpenCV", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cam.stop()