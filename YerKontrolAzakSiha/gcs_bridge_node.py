#!/usr/bin/env python3
# =============================================================================
#  GCS KÖPRÜ DÜĞÜMÜ — MAVLink ↔ ROS 2 Tam Telemetri Köprüsü
#
#  Arayüzdeki Görev, Uçuş ve Kilitlenme Butonlarına Göre Özelleştirilmiştir.
# =============================================================================

import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String, Float32, Int32

from pymavlink import mavutil


# #############################################################################
#  SABİTLER VE KOMUT NUMARALARI
# #############################################################################

SYSTEM_ID = 1
COMPONENT_ID = 191          # MAV_COMP_ID_ONBOARD_COMPUTER
DEFAULT_CONNECTION = "udpin:0.0.0.0:14550"

# Standart MAVLink Komutları
MAV_CMD_NAV_TAKEOFF = 22
MAV_CMD_NAV_LAND    = 21

# Özel Komut Numaraları (YKİ → Jetson)
CMD_MISSION_MODE = 31011    # param1: 0=KİLİTLENME, 1=KAMİKAZE, 2=ROTA_İZLE, 3=HSS_KACIS
CMD_MANUAL_LOCK  = 31013    # param1: Kilitlenecek Hedef Takım ID

# Görev Modu Eşlemesi
MISSION_MODE_MAP = {
    0: "AUTONOMOUS_LOCK",
    1: "KAMIKAZE",
    2: "WAYPOINT_PATROL",  # Rota İzle (Varsayılan / İptal durumu)
    3: "HSS_EVADE",        # HSS'den Kaçış
}

# MAVLink Sabitleri
SEVERITY_WARNING = 4
SEVERITY_INFO    = 6
MAV_TYPE_FIXED_WING = 1
MAV_AUTOPILOT_ARDUPILOT = 3
TELEMETRY_SEND_PERIOD_SEC = 0.5  # 2 Hz sayısal veri hızı


# #############################################################################
#  ANA KÖPRÜ DÜĞÜMÜ
# #############################################################################

class GcsBridgeNode(Node):

    def __init__(self):
        super().__init__("gcs_bridge")

        self.declare_parameter("connection_string", DEFAULT_CONNECTION)
        self._conn_str = self.get_parameter("connection_string").get_parameter_value().string_value

        self._mav = None
        self._connected = False
        self._shutdown = False
        self._lock = threading.Lock()
        self._boot_time_ms = int(time.monotonic() * 1000)

        # ══════════════════════════════════════════════════════════════════
        #  YAYINCILAR (Arayüzden Gelen Komutlar → ROS 2 Sistemine)
        # ══════════════════════════════════════════════════════════════════
        self.pub_mission_mode = self.create_publisher(String, "/siha/mission_mode", 10)
        self.pub_takeoff      = self.create_publisher(Bool, "/siha/cmd_takeoff", 10)
        self.pub_land         = self.create_publisher(Bool, "/siha/cmd_land", 10)
        self.pub_target_lock  = self.create_publisher(Int32, "/siha/cmd_lock_target_id", 10)

        # ══════════════════════════════════════════════════════════════════
        #  ABONELİKLER (Jetson Verileri → Arayüzdeki "Kilitlenme Bilgileri")
        # ══════════════════════════════════════════════════════════════════
        self._lock_status = "N/A"
        self._lock_duration = 0.0
        self._lock_count = 0

        self.create_subscription(String, "/siha/lock_status", lambda m: setattr(self, '_lock_status', m.data), 10)
        self.create_subscription(Float32, "/siha/lock_elapsed_sec", lambda m: setattr(self, '_lock_duration', m.data), 10)
        self.create_subscription(Int32, "/siha/lock_count", lambda m: setattr(self, '_lock_count', m.data), 10)

        # Metinsel Bildirimler (STATUSTEXT)
        self.create_subscription(String, "/siha/system_warning", self._on_system_warning, 10)

        # ══════════════════════════════════════════════════════════════════
        #  ZAMANLAYICILAR VE THREAD
        # ══════════════════════════════════════════════════════════════════
        self._hb_timer = self.create_timer(1.0, self._send_heartbeat)
        self._telem_timer = self.create_timer(TELEMETRY_SEND_PERIOD_SEC, self._send_numeric_telemetry)

        self._open_connection()

        self._recv_thread = threading.Thread(target=self._receive_loop, name="mavlink_recv", daemon=True)
        self._recv_thread.start()

        self.get_logger().info(f"GCS Bridge baslatildi → {self._conn_str}")

    # =================================================================
    #  BAĞLANTI YÖNETİMİ
    # =================================================================

    def _open_connection(self):
        try:
            self._mav = mavutil.mavlink_connection(self._conn_str, source_system=SYSTEM_ID, source_component=COMPONENT_ID)
            self._connected = True
            self.get_logger().info("MAVLink baglantisi kuruldu.")
        except Exception as exc:
            self._connected = False
            self.get_logger().error(f"MAVLink baglanti hatasi: {exc}")

    def _reconnect(self):
        self._connected = False
        time.sleep(2.0)
        self._open_connection()

    # =================================================================
    #  ALICI DÖNGÜSÜ VE GELEN KOMUT İŞLEYİCİ
    # =================================================================

    def _receive_loop(self):
        while not self._shutdown:
            if not self._connected or self._mav is None:
                self._reconnect()
                continue

            try:
                # type="COMMAND_LONG" filtresini kaldırıyoruz, gelen her MAVLink mesajını yakalayalım
                msg = self._mav.recv_match(blocking=True, timeout=1.0)
                if msg is None:
                    continue

                # TERMINAL ÇIKTISI 1: WSL'e herhangi bir MAVLink verisi ulaştı mı?
                self.get_logger().info(f"[PAKET GELDI] Mesaj Tipi: {msg.get_type()}")

                # Eğer gelen paket bir KOMUT ise detayını bas
                if msg.get_type() == "COMMAND_LONG":
                    self.get_logger().info(f"==> [BUTON TETIKLENDI] Command ID: {msg.command}, Param1: {msg.param1}")
                    self._handle_command(msg)

            except Exception as exc:
                self.get_logger().error(f"Alim hatasi: {exc}")
                time.sleep(0.1)

    def _handle_command(self, msg):
        cmd = msg.command

        # 1. Görev Modu Değişiklikleri (Kamikaze, Otonom Kilitlenme, Rota İzle, HSS Kaçış)
        if cmd == CMD_MISSION_MODE:
            mode_code = int(msg.param1)
            mode_str = MISSION_MODE_MAP.get(mode_code, "WAYPOINT_PATROL")

            out = String()
            out.data = mode_str
            self.pub_mission_mode.publish(out)
            self._send_ack(cmd, mavutil.mavlink.MAV_RESULT_ACCEPTED)
            self._send_statustext(f"MOD:{mode_str}", SEVERITY_INFO)

            self.get_logger().info(f"[GELEN KOMUT] Gorev Modu Degisti: {mode_str} (Kod: {mode_code})")

        # 2. Otonom Kalkış
        elif cmd == MAV_CMD_NAV_TAKEOFF:
            out = Bool()
            out.data = True
            self.pub_takeoff.publish(out)
            self._send_ack(cmd, mavutil.mavlink.MAV_RESULT_ACCEPTED)
            self._send_statustext("KALKIS BASLATILDI", SEVERITY_INFO)

        # 3. Otonom İniş
        elif cmd == MAV_CMD_NAV_LAND:
            out = Bool()
            out.data = True
            self.pub_land.publish(out)
            self._send_ack(cmd, mavutil.mavlink.MAV_RESULT_ACCEPTED)
            self._send_statustext("INIS BASLATILDI", SEVERITY_INFO)

        # 4. Seçilen Takıma Kilitlen Butonu
        elif cmd == CMD_MANUAL_LOCK:
            target_id = int(msg.param1)
            out = Int32()
            out.data = target_id
            self.pub_target_lock.publish(out)
            self._send_ack(cmd, mavutil.mavlink.MAV_RESULT_ACCEPTED)
            self._send_statustext(f"HEDEF SECILDI:{target_id}", SEVERITY_INFO)

    # =================================================================
    #  GİDEN TELEMETRİ (Jetson → Arayüz)
    # =================================================================

    def _send_numeric_telemetry(self):
        """Arayüzdeki 'Kilitlenme Bilgileri' kutularını doldurmak için veri yollar."""
        if not self._connected or self._mav is None:
            return

        now_ms = int(time.monotonic() * 1000) - self._boot_time_ms

        # Arayüzün okuyacağı sayısal anahtarlar
        values = {
            "LCK_DUR": float(self._lock_duration),  # Kilitlenme Süresi (sn)
            "LCK_CNT": float(self._lock_count),     # Kilitlenme Sayısı
        }

        try:
            with self._lock:
                for name, val in values.items():
                    self._mav.mav.named_value_float_send(
                        time_boot_ms=now_ms,
                        name=name.encode("ascii"),
                        value=float(val),
                    )
        except Exception:
            pass

    def _send_heartbeat(self):
        if not self._connected or self._mav is None:
            return
        try:
            with self._lock:
                self._mav.mav.heartbeat_send(
                    type=MAV_TYPE_FIXED_WING,
                    autopilot=MAV_AUTOPILOT_ARDUPILOT,
                    base_mode=mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                    custom_mode=0,
                    system_status=mavutil.mavlink.MAV_STATE_ACTIVE,
                )
        except Exception:
            self._connected = False

    def _on_system_warning(self, msg: String):
        self._send_statustext(f"UYARI:{msg.data}", SEVERITY_WARNING)

    def _send_statustext(self, text: str, severity: int = SEVERITY_INFO):
        if not self._connected or self._mav is None:
            return
        try:
            with self._lock:
                self._mav.mav.statustext_send(severity=severity, text=text[:50].encode("utf-8"))
        except Exception:
            pass

    def _send_ack(self, command: int, result: int):
        if not self._connected or self._mav is None:
            return
        try:
            with self._lock:
                self._mav.mav.command_ack_send(command=command, result=result)
        except Exception:
            pass

    def destroy_node(self):
        self._shutdown = True
        if self._recv_thread.is_alive():
            self._recv_thread.join(timeout=2.0)
        try:
            if self._mav is not None:
                self._mav.close()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GcsBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()