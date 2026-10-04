
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer, QUrl
from dronekit import connect
from YerKontrolAzakSiha.sihaArayuz import Ui_MainWindow as SihaUI
from YerKontrolAzakSiha.Uydu_Hud_Ekrani import Ui_MainWindow as UyduHudUI
from YerKontrolAzakSiha.flight_controller import FlightController
import sys, time, os, datetime
import cv2
from PyQt5.QtGui import QImage, QPixmap, QFont
from YerKontrolAzakSiha.server_service import ServerWorker
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from YerKontrolAzakSiha.hud_widget import HudWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
import subprocess
from pathlib import Path


# ✅ GÖSTERGE WIDGET'LARI (sadece ekranda görünmesi için)
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

                telemetry = {
                    "lat": float(loc.lat) if loc and loc.lat is not None else 0.0,
                    "lon": float(loc.lon) if loc and loc.lon is not None else 0.0,
                    "alt": float(loc.alt) if loc and loc.alt is not None else 0.0,
                    "air_speed": float(self.vehicle.airspeed or 0.0),
                    "ground_speed": float(self.vehicle.groundspeed or 0.0),
                    "yaw": float(att.yaw) if att and att.yaw is not None else 0.0,
                    "pitch": float(att.pitch) if att and att.pitch is not None else 0.0,
                    "roll": float(att.roll) if att and att.roll is not None else 0.0,
                    "battery": batt_level,
                    "signal": sig_level,
                }

                self.data_received.emit(telemetry)

                heading = float(getattr(self.vehicle, "heading", 0.0) or 0.0)
                self.map_signal.emit(telemetry["lat"], telemetry["lon"], heading)

            except Exception as e:
                print("Telemetry okuma hatası:", e)

            self.msleep(100)

    def stop(self):
        self.running = False
        self.wait()
class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    recording_finished = pyqtSignal(str)   # ✅ mp4 yolu
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

    def run(self):
        cap = cv2.VideoCapture(self.cam_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            self.status.emit(f"❌ Kamera açılamadı! index: {self.cam_index}")
            return

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
                    self.status.emit(f"⚠️ Kayıt yazma hatası: {e}")

            # UI'ya bas
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.frame_ready.emit(qimg)

            self.msleep(20)

        cap.release()
        self._stop_writer()

    def start_recording(self, base_name=None, out_dir="records"):
        if self.is_recording:
            self.status.emit("⚠️ Zaten kayıt yapılıyor.")
            return

        Path(out_dir).mkdir(parents=True, exist_ok=True)

        if base_name is None:
            base_name = time.strftime("%Y%m%d_%H%M%S")

        self.avi_path = str(Path(out_dir) / f"{base_name}.avi")
        self.mp4_path = str(Path(out_dir) / f"{base_name}.mp4")

        fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # ✅ stabil
        self.writer = cv2.VideoWriter(self.avi_path, fourcc, self.record_fps, self.frame_size)
        if not self.writer.isOpened():
            self.writer = None
            self.status.emit("❌ VideoWriter açılamadı. Kayıt başlayamadı.")
            return

        self.is_recording = True
        self.status.emit(f"⏺ Kayıt başladı: {self.avi_path}")

    def stop_recording(self):
        if not self.is_recording:
            self.status.emit("⚠️ Kayıt zaten kapalı.")
            return

        self.is_recording = False
        self._stop_writer()
        self.status.emit("⏹ Kayıt durdu. MP4'e dönüştürülüyor...")

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

                self.status.emit(f"✅ MP4 hazır: {self.mp4_path}")
                self.recording_finished.emit(self.mp4_path)
            except Exception as e:
                self.status.emit(f"❌ FFmpeg hata: {e}")
        else:
            # ffmpeg yoksa avi path döndür
            self.status.emit("⚠️ ffmpeg_path yok. AVI kaydedildi.")
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
class arayuzBackend(QMainWindow):
    sig_init = pyqtSignal(str)
    sig_login = pyqtSignal(str, str)
    sig_logout = pyqtSignal()
    sig_connect = pyqtSignal()
    sig_send_tel = pyqtSignal(dict)
    sig_upload_video_http = pyqtSignal(str)
    sig_poll_competitors = pyqtSignal()   # yeni eklendi

    def __init__(self):
        super().__init__()
        self.ui = SihaUI()
        self.ui.setupUi(self)


        # -------- Kamera canlı izleme (PC kamerası) --------
        if hasattr(self.ui, "kamera"):
            self.ui.kamera.setScaledContents(True)

        ffmpeg_path = r"C:\ffmpeg\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
        self.cam = CameraThread(cam_index=0, ffmpeg_path=ffmpeg_path)
        self.cam.frame_ready.connect(self.on_camera_frame)
        self.cam.start()
        self.cam.status.connect(lambda m: print("[CAM]", m))
        self.cam.recording_finished.connect(self.on_recording_finished)

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



        # -------------------------------------------------
        # ✅ GÖSTERGELERİ EKRENDA GÖSTER (SADECE GÖRÜNTÜ)
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

        # ----------- DroneKit bağlantı + telemetri thread -----------
        self.vehicle = None
        self.flight = None
        self.reader = None

        self.takeoff_worker = None
        self.land_worker = None

        self._prev_yaw = None
        self._prev_yaw_t = None

        self.connector = VehicleConnector("udp:0.0.0.0:14552")
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
        self.sig_init.connect(self.server_worker.init_client)
        self.sig_login.connect(self.server_worker.login)
        self.sig_logout.connect(self.server_worker.logout)
        self.sig_connect.connect(self.server_worker.connect_server)
        self.sig_send_tel.connect(self.server_worker.send_telemetry)
        self.sig_upload_video_http.connect(self.server_worker.upload_video_http)
        self.sig_poll_competitors.connect(self.server_worker.poll_competitors)        #yeni eklendi bu da

        # Worker -> GUI log
        self.server_worker.ok.connect(lambda m: print("[SERVER OK]", m))
        self.server_worker.err.connect(lambda m: print("[SERVER ERR]", m))

        self.server_worker.competitors.connect(self.on_competitors_received)    #yeni eklendi

        self.server_thread.start()

        # -------------------------
        # TELEMETRY SEND TIMER (5 Hz)
        # -------------------------
        self._last_telemetry = None
        self.telemetry_send_timer = QTimer(self)
        self.telemetry_send_timer.setInterval(200)  # 5 Hz
        self.telemetry_send_timer.timeout.connect(self._send_telemetry_to_server)

# bu kısımda yeni eklendi bu ara
        self.latest_competitors = []

        self.competitor_poll_timer = QTimer(self)
        self.competitor_poll_timer.setInterval(100)  # 10 Hz
        self.competitor_poll_timer.timeout.connect(lambda: self.sig_poll_competitors.emit())
# bu parça yani
        # -------------------------
        # UI BUTTON CONNECTIONS
        # (objectName'ler birebir aynı olmalı)
        # -------------------------
        self.ui.sunucuya_giris.clicked.connect(self.on_sunucuya_giris_clicked)
        self.ui.sunucuya_baglan.clicked.connect(self.on_sunucuya_baglan_clicked)
        self.ui.sunucudan_cikis.clicked.connect(self.on_sunucudan_cikis_clicked)
        self.ui.telemetri_aktarimi.clicked.connect(self.on_telemetri_aktarimi_clicked)

        # Video upload + video oynatma butonun varsa bağla:
        # Qt Designer'da buton koyduysan objectName'leri böyle varsayıyorum:
        # self.ui.video_yukle.clicked.connect(self.on_video_yukle_clicked)
        # self.ui.son_videoyu_oynat.clicked.connect(self.on_son_videoyu_oynat_clicked)

        # -------------------------
        # VIDEO PLAYER (Son videoyu arayüzde oynatma)
        # -------------------------
        self.last_recorded_video_path = None  # kaydedilen son video buraya yazılacak

        # Eğer arayüzünde bir placeholder widget varsa (ör: self.ui.video_frame gibi)
        # onu VideoWidget ile değiştirmek daha iyidir. En kolayı:
        self.video_widget = QVideoWidget(self)
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)

        # Video'yu nereye yerleştireceğiz?
        # 1) Eğer UI'da video için bir layout varsa (ör: self.ui.video_layout):
        #    self.ui.video_layout.addWidget(self.video_widget)
        #
        # 2) Eğer yoksa, şimdilik pencere içine manuel koy:
        self.video_widget.setGeometry(50, 50, 640, 360)  # istersen değiştir
        self.video_widget.hide()  # oynatınca show yapacağız

        self.server_connected = False
        self.server_worker.connected_state.connect(self.on_server_connected_state)

        # Terminal yönlendirme
        self.stdout = StreamRedirect()
        self.stdout.new_text.connect(self.append_terminal)
        sys.stdout = self.stdout
        sys.stderr = self.stdout  # Hatalar da düşsün

        # Terminal font ayarı
        font = QFont()
        font.setFamily("Consolas")  # Terminal fontu (Windows için güzel)
        font.setPointSize(14)  # Punto büyüklüğü (istediğin gibi değiştir)

        self.ui.terminal_view.setFont(font)

        print("Terminal hazır.")

        if hasattr(self.ui, "video_yukle"):
            self.ui.video_yukle.clicked.connect(self.on_video_yukle_clicked)

        if hasattr(self.ui, "kayit_baslat"):
            self.ui.kayit_baslat.clicked.connect(self.start_video_recording)

        if hasattr(self.ui, "kayit_durdur"):
            self.ui.kayit_durdur.clicked.connect(self.stop_video_recording)

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
            pitch_deg = data["pitch"] * 57.2957795
            roll_deg = data["roll"] * 57.2957795

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
            yaw_deg = data["yaw"] * 57.2957795
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
        # Turn Coordinator (bank + slip)
        # -----------------------
        # -----------------------
        # Turn Coordinator (bank + slip) - NONE SAFE
        # -----------------------
        try:
            # Bank: roll (derece)
            roll_deg = data["roll"] * 57.2957795
            if hasattr(self.turn_gauge, "setBankAngle"):
                self.turn_gauge.setBankAngle(roll_deg)

            # Heading al (None gelirse işlem yapma)
            if self.vehicle is None:
                return

            heading = getattr(self.vehicle, "heading", None)
            if heading is None:
                # heading gelmiyorsa slip hesaplayamayız, sadece bank çalışır
                return

            heading = float(heading)
            now = time.time()

            # prev değerler yoksa ilk kez set et ve çık
            if (not hasattr(self, "_prev_heading")) or (self._prev_heading is None) or \
                    (not hasattr(self, "_prev_heading_t")) or (self._prev_heading_t is None):
                self._prev_heading = heading
                self._prev_heading_t = now
                return

            dt = now - self._prev_heading_t
            if dt <= 0:
                self._prev_heading = heading
                self._prev_heading_t = now
                return

            # wrap fix: -180..180
            dhead = (heading - self._prev_heading + 180.0) % 360.0 - 180.0
            turn_rate_deg_s = dhead / dt  # deg/s

            # turn rate -> slip (görsel amaçlı)
            slip = max(-1.0, min(1.0, turn_rate_deg_s / 10.0))

            # slip'i yumuşat (opsiyonel ama güzel)
            if not hasattr(self, "_slip_ema") or self._slip_ema is None:
                self._slip_ema = 0.0
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
                    roll_deg = data["roll"] * 57.2957795
                    pitch_deg = data["pitch"] * 57.2957795
                    yaw_deg = data["yaw"] * 57.2957795
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

        self.land_worker = LandWorker(self.flight)
        self.land_worker.finished.connect(lambda msg: print(msg))
        self.land_worker.failed.connect(lambda err: print("İniş hatası:", err))
        self.land_worker.start()

    def closeEvent(self, event):
        try:
            if hasattr(self, "telemetry_send_timer") and self.telemetry_send_timer.isActive():
                self.telemetry_send_timer.stop()
        except:
            pass

        try:
            if hasattr(self, "cam") and self.cam:
                self.cam.stop()
        except:
            pass

        try:
            if self.reader:
                self.reader.stop()
            if self.vehicle:
                self.vehicle.close()
        except:
            pass

        try:
            if hasattr(self, "server_thread") and self.server_thread.isRunning():
                self.server_thread.quit()
                self.server_thread.wait(1000)
        except:
            pass

        super().closeEvent(event)

    def _read_server_inputs(self):
        base_url = self.ui.sunucu_adresi.text().strip()
        username = self.ui.kullanici_adi.text().strip()
        password = self.ui.kullanici_sifresi.text().strip()
        return base_url, username, password

    def on_sunucuya_giris_clicked(self):
        base_url, username, password = self._read_server_inputs()
        self.sig_init.emit(base_url)
        self.sig_login.emit(username, password)

    def on_sunucuya_baglan_clicked(self):
        base_url, username, password = self._read_server_inputs()
        self.sig_init.emit(base_url)
        self.sig_connect.emit()

    def on_sunucudan_cikis_clicked(self):
        if self.telemetry_send_timer.isActive():
            self.telemetry_send_timer.stop()
        self.sig_logout.emit()

    def on_telemetri_aktarimi_clicked(self):
        if self.telemetry_send_timer.isActive():
            self.telemetry_send_timer.stop()
            print("Telemetri aktarımı durduruldu.")
            return

        if not self.server_connected:
            print("Telemetri başlatılamadı: Önce Sunucuya Bağlan.")
            return

        self.telemetry_send_timer.start()
        print("Telemetri aktarımı başlatıldı.")

    def _send_telemetry_to_server(self):
        if not self._last_telemetry:
            return
        self.sig_send_tel.emit(self._last_telemetry)

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

    def on_son_videoyu_oynat_clicked(self):
        """
        Son kaydı PyQt video player ile oynatır.
        """
        if not self.last_recorded_video_path or not os.path.exists(self.last_recorded_video_path):
            print("Oynatılacak video yok.")
            return

        self.video_widget.show()
        url = QUrl.fromLocalFile(self.last_recorded_video_path)
        self.media_player.setMedia(QMediaContent(url))
        self.media_player.play()
        print("Son video oynatılıyor...")

    def on_camera_frame(self, qimg: QImage):
        if not hasattr(self.ui, "kamera"):
            return
        pix = QPixmap.fromImage(qimg)
        w = max(1, self.ui.kamera.width())
        h = max(1, self.ui.kamera.height())
        pix = pix.scaled(w, h)
        self.ui.kamera.setPixmap(pix)

    def start_video_recording(self):
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.cam.start_recording(base_name=f"record_{now}", out_dir="records")
        print("⏺ Kayıt başlatıldı.")

    def stop_video_recording(self):
        self.cam.stop_recording()
        print("⏹ Kayıt durduruldu. MP4 hazır olunca terminale yazılacak.")

    def play_last_video_on_label(self):
        if not self.last_recorded_video_path or not os.path.exists(self.last_recorded_video_path):
            print("Oynatılacak video yok.")
            return

        self._play_cap = cv2.VideoCapture(self.last_recorded_video_path)
        if not self._play_cap.isOpened():
            print("Video açılamadı:", self.last_recorded_video_path)
            return

        fps = self._play_cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps < 1:
            fps = 25
        interval = int(1000 / fps)

        if hasattr(self, "_play_timer") and self._play_timer:
            self._play_timer.stop()

        self._play_timer = QTimer(self)
        self._play_timer.timeout.connect(self._play_next_frame)
        self._play_timer.start(interval)

    def _play_next_frame(self):
        ret, frame = self._play_cap.read()
        if not ret:
            self._play_timer.stop()
            self._play_cap.release()
            print("Video bitti.")
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.on_camera_frame(qimg)  # aynı QLabel'a bas

    def on_server_connected_state(self, st: bool):
        self.server_connected = st
        print("[SERVER]", "CONNECTED" if st else "DISCONNECTED")

        if st:
            # Rakipleri çekmeye başla
            self.competitor_poll_timer.start()
            print("[COMP] Rakip telemetri polling başladı (10 Hz).")
        else:
            # Rakip polling durdur
            if self.competitor_poll_timer.isActive():
                self.competitor_poll_timer.stop()
            print("[COMP] Rakip telemetri polling durdu.")

    def append_terminal(self, text):
        self.ui.terminal_view.moveCursor(self.ui.terminal_view.textCursor().End)
        self.ui.terminal_view.insertPlainText(text)
        self.ui.terminal_view.ensureCursorVisible()

    def setup_map_in_uydu_window(self):
        self.map_view = QWebEngineView()
        file_path = os.path.abspath("YerKontrolAzakSiha/map.html")
        self.map_view.load(QUrl.fromLocalFile(file_path))

        # ✅ Burada container UyduHudUI içinde olmalı
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

    def update_map_position(self, lat, lon, heading):
        if not hasattr(self, "map_view") or self.map_view is None:
            return
        js_code = f"updatePlane({lat}, {lon}, {heading});"
        self.map_view.page().runJavaScript(js_code)

    def on_recording_finished(self, path):
        self.last_recorded_video_path = path
        print("✅ Son video hazır:", path)

#yeni eklendi
    def on_competitors_received(self, targets: list):
        # Şimdilik sadece terminale basalım
        self.latest_competitors = targets

        # Kısa özet: ilk 3 hedefi yaz
        preview = targets[:3]
        print(f"[COMP] {len(targets)} hedef alındı. İlk 3: {preview}")








'''
# zeyneple çalışan kod

import sys
import cv2

from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from sihaArayuz import Ui_MainWindow as SihaUI
from Uydu_Hud_Ekrani import Ui_MainWindow as UyduHudUI
from gostergeler import (
    AirspeedGauge, AltimeterGauge, VerticalSpeedGauge,
    AttitudeIndicator, CompassIndicator, TurnCoordinatorIndicator
)
from flight_controller import FlightController
from dronekit import connect


# ------------------- DroneKit connect thread -------------------
class VehicleConnector(QThread):
    connected = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, conn_str="udp:127.0.0.1:14552"):
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

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle
        self.running = True

    def run(self):
        while self.running:
            try:
                loc = self.vehicle.location.global_relative_frame
                att = self.vehicle.attitude

                telemetry = {
                    'lat': loc.lat if loc else 0.0,
                    'lon': loc.lon if loc else 0.0,
                    'alt': loc.alt if loc else 0.0,
                    'air_speed': float(self.vehicle.airspeed or 0.0),
                    'ground_speed': float(self.vehicle.groundspeed or 0.0),
                    'yaw': float(att.yaw or 0.0),
                    'pitch': float(att.pitch or 0.0),
                    'roll': float(att.roll or 0.0),
                }
                self.data_received.emit(telemetry)
            except Exception as e:
                print("Okuma Hatası:", e)

            self.msleep(100)

    def stop(self):
        self.running = False
        self.wait()


# ------------------- Video thread (camera_service yayını) -------------------
class VideoClient(QThread):
    frame_ready = pyqtSignal(QImage)

    def __init__(self, url="http://127.0.0.1:8080/video"):
        super().__init__()
        self.url = url
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(self.url)
        if not cap.isOpened():
            print("Video stream açılamadı:", self.url)
            return

        while self.running:
            ret, frame = cap.read()
            if not ret:
                self.msleep(10)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            self.frame_ready.emit(qimg)

            self.msleep(30)

        cap.release()

    def stop(self):
        self.running = False
        self.wait()


# ------------------- Main GUI -------------------
class arayuzBackend(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = SihaUI()
        self.ui.setupUi(self)

        # ----------------- Flight gauges -----------------
        self.airspeed = AirspeedGauge()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.airspeed)
        self.ui.airspeed_indicator.setLayout(layout)

        self.altimeter = AltimeterGauge()
        layout2 = QVBoxLayout()
        layout2.setContentsMargins(0, 0, 0, 0)
        layout2.addWidget(self.altimeter)
        self.ui.altimeter_indicator.setLayout(layout2)

        self.vsi = VerticalSpeedGauge()
        layout3 = QVBoxLayout()
        layout3.setContentsMargins(0, 0, 0, 0)
        layout3.addWidget(self.vsi)
        self.ui.vertical_speed_indicator.setLayout(layout3)

        self.attitude = AttitudeIndicator()
        layout4 = QVBoxLayout()
        layout4.setContentsMargins(0, 0, 0, 0)
        layout4.addWidget(self.attitude)
        self.ui.attitude_indicator.setLayout(layout4)

        self.compass = CompassIndicator()
        layout5 = QVBoxLayout()
        layout5.setContentsMargins(0, 0, 0, 0)
        layout5.addWidget(self.compass)
        self.ui.compass_indicator.setLayout(layout5)

        self.turn_widget = TurnCoordinatorIndicator()
        layout6 = QVBoxLayout()
        layout6.setContentsMargins(0, 0, 0, 0)
        layout6.addWidget(self.turn_widget)
        self.ui.turn_coordinator_indicator.setLayout(layout6)

        # Uydu HUD butonu
        self.ui.hud_uydu.clicked.connect(self.open_uydu_hud)

        # Kalkış/iniş butonları
        self.ui.otonom_kalkis.clicked.connect(self.start_takeoff)
        self.ui.otonom_inis.clicked.connect(self.start_land)

        # ----------------- Kamera canlı izleme -----------------
        # kamera sizin kamera alanı
        if hasattr(self.ui, "kamera"):
            self.ui.kamera.setScaledContents(True)

        self.video = VideoClient("http://127.0.0.1:8080/video")
        self.video.frame_ready.connect(self.on_frame)
        self.video.start()

        # ----------------- DroneKit bağlantısı -----------------
        self.connector = VehicleConnector("udp:127.0.0.1:14552")
        self.connector.connected.connect(self.on_vehicle_connected)
        self.connector.failed.connect(self.on_vehicle_failed)
        self.connector.start()

        # Demo timer (istersen kaldır)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gauge_demo)
        self.timer.start(200)

        self.vehicle = None
        self.flight = None
        self.reader = None

    def on_vehicle_connected(self, vehicle):
        self.vehicle = vehicle
        self.flight = FlightController(self.vehicle)

        self.reader = TelemetryReader(self.vehicle)
        self.reader.data_received.connect(self.update_ui_safely)
        self.reader.start()

    def on_vehicle_failed(self, err):
        print("DroneKit bağlantı hatası:", err)

    def update_ui_safely(self, data):
        try:
            # UI label isimleri sizde farklıysa çökmesin diye güvenli yazıyoruz
            if hasattr(self.ui, "enlem_label"):
                self.ui.enlem_label.setText(f"Enlem: {data['lat']:.6f}")
            if hasattr(self.ui, "boylam_label"):
                self.ui.boylam_label.setText(f"Boylam: {data['lon']:.6f}")
            if hasattr(self.ui, "irtifa_label"):
                self.ui.irtifa_label.setText(f"İrtifa: {data['alt']:.2f} m")

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

            # Gauge güncelle
            self.airspeed.setValue(data["air_speed"])
            self.altimeter.setAltitude(data["alt"])
        except Exception as e:
            print("GUI Güncelleme Hatası:", e)

    def on_frame(self, qimg):
        try:
            if not hasattr(self.ui, "kamera"):
                print("UI'da kamera bulunamadı! (Qt Designer objectName kontrol et)")
                return

            pix = QPixmap.fromImage(qimg)

            # kamera boyutuna sığdır
            w = max(1, self.ui.kamera.width())
            h = max(1, self.ui.kamera.height())
            pix = pix.scaled(w, h)

            self.ui.kamera.setPixmap(pix)

        except Exception as e:
            print("KAMERA LABEL HATASI:", e)

    def start_takeoff(self):
        if self.flight:
            self.flight.otonom_kalkis()

    def start_land(self):
        if self.flight:
            self.flight.otonom_inis()

    def open_uydu_hud(self):
        self.uydu_window = QMainWindow()
        self.uydu_ui = UyduHudUI()
        self.uydu_ui.setupUi(self.uydu_window)
        self.uydu_window.show()

    def update_gauge_demo(self):
        pass

    def closeEvent(self, event):
        try:
            if hasattr(self, "video") and self.video:
                self.video.stop()
            if hasattr(self, "reader") and self.reader:
                self.reader.stop()
            if hasattr(self, "vehicle") and self.vehicle:
                self.vehicle.close()
        except Exception:
            pass
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = arayuzBackend()
    w.show()
    sys.exit(app.exec_())
'''


















'''
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout
from PyQt5.QtCore import QTimer,QThread, pyqtSignal
from sihaArayuz import Ui_MainWindow as SihaUI
from Uydu_Hud_Ekrani import Ui_MainWindow as UyduHudUI
from gostergeler import AirspeedGauge, AltimeterGauge, VerticalSpeedGauge, AttitudeIndicator,CompassIndicator,TurnCoordinatorIndicator
from dronekit import connect
from flight_controller import FlightController



class arayuzBackend(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = SihaUI()
        self.ui.setupUi(self)

        print("Bağlanılıyor...")
        self.vehicle = connect('tcp:127.0.0.1:5762', wait_ready=True)

        self.flight = FlightController(self.vehicle)

        print("Bağlantı başarılı.")

        # sonradan eklendiiii
        # Queue oluştur
        self.telemetry_queue = Queue()

        QTimer.singleShot(100, self.start_telemetry_thread)


        # ---------------------------
        # AIRSPEED GAUGE OLUŞTUR
        # ---------------------------
        self.airspeed = AirspeedGauge()

        # airspeed_indicator widget'ı içine layout ekle
        layout = QVBoxLayout()                          # Yeni layout oluştur
        layout.setContentsMargins(0, 0, 0, 0)           # Kenarlıkları sıfırla
        layout.addWidget(self.airspeed)                 # Hızı gösterecek widget'ı ekle
        self.ui.airspeed_indicator.setLayout(layout)    # layout'u widget'a ata

        # ---------------------------
        # TIMER (SÜREKLİ ÇALIŞIR)
        # ---------------------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gauge)
        self.timer.start(200)

        # ---------------------------
        # ALTIMETER OLUŞTUR
        # ---------------------------
        self.altimeter = AltimeterGauge()

        layout2 = QVBoxLayout()
        layout2.setContentsMargins(0, 0, 0, 0)
        layout2.addWidget(self.altimeter)

        self.ui.altimeter_indicator.setLayout(layout2)


        self.compass = CompassIndicator()

        layout5 = QVBoxLayout()
        layout5.setContentsMargins(0, 0, 0, 0)
        layout5.addWidget(self.compass)

        self.ui.compass_indicator.setLayout(layout5)

        self.altimeter.setAltitude(3500)

        # ---------------------------
        # VERTICAL SPEED
        # ---------------------------
        self.vsi = VerticalSpeedGauge()

        layout3 = QVBoxLayout()
        layout3.setContentsMargins(0, 0, 0, 0)
        layout3.addWidget(self.vsi)

        self.ui.vertical_speed_indicator.setLayout(layout3)

        # ---------------------------
        # ATTITUDE INDICATOR
        # ---------------------------
        self.attitude = AttitudeIndicator()

        layout4 = QVBoxLayout()
        layout4.setContentsMargins(0, 0, 0, 0)
        layout4.addWidget(self.attitude)

        self.ui.attitude_indicator.setLayout(layout4)

        self.compass_indicator = CompassIndicator()
        self.ui.verticalLayout_5.addWidget(self.compass_indicator)

        self.turn_widget = TurnCoordinatorIndicator()
        self.ui.verticalLayout_6.addWidget(self.turn_widget)
        layout6 = QVBoxLayout()
        layout6.setContentsMargins(0, 0, 0, 0)
        layout6.addWidget(self.turn_widget)
        self.ui.turn_coordinator_indicator.setLayout(layout6)

        # Uydu HUD butonu sadece pencere açsın
        self.ui.hud_uydu.clicked.connect(self.open_uydu_hud)



        # bunlar sonra eklendiiii

        self.ui.otonom_kalkis.clicked.connect(self.start_takeoff)
        self.ui.otonom_inis.clicked.connect(self.start_land)



        # Flight controller
        self.flight = FlightController(self.vehicle)





    # Sürekli çalışan fonksiyon
    def update_gauge(self):
        self.airspeed.setValue(20)

    # Uydu HUD penceresi
    def open_uydu_hud(self):
        self.uydu_window = QMainWindow()
        self.uydu_ui = UyduHudUI()
        self.uydu_ui.setupUi(self.uydu_window)
        self.uydu_window.show()


    # sonradan eklendiii
    def start_takeoff(self):
        self.flight.otonom_kalkis()

    def start_land(self):
        self.flight.otonom_inis()
'''