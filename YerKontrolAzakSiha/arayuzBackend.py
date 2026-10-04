
############## wsl de çalışan kod

from PyQt5.QtWidgets import QMainWindow, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer, QUrl, Qt
from dronekit import connect
from sihaArayuz import Ui_MainWindow as SihaUI
from Uydu_Hud_Ekrani import Ui_MainWindow as UyduHudUI
from mod_ekrani import Ui_mod_ekrani
from flight_controller import FlightController
import sys, time, os
import cv2
from PyQt5.QtGui import QImage, QPixmap, QFont
from server_service import ServerWorker
from hud_widget import HudWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sys, traceback, faulthandler
import math
from jetson_mavlink_bridge import JetsonMavlinkWorker
import json

_orig_stderr = sys.stderr  # gerçek konsolu sakla

def _crash_logger(exc_type, exc_value, exc_tb):
    with open("crash_log.txt", "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    traceback.print_exception(exc_type, exc_value, exc_tb, file=_orig_stderr)

sys.excepthook = _crash_logger
faulthandler.enable()

#GÖSTERGE WIDGET'LARI (sadece ekranda görünmesi için)
from gostergeler import (
    AirspeedGauge, AltimeterGauge, VerticalSpeedGauge,
    AttitudeIndicator, CompassIndicator, TurnCoordinatorIndicator
)

# ------------------- DroneKit connect thread -------------------
class VehicleConnector(QThread):
    connected = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, conn_str: str):
        super().__init__()
        self.conn_str = conn_str

    def run(self):
        try:
            print("Bağlanılıyor...", self.conn_str)
            vehicle = connect(self.conn_str, wait_ready=True)
            print("Bağlantı başarılı.")
            self.connected.emit(vehicle)
        except Exception as e:
            self.failed.emit(str(e))


# ------------------- Telemetry thread -------------------
class TelemetryReader(QThread):
    data_received = pyqtSignal(dict)
    map_signal = pyqtSignal(float, float, float)

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle
        self.running = True

    def run(self):
        while self.running:
            try:
                loc = self.vehicle.location.global_relative_frame
                att = self.vehicle.attitude

                # ---- Batarya (DroneKit: vehicle.battery.level genelde 0-100) ----
                batt_level = None
                try:
                    if self.vehicle.battery and self.vehicle.battery.level is not None:
                        batt_level = int(self.vehicle.battery.level)
                except Exception:
                    batt_level = None

                # ---- Sinyal (RADIO_STATUS -> rssi 0..255) ----
                sig_level = None
                try:
                    msg = self.vehicle._master.recv_match(type="RADIO_STATUS", blocking=False)
                    if msg and hasattr(msg, "rssi") and msg.rssi is not None:
                        sig_level = int(max(0, min(100, (msg.rssi / 255.0) * 100)))
                except Exception:
                    sig_level = None

                iha_yatis = math.degrees(att.roll) if att and att.roll is not None else 0.0
                iha_dikilme = math.degrees(att.pitch) if att and att.pitch is not None else 0.0
                iha_yonelme = float(getattr(self.vehicle, "heading", 0.0) or 0.0)

                telemetry = {
                    "lat": float(loc.lat) if loc and loc.lat is not None else 0.0,
                    "lon": float(loc.lon) if loc and loc.lon is not None else 0.0,
                    "alt": float(loc.alt) if loc and loc.alt is not None else 0.0,
                    "air_speed": float(self.vehicle.airspeed or 0.0),
                    "ground_speed": float(self.vehicle.groundspeed or 0.0),
                    "yaw": iha_yonelme,  # Derece cinsinden yonelme/yaw
                    "pitch": iha_dikilme,  # Derece cinsinden pitch
                    "roll": iha_yatis,  # Derece cinsinden roll
                    "battery": batt_level,
                    "signal": sig_level,
                    "mode": str(self.vehicle.mode.name) if self.vehicle.mode else "UNKNOWN",
                }

                self.data_received.emit(telemetry)
                self.map_signal.emit(telemetry["lat"], telemetry["lon"], iha_yonelme)

            except Exception as e:
                print("Telemetry okuma hatası:", e)

            self.msleep(100)

    def stop(self):
        self.running = False
        self.wait()

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    recording_finished = pyqtSignal(str)   # mp4 yolu
    status = pyqtSignal(str)

    def __init__(self, cam_index=0, ffmpeg_path=None):
        super().__init__()
        self.cam_index = cam_index
        self.running = True

        # ffmpeg
        self.ffmpeg_path = ffmpeg_path

        # recording
        self.is_recording = False
        self.writer = None
        self.avi_path = None
        self.mp4_path = None
        self.record_fps = 25
        self.frame_size = (640, 480)
        self.map_ready = False


        # STREAMING
        self.streaming = False
        self.ffmpeg_process = None
        self.stream_url = None


    def run(self):
        cap = cv2.VideoCapture(self.cam_index)
        if not cap.isOpened():
            self.status.emit(f"Kamera açılamadı! index: {self.cam_index}")
            return

        self.status.emit("Kamera açıldı.")

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])

        while self.running:
            ret, frame = cap.read()
            if not ret:
                self.msleep(10)
                continue

            # Kayıt varsa yaz (AVI MJPG)
            if self.is_recording and self.writer is not None:
                try:
                    self.writer.write(cv2.resize(frame, self.frame_size))
                except Exception as e:
                    self.status.emit(f"Kayıt yazma hatası: {e}")


            # CANLI STREAM (BURAYA)
            if self.streaming and self.ffmpeg_process:
                try:
                    resized = cv2.resize(frame, self.frame_size)
                    self.ffmpeg_process.stdin.write(resized.tobytes())
                except Exception as e:
                    self.status.emit(f"Streaming hata: {e}")


            # UI'ya bas
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.frame_ready.emit(qimg)

            self.msleep(20)

        cap.release()
        self._stop_writer()

    def start_recording(self, base_name="latest", out_dir="records"):
        if self.is_recording:
            self.status.emit("Zaten kayıt yapılıyor.")
            return

        Path(out_dir).mkdir(parents=True, exist_ok=True)

        tarih_str = datetime.now().strftime("%d_%m_%Y")

        formatted_name = f"18_AZAK_SIHA_DGM_TAKIMI_{tarih_str}"  # şimdilik 18 koydum o gün değiştirilecek

        self.avi_path = str(Path(out_dir) / f"{formatted_name}.avi")
        self.mp4_path = str(Path(out_dir) / f"{formatted_name}.mp4")

        # Eski dosyaları sil (üstüne yazma garantisi)
        try:
            if os.path.exists(self.avi_path):
                os.remove(self.avi_path)
            if os.path.exists(self.mp4_path):
                os.remove(self.mp4_path)
        except Exception as e:
            self.status.emit(f"Eski dosya silinemedi: {e}")

        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        self.writer = cv2.VideoWriter(self.avi_path, fourcc, self.record_fps, self.frame_size)
        if not self.writer.isOpened():
            self.writer = None
            self.status.emit("VideoWriter açılamadı. Kayıt başlayamadı.")
            return

        self.is_recording = True
        self.status.emit(f"Kayıt başladı (overwrite): {self.avi_path}")

    def stop_recording(self):
        if not self.is_recording:
            self.status.emit("Kayıt zaten kapalı.")
            return

        self.is_recording = False
        self._stop_writer()
        self.status.emit("Kayıt durdu. MP4'e dönüştürülüyor...")

        # AVI -> MP4 (thread içinde, UI kilitlenmez)
        if self.ffmpeg_path:
            try:
                subprocess.run([
                    self.ffmpeg_path,
                    "-y",
                    "-i", self.avi_path,
                    "-vcodec", "libx264",
                    "-crf", "23",
                    self.mp4_path
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                self.status.emit(f"MP4 hazır: {self.mp4_path}")
                self.recording_finished.emit(self.mp4_path)
            except Exception as e:
                self.status.emit(f"FFmpeg hata: {e}")
        else:
            # ffmpeg yoksa avi path döndür
            self.status.emit("ffmpeg_path yok. AVI kaydedildi.")
            self.recording_finished.emit(self.avi_path)

    def _stop_writer(self):
        if self.writer is not None:
            try:
                self.writer.release()
            except Exception:
                pass
            self.writer = None

    def stop(self):
        self.running = False
        self.wait()

    def start_streaming(self, stream_url):
        if self.streaming:
            self.status.emit("Zaten yayın yapılıyor.")
            return

        self.stream_url = stream_url

        try:
            self.ffmpeg_process = subprocess.Popen([
                self.ffmpeg_path,
                '-y',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', f'{self.frame_size[0]}x{self.frame_size[1]}',
                '-r', str(self.record_fps),
                '-i', '-',
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-tune', 'zerolatency',
                '-f', 'flv',
                stream_url
            ], stdin=subprocess.PIPE)

            self.streaming = True

            # aynı işi print(" Canlı yayın başlatıldı") yapıyor
            # self.status.emit("Canlı yayın başladı")

        except Exception as e:
            self.status.emit(f"Streaming başlatılamadı: {e}")

    def stop_streaming(self):
        if not self.streaming:
            self.status.emit("Yayın zaten kapalı.")
            return

        self.streaming = False

        try:
            if self.ffmpeg_process:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.wait()
        except Exception as e:
            self.status.emit(f"Streaming kapatma hatası: {e}")

        self.ffmpeg_process = None
        # aynısı print("Canlı yayın durduruldu")
        # self.status.emit(" Canlı yayın durdu")


class TakeoffWorker(QThread):
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, flight_controller):
        super().__init__()
        self.flight = flight_controller

    def run(self):
        try:
            self.flight.otonom_kalkis()
            self.finished.emit("Kalkış tamamlandı.")
        except Exception as e:
            self.failed.emit(str(e))

class LandWorker(QThread):
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, flight_controller):
        super().__init__()
        self.flight = flight_controller

    def run(self):
        try:
            # HOME’a planlı iniş (AUTO + LAND)
            self.flight.planli_inis()
            self.finished.emit("Planlı iniş başlatıldı (AUTO).")
        except Exception as e:
            self.failed.emit(str(e))

class StreamRedirect(QObject):
    new_text = pyqtSignal(str)

    def write(self, text):
        self.new_text.emit(str(text))

    def flush(self):
        pass

# ------------------- Main GUI -------------------
class arayuz_backend(QMainWindow):
    sig_init = pyqtSignal(str)
    sig_login = pyqtSignal(str, str)
    sig_logout = pyqtSignal()
    sig_connect = pyqtSignal()
    sig_send_tel = pyqtSignal(dict)
    sig_upload_video_http = pyqtSignal(str)
    # sig_poll_competitors = pyqtSignal()   # yeni eklendi

    def __init__(self):
        super().__init__()
        self.ui = SihaUI()
        self.ui.setupUi(self)

        self.stdout = StreamRedirect()
        self.stdout.new_text.connect(self.append_terminal)
        sys.stdout = self.stdout
        sys.stderr = self.stdout

        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(14)
        self.ui.terminal_view.setFont(font)

        # -------- Kamera canlı izleme (PC kamerası) --------
        if hasattr(self.ui, "kamera"):
            self.ui.kamera.setScaledContents(True)

        ffmpeg_path = r"C:\ffmpeg\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
        self.cam = CameraThread(cam_index=0, ffmpeg_path=ffmpeg_path)
        self.cam.frame_ready.connect(self.on_camera_frame, Qt.UniqueConnection)

        self.cam.status.connect(lambda m: print("[CAM]", m))

        self.cam.start()
        self.start_video_recording()
        # self.cam.status.connect(lambda m: print("[CAM]", m)) ennn yeniiii
        self.cam.recording_finished.connect(self.on_recording_finished)

        # Kamera açıldıktan 20 saniye sonra otomatik kayda başla
        #QTimer.singleShot(20_000, self._auto_start_recording)

        self.last_recorded_video_path = None

        self._prev_alt = None
        self._prev_t = None

        # --- VSI smoothing state ---
        self._vsi_ema = 0.0

        # --- Heading-based turn rate state ---
        self._prev_heading = None
        self._prev_heading_t = None

        # (Opsiyonel) turn rate smoothing
        self._turn_ema = 0.0
        self._slip_ema = 0.0

        self._landing_requested = False


        # -------------------------------------------------
        # GÖSTERGELERİ EKRENDA GÖSTER (SADECE GÖRÜNTÜ)
        # objectName'ler: airspeed_indicator, altimeter_indicator,
        # vertical_speed_indicator, attitude_indicator, compass_indicator,
        # turn_coordinator_indicator
        # -------------------------------------------------

        # Airspeed
        self.airspeed_gauge = AirspeedGauge()
        l1 = QVBoxLayout()
        l1.setContentsMargins(0, 0, 0, 0)
        l1.addWidget(self.airspeed_gauge)
        self.ui.airspeed_indicator.setLayout(l1)

        # Altimeter
        self.altimeter_gauge = AltimeterGauge()
        l2 = QVBoxLayout()
        l2.setContentsMargins(0, 0, 0, 0)
        l2.addWidget(self.altimeter_gauge)
        self.ui.altimeter_indicator.setLayout(l2)

        # Vertical Speed
        self.vsi_gauge = VerticalSpeedGauge()
        l3 = QVBoxLayout()
        l3.setContentsMargins(0, 0, 0, 0)
        l3.addWidget(self.vsi_gauge)
        self.ui.vertical_speed_indicator.setLayout(l3)

        # Attitude
        self.attitude_gauge = AttitudeIndicator()
        l4 = QVBoxLayout()
        l4.setContentsMargins(0, 0, 0, 0)
        l4.addWidget(self.attitude_gauge)
        self.ui.attitude_indicator.setLayout(l4)

        # Compass
        self.compass_gauge = CompassIndicator()
        l5 = QVBoxLayout()
        l5.setContentsMargins(0, 0, 0, 0)
        l5.addWidget(self.compass_gauge)
        self.ui.compass_indicator.setLayout(l5)

        # Turn Coordinator
        self.turn_gauge = TurnCoordinatorIndicator()
        l6 = QVBoxLayout()
        l6.setContentsMargins(0, 0, 0, 0)
        l6.addWidget(self.turn_gauge)
        self.ui.turn_coordinator_indicator.setLayout(l6)

        # -------------------------------------------------
        # Buton bağlantıları (senin kodun aynen)
        # -------------------------------------------------
        self.ui.hud_uydu.clicked.connect(self.open_uydu_hud)
        self.ui.otonom_kalkis.clicked.connect(self.start_takeoff)
        self.ui.otonom_inis.clicked.connect(self.start_land)
        self.ui.mod_butonu.clicked.connect(self.open_mod_window)

        # ----------- DroneKit bağlantı + telemetri thread -----------
        self.vehicle = None
        self.flight = None
        self.reader = None

        self.takeoff_worker = None
        self.land_worker = None

        self._prev_yaw = None
        self._prev_yaw_t = None

        self.last_position = None # yeni eklendi

        self.connector = VehicleConnector("tcp:192.168.1.16:14553")       # tcp:192.168.1.16:14553 efede çalışan ardupilot
        self.connector.connected.connect(self.on_vehicle_connected)
        self.connector.failed.connect(self.on_vehicle_failed)
        self.connector.start()

        # -------------------------
        # SERVER THREAD SETUP
        # -------------------------
        self.server_thread = QThread(self)
        self.server_worker = ServerWorker()
        self.server_worker.moveToThread(self.server_thread)

        # GUI -> Worker (Queued)
        self.sig_init.connect(self.server_worker.init_client, Qt.UniqueConnection)
        self.sig_login.connect(self.server_worker.login, Qt.UniqueConnection)
        self.sig_logout.connect(self.server_worker.logout, Qt.UniqueConnection)
        self.sig_connect.connect(self.server_worker.connect_server, Qt.UniqueConnection)
        self.sig_send_tel.connect(self.server_worker.send_telemetry, Qt.UniqueConnection)
        self.sig_upload_video_http.connect(self.server_worker.upload_video_http, Qt.UniqueConnection)
        # self.sig_poll_competitors.connect(self.server_worker.poll_competitors, Qt.UniqueConnection) #yeni eklendi bu da

        # Worker -> GUI log
        self.server_worker.err.connect(lambda m: print("[SERVER ERR]", m))
        # Worker'dan başarılı yükleme mesajı geldiğinde oturumu kapat
        self.server_worker.ok.connect(self._on_server_ok)
        self.server_worker.competitors.connect(self.on_competitors_received)    #yeni eklendi
        self.server_thread.start()

        # -------------------------
        # TELEMETRY SEND TIMER (5 Hz)
        # -------------------------
        self._last_telemetry = None
        self.telemetry_send_timer = QTimer(self)
        self.telemetry_send_timer.setInterval(1000)  # 1 Hz telemetri veri gönderim sıklığı
        self.telemetry_send_timer.timeout.connect(self._send_telemetry_to_server)

        self.server_connected = False
        self.time_offset = 0.0  # Saniye cinsinden farkı tutacak değişken

        # MAP UPDATE TIMER (5 Hz) güncellllllllll
        self.map_timer = QTimer(self)
        self.map_timer.setInterval(200)  # 5 Hz
        self.map_timer.timeout.connect(self.update_map_safe)
        self.map_timer.start()

        # __init__ içinde:
        self.hss_poll_timer = QTimer(self)
        self.hss_poll_timer.setInterval(5000)  # Veri gelene kadar her 5 saniyede bir istek atar
        self.hss_poll_timer.timeout.connect(self.server_worker.fetch_hss_coordinates)

        # Worker'dan gelen cevabı dinleyecek slot bağlantısı:
        self.server_worker.hss_received.connect(self.on_hss_received)

        # Jetson MAVLink Worker'ını Başlat
        self.mav_worker = JetsonMavlinkWorker(connection_str="tcp:192.168.1.16:14550")

        # Sinyalleri Arayüz Metotlarına Bağla
        self.mav_worker.telemetry_updated.connect(self.update_telemetry_ui)
        self.mav_worker.statustext_received.connect(self.update_status_logs)
        self.mav_worker.connection_changed.connect(self.update_connection_status)

        # Thread'i Çalıştır
        self.mav_worker.start()

        # Buton Bağlantılarını Kur
        self.setup_button_connections()

# bu parça yani
        # -------------------------
        # UI BUTTON CONNECTIONS
        # (objectName'ler birebir aynı olmalı)
        # -------------------------
        try:
            self.ui.sunucuya_giris.clicked.disconnect()
            self.ui.sunucuya_baglan.clicked.disconnect()
            self.ui.sunucudan_cikis.clicked.disconnect()
            self.ui.telemetri_aktarimi.clicked.disconnect()
        except Exception:
            pass  # İlk çalıştırmada kesilecek bağlantı yoksa hatayı yut

        self.ui.sunucuya_giris.clicked.connect(self.on_sunucuya_giris_clicked)
        self.ui.sunucuya_baglan.clicked.connect(self.on_sunucuya_baglan_clicked)
        self.ui.sunucudan_cikis.clicked.connect(self.on_sunucudan_cikis_clicked)
        self.ui.telemetri_aktarimi.clicked.connect(self.on_telemetri_aktarimi_clicked)

        # CANLI YAYIN BUTONLARI
        if hasattr(self.ui, "canli_yayin_baslat"):
            self.ui.canli_yayin_baslat.clicked.connect(self.start_stream)

        if hasattr(self.ui, "canli_yayin_durdur"):
            self.ui.canli_yayin_durdur.clicked.connect(self.stop_stream)

        self.server_connected = False
        self.server_time = None

        self.server_worker.connected_state.connect(self.on_server_connected_state)


        if hasattr(self.ui, "video_yukle"):
            self.ui.video_yukle.clicked.connect(self.on_video_yukle_clicked, Qt.UniqueConnection)

        if hasattr(self.ui, "kayit_baslat"):
            self.ui.kayit_baslat.clicked.connect(self.start_video_recording, Qt.UniqueConnection)

        if hasattr(self.ui, "kayit_durdur"):
            self.ui.kayit_durdur.clicked.connect(self.stop_video_recording, Qt.UniqueConnection)


    def on_vehicle_connected(self, vehicle):
        self.vehicle = vehicle
        self.flight = FlightController(self.vehicle)

        self.reader = TelemetryReader(self.vehicle)
        self.reader.data_received.connect(self.update_ui_safely)
        self.reader.map_signal.connect(self.update_map_position)
        self.reader.start()

    def on_vehicle_failed(self, err):
        print("DroneKit bağlantı hatası:", err)

    def update_ui_safely(self, data: dict):
        self._last_telemetry = data

        if hasattr(self.ui, "air_speed"):
            self.ui.air_speed.setText(f"Air Speed: {data['air_speed']:.2f} m/s")

        if hasattr(self.ui, "ground_speed"):
            self.ui.ground_speed.setText(f"Ground Speed: {data['ground_speed']:.2f} m/s")

        if hasattr(self.ui, "yaw_label"):
            self.ui.yaw_label.setText(f"Yaw: {data['yaw']:.3f}")

        if hasattr(self.ui, "pitch_label"):
            self.ui.pitch_label.setText(f"Pitch: {data['pitch']:.3f}")

        if hasattr(self.ui, "roll_label"):
            self.ui.roll_label.setText(f"Roll: {data['roll']:.3f}")

        if hasattr(self.ui, "altitiude_label"):
            self.ui.altitiude_label.setText(f"Altitude: {data['alt']:.2f} m")

        if hasattr(self.ui, "enlem_label"):
            self.ui.enlem_label.setText(f"Enlem: {data['lat']:.6f}")

        if hasattr(self.ui, "boylam_label"):
            self.ui.boylam_label.setText(f"Boylam: {data['lon']:.6f}")

        if hasattr(self.ui, "irtifa_label"):
            self.ui.irtifa_label.setText(f"İrtifa: {data['alt']:.2f} m")

        if hasattr(self.ui, "batarya_bar") and data.get("battery") is not None:
            try:
                self.ui.batarya_bar.setValue(int(max(0, min(100, data["battery"]))))
            except Exception:
                pass

        if hasattr(self.ui, "sinyal_bar") and data.get("signal") is not None:
            try:
                self.ui.sinyal_bar.setValue(int(max(0, min(100, data["signal"]))))
            except Exception:
                pass

        if hasattr(self.ui, "mod_label"):
            self.ui.mod_label.setText(f"Mod: {data.get('mode', 'UNKNOWN')}")
        # --- Safety check (acil RTL) ---
        try:
            if self.flight:
                self.flight.safety_check(
                    battery_percent=data.get("battery"),
                    signal_percent=data.get("signal")
                )
        except Exception as e:
            print("Safety check error:", e)


        # -----------------------
        # GAUGE GÜNCELLEME
        # -----------------------

        # Airspeed gauge
        try:
            # bazen setValue, bazen setSpeed olabilir
            if hasattr(self.airspeed_gauge, "setValue"):
                self.airspeed_gauge.setValue(data["air_speed"])
            elif hasattr(self.airspeed_gauge, "setSpeed"):
                self.airspeed_gauge.setSpeed(data["air_speed"])
        except Exception as e:
            print("Airspeed gauge update error:", e)

        # Altimeter gauge
        try:
            if hasattr(self.altimeter_gauge, "setAltitude"):
                self.altimeter_gauge.setAltitude(data["alt"])
            elif hasattr(self.altimeter_gauge, "setValue"):
                self.altimeter_gauge.setValue(data["alt"])
        except Exception as e:
            print("Altimeter gauge update error:", e)

        # Vertical speed (VSI) - alt farkından hesaplıyoruz (m/s)
            # -----------------------
            # VSI (Vertical Speed) - daha stabil + filtreli
            # -----------------------
        try:
            # 1) En iyi kaynak: vehicle.velocity (vz aşağı +)
            vs_mps = None
            if self.vehicle is not None and getattr(self.vehicle, "velocity", None):
                v = self.vehicle.velocity
                if isinstance(v, (list, tuple)) and len(v) >= 3 and v[2] is not None:
                    vs_mps = float(-v[2])  # climb rate (m/s)

            # 2) Fallback: alt farkı / dt (gerekirse)
            if vs_mps is None:
                now = time.time()
                if self._prev_alt is not None and self._prev_t is not None:
                    dt = max(0.1, now - self._prev_t)  # dt'yi büyüt -> jitter azalır
                    vs_mps = (data["alt"] - self._prev_alt) / dt
                else:
                    vs_mps = 0.0
                self._prev_alt = data["alt"]
                self._prev_t = now

            # 3) Clamp (çok uç değerleri kırp)
            vs_mps = max(-20.0, min(20.0, vs_mps))

            # 4) EMA low-pass filtre (yumuşatma)
            alpha = 0.15  # 0.10-0.25 arası güzel; büyürse daha hızlı tepki
            self._vsi_ema = (1 - alpha) * self._vsi_ema + alpha * vs_mps

            # 5) Widget'a yaz
            if hasattr(self.vsi_gauge, "setVerticalSpeed"):
                self.vsi_gauge.setVerticalSpeed(self._vsi_ema)
            elif hasattr(self.vsi_gauge, "setVSpeed"):
                self.vsi_gauge.setVSpeed(self._vsi_ema)
            elif hasattr(self.vsi_gauge, "setSpeed"):
                self.vsi_gauge.setSpeed(self._vsi_ema)
            elif hasattr(self.vsi_gauge, "setValue"):
                self.vsi_gauge.setValue(self._vsi_ema)

            # Görsel güncelleme garanti olsun
            if hasattr(self.vsi_gauge, "update"):
                self.vsi_gauge.update()

        except Exception as e:
            print("VSI update error:", e)

        # Attitude (pitch/roll)
        try:
            pitch_deg = data["pitch"]
            roll_deg = data["roll"]

            if hasattr(self.attitude_gauge, "setPitchRoll"):
                self.attitude_gauge.setPitchRoll(pitch_deg, roll_deg)
            elif hasattr(self.attitude_gauge, "setAttitude"):
                self.attitude_gauge.setAttitude(pitch_deg, roll_deg)
            else:
                if hasattr(self.attitude_gauge, "setPitch"):
                    self.attitude_gauge.setPitch(pitch_deg)
                if hasattr(self.attitude_gauge, "setRoll"):
                    self.attitude_gauge.setRoll(roll_deg)
        except Exception as e:
            print("Attitude update error:", e)

        # Compass / Heading (yaw)
        try:
            yaw_deg = data["yaw"]
            # -180..180 gibi gelebilir, 0..360'e çevir
            if yaw_deg < 0:
                yaw_deg += 360.0

            if hasattr(self.compass_gauge, "setHeading"):
                self.compass_gauge.setHeading(yaw_deg)
            elif hasattr(self.compass_gauge, "setValue"):
                self.compass_gauge.setValue(yaw_deg)
        except Exception as e:
            print("Compass update error:", e)

        # -----------------------
        # Turn Coordinator (bank + slip) - NONE SAFE
        # -----------------------
        try:
            # Bank: roll (derece)
            roll_deg = data["roll"]
            if hasattr(self.turn_gauge, "setBankAngle"):
                self.turn_gauge.setBankAngle(roll_deg)

            # Heading al (None gelirse sadece slip'i geç, fonksiyon devam etsin)
            heading = None
            if self.vehicle is not None:
                heading = getattr(self.vehicle, "heading", None)

            if heading is None:
                # heading yoksa slip hesaplamayı atla (bank yine güncellendi)
                pass
            else:
                heading = float(heading)
                now = time.time()

                # prev değerler yoksa sadece set et (return YOK!)
                if (self._prev_heading is None) or (self._prev_heading_t is None):
                    self._prev_heading = heading
                    self._prev_heading_t = now
                else:
                    dt = now - self._prev_heading_t
                    if dt > 0:
                        # wrap fix: -180..180
                        dhead = (heading - self._prev_heading + 180.0) % 360.0 - 180.0
                        turn_rate_deg_s = dhead / dt  # deg/s

                        # turn rate -> slip (görsel amaçlı)
                        slip = max(-1.0, min(1.0, turn_rate_deg_s / 10.0))

                        beta = 0.2
                        self._slip_ema = (1 - beta) * self._slip_ema + beta * slip

                        if hasattr(self.turn_gauge, "setSlip"):
                            self.turn_gauge.setSlip(self._slip_ema)

                        # prev güncelle
                        self._prev_heading = heading
                        self._prev_heading_t = now

        except Exception as e:
            print("Turn coordinator update error:", e)
        # -----------------------
        # HUD GÜNCELLEME
        # -----------------------
        try:
            if hasattr(self, "uydu_window") and self.uydu_window and self.uydu_window.isVisible():
                if hasattr(self, "hud") and self.hud:
                    roll_deg = data["roll"]
                    pitch_deg = data["pitch"]
                    yaw_deg = data["yaw"]
                    if yaw_deg < 0:
                        yaw_deg += 360.0

                    status = "ARMED" if self.vehicle and self.vehicle.armed else "DISARMED"

                    self.hud.set_telemetry(
                        roll_deg=roll_deg,
                        pitch_deg=pitch_deg,
                        yaw_deg=yaw_deg,
                        airspeed=data["air_speed"],
                        groundspeed=data["ground_speed"],
                        altitude=data["alt"],
                        status_text=status,
                        warn_text=""
                    )
        except Exception as e:
            print("HUD update error:", e)

        # İniş bittiyse (DISARM) kaydı durdur
        try:
            if getattr(self, "_landing_requested", False):
                if self.vehicle and (not self.vehicle.armed):
                    self._landing_requested = False
                    print("İniş tamamlandı (DISARM). Kayıt durduruluyor...")
                    self.stop_video_recording()
        except Exception as e:
            print("Landing auto-stop error:", e)

    def open_uydu_hud(self):
        try:
            self.uydu_window = QMainWindow()
            self.uydu_ui = UyduHudUI()
            self.uydu_ui.setupUi(self.uydu_window)

            self.setup_map_in_uydu_window()

            # 1) HUD oluştur (parent ver: pencere kapanınca düzgün toplansın)
            self.hud = HudWidget(parent=self.uydu_window)

            # 2) HUD'u nereye koyacaksın?
            #    A) Eğer Designer'da HUD alanının içinde zaten layout varsa:
            #       self.uydu_ui.hudLayout.addWidget(self.hud)
            #
            #    B) Eğer layout yoksa, container'a layout kurup ekle:
            if hasattr(self.uydu_ui, "hud_container"):
                container = self.uydu_ui.hud_container

                if container.layout() is None:
                    lay = QVBoxLayout(container)
                    lay.setContentsMargins(0, 0, 0, 0)
                    container.setLayout(lay)

                container.layout().addWidget(self.hud)
            else:
                # objectName yanlışsa buraya düşer
                raise AttributeError("UI içinde 'hud_container' adında bir widget yok. ObjectName yanlış.")

            self.uydu_window.show()

        except Exception as e:
            import traceback
            print("UYDU/HUD AÇILIRKEN HATA:", e)
            traceback.print_exc()

    def open_mod_window(self):
        self.mod_window = QMainWindow()
        self.mod_ui = Ui_mod_ekrani()
        self.mod_ui.setupUi(self.mod_window)

        # MEVCUT MODU YAZ
        if self.vehicle:
            current_mode = self.vehicle.mode.name
            self.mod_ui.mod_durumu.setText(f"Mod: {current_mode}")
        else:
            self.mod_ui.mod_durumu.setText("Mod: UNKNOWN")

        # BUTON BAĞLANTILARI
        self.mod_ui.auto_buton.clicked.connect(lambda: self.set_mode("AUTO"))
        self.mod_ui.loiter_buton.clicked.connect(lambda: self.set_mode("LOITER"))
        self.mod_ui.rtl_buton.clicked.connect(lambda: self.set_mode("RTL"))
        self.mod_ui.manual_buton.clicked.connect(lambda: self.set_mode("MANUAL"))

        self.mod_window.show()

    def start_takeoff(self):
        if not self.flight:
            print("FlightController hazır değil (bağlantı yok).")
            return

        # Aynı anda iki kez başlamasın
        if self.takeoff_worker and self.takeoff_worker.isRunning():
            print("Kalkış zaten çalışıyor.")
            return

        self.takeoff_worker = TakeoffWorker(self.flight)
        self.takeoff_worker.finished.connect(lambda msg: print(msg))
        self.takeoff_worker.failed.connect(lambda err: print("Kalkış hatası:", err))
        self.takeoff_worker.start()

    def start_land(self):
        if not self.flight:
            print("FlightController hazır değil (bağlantı yok).")
            return

        if self.land_worker and self.land_worker.isRunning():
            print("İniş zaten çalışıyor.")
            return

        self._landing_requested = True

        self.land_worker = LandWorker(self.flight)
        self.land_worker.finished.connect(lambda msg: print(msg))
        self.land_worker.failed.connect(lambda err: print("İniş hatası:", err))
        self.land_worker.start()

    def set_mode(self, mode_name):
        if not self.vehicle:
            print("Araç bağlı değil!")
            return

        try:
            from dronekit import VehicleMode

            # aynısı print(f"Mod değişti: {mode_name}")
            # print(f"Mode değiştiriliyor: {mode_name}")
            self.vehicle.mode = VehicleMode(mode_name)

            # GERÇEKTEN DEĞİŞTİ Mİ?
            for i in range(10):
                if self.vehicle.mode.name == mode_name:
                    print(f"Mod değişti: {mode_name}")
                    break
                time.sleep(0.5)
            else:
                print("Mod değişmedi!")

            # GERÇEK MODE'U YAZ
            current_mode = self.vehicle.mode.name

            if hasattr(self, "mod_ui"):
                self.mod_ui.mod_durumu.setText(f"Mod: {current_mode}")

            if hasattr(self.ui, "mod_label"):
                self.ui.mod_label.setText(f"Mod: {current_mode}")

        except Exception as e:
            print("Mod değiştirme hatası:", e)

    def _read_server_inputs(self):
        base_url = self.ui.sunucu_adresi.text().strip()
        username = self.ui.kullanici_adi.text().strip()
        password = self.ui.kullanici_sifresi.text().strip()
        return base_url, username, password

    # 1. BUTON: Sunucuya Giriş
    def on_sunucuya_giris_clicked(self):
        base_url, username, password = self._read_server_inputs()
        if not base_url:
            print("[HATA] Lütfen geçerli bir sunucu adresi girin.")
            return
        if not username or not password:
            print("[HATA] Kullanıcı adı veya şifre boş olamaz.")
            return

        # Client None ise önce istemciyi ilklendir
        print(f"[SİSTEM] Sunucu adresi ayarlanıyor: {base_url}")
        self.sig_init.emit(base_url)
        print("[SİSTEM] Sunucuya giriş isteği gönderiliyor...")
        self.sig_login.emit(username, password)
        # self.sync_server_time()

    # 2. BUTON: Sunucuya Bağlan
    def on_sunucuya_baglan_clicked(self):
        base_url, username, password = self._read_server_inputs()
        print("[SİSTEM] Sunucuya bağlantı doğrulama isteği gönderiliyor...")
        self.sig_connect.emit()

    # 3. BUTON: Sunucudan Çıkış
    def on_sunucudan_cikis_clicked(self):
        print("[SİSTEM] Sunucudan çıkış işlemleri başlatıldı...")

        # 1. Telemetri gönderimini durdur
        if hasattr(self, "telemetry_send_timer") and self.telemetry_send_timer.isActive():
            self.telemetry_send_timer.stop()
            print("[SİSTEM] Telemetri aktarımı durduruldu.")

        # 2. Kamera kaydı aktifse durdur
        if hasattr(self, "cam") and self.cam and getattr(self.cam, "is_recording", False):
            print("[KAYIT] Kamera kaydı durduruluyor...")
            self.cam.stop_recording()

        # 3. Video kontrolü ve Yükleme/Çıkış Yönetimi
        musabaka_no = "18"    # 18 yazdım geçici
        tarih_str = datetime.now().strftime("%d_%m_%Y")
        target_mp4 = os.path.join("records", f"{musabaka_no}_AZAK_SIHA_DGM_TAKIMI_{tarih_str}.mp4")
        video_path = getattr(self, "last_recorded_video_path", None) or target_mp4

        if os.path.exists(video_path):
            print(f"[YÜKLEME] Video sunucuya yükleniyor: {video_path}")
            # Yalnızca yükleme sinyali atılır. Yükleme tamamlanınca _on_server_ok fonksiyonu çıkışı yapacaktır.
            self.sig_upload_video_http.emit(video_path)
        else:
            print(f"[BİLGİ] Yüklenecek video bulunamadı, direkt oturum kapatılıyor.")
            self.sig_logout.emit()

    # 4. BUTON: Telemetri Aktarımı
    def on_telemetri_aktarimi_clicked(self):
        if self.telemetry_send_timer.isActive():
            self.telemetry_send_timer.stop()
            print("[SİSTEM] Telemetri aktarımı durduruldu.")
            return

        if not self.server_connected:
            print("[HATA] Telemetri başlatılamadı: Önce Sunucuya Bağlanın.")
            return

        self.telemetry_send_timer.start()
        print("[SİSTEM] Telemetri aktarımı başlatıldı.")

    # SERVER OK Dinleyicisi (Tek Çıkış Garantisi)
    def _on_server_ok(self, msg: str):
        print("[SERVER OK]", msg)
        # Video yüklendikten sonra logout işlemini tek seferde tetikler
        if "Video dosyası (HTTP) sunucuya gönderildi" in msg:
            print("[SİSTEM] Video yükleme tamamlandı, sunucu oturumu kapatılıyor...")
            self.sig_logout.emit()


    def sync_server_time(self):
        """İlk girişte veya bağlantıda 1 kere çalışır; zaman farkını (offset) hesaplar."""
        try:
            if self.server_worker and self.server_worker.client:
                # Sunucudan 1 kere zaman yanıtı alınıyor
                data = self.server_worker.client.get_server_time()
                if data and isinstance(data, dict):
                    # Sunucudan gelen saati datetime nesnesine dönüştür
                    now_year = datetime.now().year
                    now_month = datetime.now().month
                    now_day = datetime.now().day

                    server_dt = datetime(
                        now_year, now_month, now_day,
                        data.get("saat", 0),
                        data.get("dakika", 0),
                        data.get("saniye", 0),
                        data.get("milisaniye", 0) * 1000
                    )

                    # Sunucu saati ile bilgisayarın yerel saati arasındaki fark (saniye cinsinden)
                    local_dt = datetime.now()
                    self.time_offset = (server_dt - local_dt).total_seconds()
                    print(f"[SİSTEM] Zaman senkronizasyonu tamamlandı. Offset: {self.time_offset:.3f} sn")
        except Exception as e:
            print("Zaman senkronizasyon hatası:", e)


    def _send_telemetry_to_server(self):
        if not self._last_telemetry:
            return

        raw = self._last_telemetry
        is_autonom = 1 if raw.get("mode") in ["AUTO", "GUIDED", "RTL"] else 0

        # ------------------------------------------------------------------
        # YEREL SAAT + OFFSET KULLANILARAK ANLIK SUNUCU SAATİ HESAPLANIYOR
        # ------------------------------------------------------------------
        gps_utc_time = datetime.now(timezone.utc) + timedelta(seconds=self.time_offset)         # değişecek

        gps_saati = {
            "saat": gps_utc_time.hour,
            "dakika": gps_utc_time.minute,
            "saniye": gps_utc_time.second,
            "milisaniye": int(gps_utc_time.microsecond / 1000)
        }

        payload = {
            "takim_numarasi": 18,
            "iha_enlem": raw.get("lat", 0.0),
            "iha_boylam": raw.get("lon", 0.0),
            "iha_irtifa": raw.get("alt", 0.0),
            "iha_dikilme": round(raw.get("pitch", 0.0), 2),  # Zaten derece
            "iha_yonelme": round(raw.get("yaw", 0.0), 2),  # Zaten derece
            "iha_yatis": round(raw.get("roll", 0.0), 2),  # Zaten derece
            "iha_hiz": raw.get("ground_speed", 0.0),
            "iha_batarya": raw.get("battery") if raw.get("battery") is not None else 0,
            "iha_otonom": is_autonom,
            "iha_kilitlenme": getattr(self, "lock_status", 0),
            "hedef_merkez_X": getattr(self, "target_x", 0),
            "hedef_merkez_Y": getattr(self, "target_y", 0),
            "hedef_genislik": getattr(self, "target_w", 0),
            "hedef_yukseklik": getattr(self, "target_h", 0),
            "gps_saati": gps_saati                                  # bu değişecek gerçek ihadan gelmeli
        }

        self.sig_send_tel.emit(payload)

    # -------------------------
    # VIDEO: Upload + Play
    # -------------------------
    def on_video_yukle_clicked(self):
        """
        last_recorded_video_path doluysa sunucuya yollar.
        """
        if not self.last_recorded_video_path or not os.path.exists(self.last_recorded_video_path):
            print("Yüklenecek video yok. Önce video kaydı oluşturmalısın.")
            return
        self.sig_upload_video_http.emit(self.last_recorded_video_path)

    def on_camera_frame(self, qimg: QImage):
        if not hasattr(self.ui, "kamera"):
            return

        pix = QPixmap.fromImage(qimg)
        w = max(1, self.ui.kamera.width())
        h = max(1, self.ui.kamera.height())
        pix = pix.scaled(w, h)
        self.ui.kamera.setPixmap(pix)


    # gereksiz satır, self.cam.status.connect(lambda m: print("[CAM]", m)) aynı işi yapıyor
    def start_video_recording(self):
        self.cam.start_recording(base_name="latest", out_dir="records")
        print("Kayıt başlatıldı.")


    def start_stream(self):
        # BURAYI SONRA SERVERA GÖRE DEĞİŞTİRECEĞİZ
        stream_url = "rtmp://localhost/live/test"

        if hasattr(self, "cam") and self.cam:
            self.cam.start_streaming(stream_url)
            print(" Canlı yayın başlatıldı")

    def stop_stream(self):
        if hasattr(self, "cam") and self.cam:
            self.cam.stop_streaming()
            print("Canlı yayın durduruldu")


    def _auto_start_recording(self):
        # Zaten kayıt başladıysa tekrar başlatma
        if hasattr(self, "cam") and self.cam and not self.cam.is_recording:
            self.start_video_recording()
            # print("20 sn geçti: otomatik kayıt başlatıldı.")

    # gereksiz çünkü, self.status.emit("Kayıt durdu. MP4'e dönüştürülüyor...") bu satır aynı işi yapıyor
    def stop_video_recording(self):
        self.cam.stop_recording()
        # print("Kayıt durduruldu. MP4 hazır olunca terminale yazılacak.")


    def on_server_connected_state(self, st: bool):
        self.server_connected = st

        if st:
            print("[Sistem] Server bağlandı")
            self.sync_server_time()

            print("HSS verileri periyodik olarak sorgulanıyor...")

            # İstek döngüsünü başlat (Eğer zaten çalışmıyorta)
            if not self.hss_poll_timer.isActive():
                self.hss_poll_timer.start()
        else:
            print("[SİSTEM] Server bağlantısı koptu.")

    def on_hss_received(self, hss_list: list):
        # Veri None gelirse boş liste olarak ele al
        if hss_list is None:
            hss_list = []

        # Veriyi arka planda her durumda (boş olsa dahi) güncel tut
        self.latest_hss_list = hss_list

        # Harita penceresi yüklendi ve hazırsa JS tarafına aktar (boş liste gitse bile haritadaki çizimleri temizler)
        if hasattr(self, "map_view") and self.map_view and getattr(self, "map_ready", False):
            js_code = f"updateHSSAreas({json.dumps(hss_list)});"
            self.map_view.page().runJavaScript(js_code)


    def append_terminal(self, text):
        self.ui.terminal_view.moveCursor(self.ui.terminal_view.textCursor().End)
        self.ui.terminal_view.insertPlainText(text)
        self.ui.terminal_view.ensureCursorVisible()

    def setup_button_connections(self):
        def safe_connect(button, func):
            try:
                button.clicked.disconnect()
            except Exception:
                pass
            button.clicked.connect(func)

        # Otonom Kilitlenme
        if hasattr(self.ui, "otonom_kilitlenme_gorevi"):
            safe_connect(self.ui.otonom_kilitlenme_gorevi,
                         lambda: self.handle_mission_send(0, "Otonom Kilitlenme Görevi"))
        else:
            print(
                "[UYARI] UI nesnesinde 'otonom_kilitlenme_gorevi' butonu bulunamadı! Designer objectName kontrol edin.")

        # Kamikaze
        if hasattr(self.ui, "kamikaze_gorevi"):
            safe_connect(self.ui.kamikaze_gorevi, lambda: self.handle_mission_send(1, "Kamikaze Görevi"))
        else:
            print("[UYARI] UI nesnesinde 'kamikaze_gorevi' butonu bulunamadı!")

        # Rota İzle
        if hasattr(self.ui, "rota_izle"):
            safe_connect(self.ui.rota_izle, lambda: self.handle_mission_send(2, "Rota İzle Görevi"))
        else:
            print("[UYARI] UI nesnesinde 'rota_izle' butonu bulunamadı!")

        # HSS Kacis
        if hasattr(self.ui, "hssden_kacis"):
            safe_connect(self.ui.hssden_kacis, lambda: self.handle_mission_send(3, "HSS'den Kaçış Görevi"))
        else:
            print("[UYARI] UI nesnesinde 'hssden_kacis' butonu bulunamadı!")

        # Kilitlen Butonu
        if hasattr(self.ui, "kilitlen_butonu"):
            safe_connect(self.ui.kilitlen_butonu, self.on_kilitlen_clicked)
        else:
            print("[UYARI] UI nesnesinde 'kilitlen_butonu' bulunamadı!")

    def handle_mission_send(self, mode_id: int, mode_name: str):
        """Butona basıldığında arayüz terminaline log basar ve MAVLink worker'a komutu iletir."""
        print(f"[GÖREV EMRİ] {mode_name} (Mod ID: {mode_id}) tetiklendi.")
        if hasattr(self, "mav_worker") and self.mav_worker:
            self.mav_worker.send_mission_mode(mode_id)
            print(f"[MAVLINK] Mod ID {mode_id} Jetson MAVLink worker'a gönderildi.")
        else:
            print("[HATA] JetsonMavlinkWorker başlatılamadığı için komut iletilemedi!")

    def update_telemetry_ui(self, data: dict):
        lock_duration = data.get("LCK_DUR", 0.0)
        lock_count = int(data.get("LCK_CNT", 0))
        remaining_time = data.get("REMAINING_TIME", 0)  # Telemetriden gelen kalan süre ekleniyor

        if hasattr(self.ui, "kilitlenme_suresi"):
            self.ui.kilitlenme_suresi.setText(f"{lock_duration:.1f} s")

        if hasattr(self.ui, "kilitlenme_sayisi"):
            self.ui.kilitlenme_sayisi.setText(f"{lock_count}")

        # Kalan yarışma süresi kutusu güncellemesi
        if hasattr(self.ui, "kalan_yarisma_suresi"):
            self.ui.kalan_yarisma_suresi.setText(f"{remaining_time} s")

    def update_status_logs(self, text: str, severity: int):
        if hasattr(self.ui, "kilitlenme_durumu"):
            self.ui.kilitlenme_durumu.setText(text)

        if hasattr(self.ui, "txt_system_log"):
            self.ui.txt_system_log.append(f"[{time.strftime('%H:%M:%S')}] {text}")

    def update_connection_status(self, connected: bool):
        if hasattr(self.ui, "lbl_connection_status"):
            if connected:
                self.ui.lbl_connection_status.setText("BAĞLANDI")
                self.ui.lbl_connection_status.setStyleSheet("color: green;")
            else:
                self.ui.lbl_connection_status.setText("BAĞLANTI KOPTU")
                self.ui.lbl_connection_status.setStyleSheet("color: red;")

    def on_kilitlen_clicked(self):
        """takim_adi QLineEdit kutusundaki ID/metin değerini okur ve Jetson Worker'a kilitlenme emri gönderir."""
        if hasattr(self.ui, "takim_adi"):
            target_text = self.ui.takim_adi.text().strip()
            try:
                target_id = int(target_text) if target_text else 0
                self.mav_worker.send_target_lock(target_id)
                print(f"[KİLİTLENME] Hedef ID: {target_id} için kilitlenme emri gönderildi.")
            except ValueError:
                print(f"[HATA] Geçersiz hedef ID'si: '{target_text}'. Sayısal bir değer giriniz.")

    def closeEvent(self, event):
        # 1. Timers
        if hasattr(self, "telemetry_send_timer") and self.telemetry_send_timer.isActive():
            self.telemetry_send_timer.stop()
        if hasattr(self, "map_timer") and self.map_timer.isActive():
            self.map_timer.stop()

        # 2. Jetson Worker
        if hasattr(self, "mav_worker") and self.mav_worker:
            self.mav_worker.stop()

        # 3. Telemetry Reader Thread
        if hasattr(self, "reader") and self.reader:
            self.reader.stop()

        # 4. Camera Thread
        if hasattr(self, "cam") and self.cam:
            self.cam.stop()

        # 5. Server Thread
        if hasattr(self, "server_thread") and self.server_thread.isRunning():
            self.server_thread.quit()
            self.server_thread.wait(1000)

        event.accept()

    def setup_map_in_uydu_window(self):
        self.map_view = QWebEngineView()
        file_path = os.path.abspath("map.html")
        # bunu yeni ekledim
        print("MAP PATH:", file_path)
        print("EXISTS:", os.path.exists(file_path))

        if not os.path.exists(file_path):
            print("HARİTA DOSYASI BULUNAMADI ")
            return

        self.map_view.load(QUrl.fromLocalFile(file_path))
        self.map_view.loadFinished.connect(self.on_map_loaded)

        # Burada container UyduHudUI içinde olmalı
        # Qt Designer'da uydu penceresindeki sol alanın objectName'i neyse onu yazacaksın.
        # Örnek: "uydu_goruntusu_widget" diyelim:
        if not hasattr(self.uydu_ui, "uydu_goruntusu_widget"):
            raise AttributeError("UyduHudUI içinde 'uydu_goruntusu_widget' yok. Designer objectName'i kontrol et.")

        container = self.uydu_ui.uydu_goruntusu_widget

        if container.layout() is None:
            lay = QVBoxLayout(container)
            lay.setContentsMargins(0, 0, 0, 0)
            container.setLayout(lay)

        container.layout().addWidget(self.map_view)

    def on_recording_finished(self, path):
        self.last_recorded_video_path = path
        print("Son video hazır:", path)
        # alttaki güncellllllllll

    def update_map_position(self, lat, lon, heading):

        # SADECE SON KONUMU SAKLA
        self.last_position = (lat, lon, heading)

        # BURADAN SONRA HİÇBİR ŞEY YAPMA

    def on_competitors_received(self, targets: list):
        self.latest_competitors = targets

        if len(targets) > 0 and hasattr(self.ui, "takim_adi_1"):
            team1_name = str(targets[0].get("takim_numarasi", targets[0]))
            self.ui.takim_adi_1.setText(team1_name)

        if len(targets) > 1 and hasattr(self.ui, "takim_adi_2"):
            team2_name = str(targets[1].get("takim_numarasi", targets[1]))
            self.ui.takim_adi_2.setText(team2_name)

        if len(targets) > 2 and hasattr(self.ui, "takim_adi_4"):
            team4_name = str(targets[2].get("takim_numarasi", targets[2]))
            self.ui.takim_adi_4.setText(team4_name)

    def on_map_loaded(self):
        print("Harita tamamen yüklendi")
        self.map_ready = True

        # SON KONUMU BAS
        if self.last_position:
            lat, lon, heading = self.last_position
            js_code = f"updatePlane({lat}, {lon}, {heading});"
            self.map_view.page().runJavaScript(js_code)

        # 2. BOUNDARY / YASAKLI SAHAYI BASS[cite: 5]
        self.load_boundary_to_map()

        # 3. Harita açılmadan önce gelmiş olan HSS verileri varsa çizdir
        if hasattr(self, "latest_hss_list") and self.latest_hss_list:
            js_code = f"updateHSSAreas({json.dumps(self.latest_hss_list)});"
            self.map_view.page().runJavaScript(js_code)
            print("[HARİTA] Önceki HSS verileri haritaya aktarıldı.")

    # bunu da yeni ekledim güncellllll
    def update_map_safe(self):
        if not hasattr(self, "map_view") or self.map_view is None:
            return

        if not hasattr(self, "map_ready") or not self.map_ready:
            return

        try:
            # BİZİM İHA
            if hasattr(self, "last_position") and self.last_position is not None:
                lat, lon, heading = self.last_position
                js_code = f"updatePlane({lat}, {lon}, {heading});"
                self.map_view.page().runJavaScript(js_code)

            # RAKİPLER
            if hasattr(self, "latest_competitors") and self.latest_competitors:
                js = f"updateEnemies({json.dumps(self.latest_competitors)});"
                self.map_view.page().runJavaScript(js)

        except Exception as e:
            print("Map update error:", e)

    def load_boundary_to_map(self):
        boundary_file = "boundary.json"

        if not os.path.exists(boundary_file):
            print("[UYARI] Boundary dosyası bulunamadı:", boundary_file)
            return

        try:
            with open(boundary_file, "r", encoding="utf-8") as f:
                boundary_data = json.load(f)

            js_data = json.dumps(boundary_data)
            js_code = f"drawBoundaryPolygon({js_data});"

            # Harita DOM'unun tam hazır olması için 500ms gecikmeli çalıştır
            QTimer.singleShot(500, lambda: self.map_view.page().runJavaScript(js_code))
            print("[SİSTEM] Boundary çizim komutu haritaya gönderildi.")

        except Exception as e:
            print("Boundary yükleme hatası:", e)


