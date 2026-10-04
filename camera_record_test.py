import cv2
import subprocess
import time

# ---------- Ayarlar ----------
camera_index = 0
avi_file = "test_record.avi"
mp4_file = "test_record.mp4"
fps = 20
width = 640
height = 480
record_seconds = 10
# -----------------------------

cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("❌ Kamera açılamadı.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

fourcc = cv2.VideoWriter_fourcc(*"MJPG")
out = cv2.VideoWriter(avi_file, fourcc, fps, (width, height))

print("⏺ Kayıt başladı...")

start_time = time.time()

while time.time() - start_time < record_seconds:
    ret, frame = cap.read()
    if not ret:
        break

    out.write(frame)
    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

print("⏹ Kayıt bitti.")

cap.release()
out.release()
cv2.destroyAllWindows()

# -------- FFmpeg ile MP4'e çevir --------
print("🔄 MP4'e dönüştürülüyor...")

ffmpeg_path = r"C:\ffmpeg\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"

subprocess.run([
    ffmpeg_path,
    "-y",
    "-i", avi_file,
    "-vcodec", "libx264",
    "-crf", "23",
    mp4_file
], check=True)

print("✅ MP4 oluşturuldu:", mp4_file)