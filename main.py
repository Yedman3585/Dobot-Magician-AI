import cv2
from camera.droidcam import DroidCam
from utils import constants

W, H = 800, 600

def main():

    cam = DroidCam(
        url="http://192.168.178.112:4747/video",
        width=W, height=H, fps=30
    )
    cam.start()

    try:
        while True:
            ret, frame = cam.read()
            if ret:

                # draw_detection_area(frame, W, H)
                frames(frame, W, H)

                # 4. Обработка ИИ (будет добавлено позже)
                # objects = detector.detect(frame)

                cv2.imshow("Main Sorting Station", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cam.stop()


def frames(frame, W, H):
    zones = {
        'plastic': ( 80, 235, (255,0,251) ) ,
        'paper' : (236, 235,(255,240,0)),
        'glass' : (392, 235, (110, 191 , 255)),
        'metall' : (550, 235,  (117,117,117 ))
    }

    for label, (cx, cy, color) in zones.items():
        cv2.rectangle(frame, (cx - 40, cy - 40), (cx + 40, cy + 40), color, 3)
        cv2.putText(frame, label.upper(), (cx - 35, cy + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)



if __name__ == "__main__":
    main()

