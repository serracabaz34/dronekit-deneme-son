# camera_service.py
import cv2
import os
import time
import threading
from flask import Flask, Response

# =============================
# WINDOWS DOSYA YOLLARI
# =============================
FLAG_PATH  = r"C:\Users\serra\OneDrive\Masaüstü\record_flag.txt"
VIDEO_PATH = r"C:\Users\serra\OneDrive\Masaüstü\ucus_kaydi.mp4"

CAM_INDEX = 0
FPS = 20

app = Flask(__name__)

recording = False
cap = None
out = None
last_frame = None
lock = threading.Lock()


def camera_loop():
    """Eski kamera kodunun aynısı + last_frame güncellemesi"""
    global recording, cap, out, last_frame

    print("Kamera servisi hazır...")
    print("Canlı yayın: http://127.0.0.1:8080/video")

    while True:
        flag_exists = os.path.exists(FLAG_PATH)

        # =============================
        # KAYIT BAŞLAT
        # =============================
        if flag_exists and not recording:
            print("Kayıt başladı... Kamera açılıyor")

            cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)  # Windows için hızlı açılır

            if not cap.isOpened():
                print("Kamera açılamadı!")
                time.sleep(1)
                continue

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(VIDEO_PATH, fourcc, float(FPS), (width, height))

            recording = True

        # =============================
        # FRAME OKU / YAYINLA / KAYDET
        # =============================
        if cap is not None:
            ret, frame = cap.read()
            if ret:
                # arayüz için son frame'i sakla
                with lock:
                    last_frame = frame.copy()

                # kayıt açıksa dosyaya yaz
                if recording and out is not None:
                    out.write(frame)

        # =============================
        # KAYIT DURDUR
        # =============================
        if (not flag_exists) and recording:
            print("Kayıt durdu... Kamera kapatılıyor")
            recording = False

            if cap is not None:
                cap.release()
                cap = None

            if out is not None:
                out.release()
                out = None

            cv2.destroyAllWindows()
            print("Video dosyası kapatıldı")

        time.sleep(0.05)


def mjpeg_generator():
    """Flask /video endpoint'i için MJPEG stream"""
    global last_frame
    while True:
        with lock:
            frame = None if last_frame is None else last_frame.copy()

        if frame is None:
            time.sleep(0.02)
            continue

        ok, jpeg = cv2.imencode(".jpg", frame)
        if not ok:
            time.sleep(0.02)
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")

        time.sleep(1.0 / max(1, FPS))


@app.route("/video")
def video():
    return Response(mjpeg_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    # Kamera döngüsünü ayrı thread'de başlat
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()

    # HTTP yayın
    app.run(host="127.0.0.1", port=8080, threaded=True)