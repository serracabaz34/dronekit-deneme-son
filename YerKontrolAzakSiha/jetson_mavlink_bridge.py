#!/usr/bin/env python3
# =============================================================================
#  MAVLINK KOMUT GÖNDERİCİ — MavlinkCommandSender
#
#  Görev  : Yer istasyonu arayüzündeki butonları Jetson (MAV_COMP_ID 191)
#           için COMMAND_LONG paketlerine dönüştürür ve DroneKit'in
#           vehicle._master.mav üzerinden RF telemetri radyosuna gönderir.
#
#  MİMARİ NOT:
#    - Ayrı bir UDP/TCP bağlantısı YOKTUR.
#    - Fiziksel yol: YKİ → RF Radyo → Orange Cube+ TELEM1
#                   Orange Cube+ (ArduPilot routing) → TELEM2 → Jetson
#    - Bu sınıf DroneKit'in halihazırda açık olan vehicle._master bağlantısını
#      yeniden kullanır. İkinci bir soket açmaz.
#
#  KULLANIM:
#    self.cmd_sender = MavlinkCommandSender()
#    # DroneKit bağlantısı kurulduktan sonra:
#    self.cmd_sender.set_vehicle(vehicle)
#    # Komut göndermek için:
#    self.cmd_sender.send_mission_mode(0)   # Otonom Kilitlenme (L7)
#    self.cmd_sender.send_abort()           # Kalkış/iniş güvenliği (L8)
#    self.cmd_sender.send_target_lock(18)   # Takım 18'e kilitlen
#
#  KOMUT NUMARALARI:
#    CMD_MISSION_MODE = 31011
#      param1=0 → searching_target=True    (L7 Arama/Kilitlenme)
#      param1=1 → kamikaze_authorized=True (L4 Kamikaze)
#      param1=2 → tüm flagler False        (L8 Devriye)
#      param1=3 → hss_active=True          (L3 HSS Kaçış)
#    CMD_MANUAL_LOCK = 31013
#      param1=<takim_id>
#
#  target_system    = 1    (ArduPilot sistem ID)
#  target_component = 191  (MAV_COMP_ID_ONBOARD_COMPUTER = Jetson)
# =============================================================================

from PyQt5.QtCore import QObject, pyqtSignal


class MavlinkCommandSender(QObject):
    """
    DroneKit vehicle referansı üzerinden Jetson'a COMMAND_LONG gönderir.
    QThread değildir — GUI thread'inde çalışır, bloklanmaz.
    """

    # Durum mesajı sinyali (arayüz terminaline yazdırmak için)
    status_message = pyqtSignal(str)

    # MAVLink sabit tanımları
    TARGET_SYSTEM    = 1    # ArduPilot
    TARGET_COMPONENT = 191  # MAV_COMP_ID_ONBOARD_COMPUTER (Jetson)

    CMD_MISSION_MODE = 31011
    CMD_MANUAL_LOCK  = 31013

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vehicle = None  # DroneKit vehicle referansı (dışarıdan verilir)

    # ------------------------------------------------------------------
    #  REFERANS ATAMA
    # ------------------------------------------------------------------

    def set_vehicle(self, vehicle):
        """
        DroneKit bağlantısı kurulduktan sonra çağrılır.
        on_vehicle_connected() içinde self.cmd_sender.set_vehicle(vehicle)
        satırıyla çağrılmalıdır.
        """
        self._vehicle = vehicle
        self.status_message.emit("[MAVLINK] Komut gönderici DroneKit'e bağlandı.")

    # ------------------------------------------------------------------
    #  TEMEL GÖNDERİCİ
    # ------------------------------------------------------------------

    def _send_command_long(self, command_id: int, param1: float = 0.0,
                           param2: float = 0.0, param3: float = 0.0,
                           param4: float = 0.0, param5: float = 0.0,
                           param6: float = 0.0, param7: float = 0.0) -> bool:
        """
        vehicle._master.mav.command_long_send() ile Jetson'a (compID=191)
        COMMAND_LONG paketi gönderir.

        Returns:
            True  → Başarılı gönderim
            False → vehicle bağlı değil veya hata oluştu
        """
        if self._vehicle is None:
            self.status_message.emit(
                f"[MAVLINK UYARI] Komut gönderilemedi (command={command_id}): "
                "DroneKit bağlantısı henüz kurulmadı. "
                "on_vehicle_connected() içinde set_vehicle() çağrıldı mı?"
            )
            return False

        try:
            self._vehicle._master.mav.command_long_send(
                self.TARGET_SYSTEM,    # target_system  = 1 (ArduPilot)
                self.TARGET_COMPONENT, # target_component = 191 (Jetson)
                command_id,            # komut numarası
                0,                     # confirmation = 0
                float(param1),
                float(param2),
                float(param3),
                float(param4),
                float(param5),
                float(param6),
                float(param7),
            )
            return True

        except Exception as exc:
            self.status_message.emit(
                f"[MAVLINK HATA] command_long_send() başarısız "
                f"(command={command_id}): {exc}"
            )
            return False

    # ------------------------------------------------------------------
    #  GÖREV MODU KOMUTLARI
    # ------------------------------------------------------------------

    def send_mission_mode(self, mode_code: int):
        """
        CMD_MISSION_MODE (31011) — Jetson BT seviyesini değiştirir.

        mode_code:
            0 → searching_target=True    (BT L7 Arama/Kilitlenme)
            1 → kamikaze_authorized=True (BT L4 Kamikaze)
            2 → tüm flagler False        (BT L8 Devriye fallback)
            3 → hss_active=True          (BT L3 HSS Kaçış)

        gcs_bridge_node.py bu komutu alır, doğru ROS2 topic'ine çevirir.
        """
        MODE_NAMES = {
            0: "Otonom Kilitlenme (L7)",
            1: "Kamikaze (L4)",
            2: "Rota İzle / Durdur (L8)",
            3: "HSS'den Kaçış (L3)",
        }
        mode_name = MODE_NAMES.get(mode_code, f"Bilinmeyen mod ({mode_code})")

        success = self._send_command_long(self.CMD_MISSION_MODE, param1=float(mode_code))
        if success:
            self.status_message.emit(f"[MAVLINK] Görev modu gönderildi: {mode_name}")

    def send_target_lock(self, team_id: int):
        """
        CMD_MANUAL_LOCK (31013) — Belirli bir rakip takıma kilitlenme emri.

        gcs_bridge_node.py bu komutu alır:
          - /siha/cmd_lock_target_id (Int32) yayınlar
          - /siha/lock_in_progress=True yayınlar → BT L5 (Saldırı) seviyesine geçer
        """
        success = self._send_command_long(self.CMD_MANUAL_LOCK, param1=float(team_id))
        if success:
            self.status_message.emit(
                f"[MAVLINK] Kilitlenme emri gönderildi: Hedef Takım ID={team_id}"
            )

    def send_abort(self):
        """
        Güvenlik komutu — mode_code=2 göndererek tüm BT flaglerini False yapar.
        BT L8 (Devriye fallback) seviyesine düşer; drone waypoint almayı durdurur.

        Kalkış, iniş ve manuel mod geçişlerinden ÖNCE çağrılmalıdır:
            start_takeoff() → send_abort() çağırır
            start_land()    → send_abort() çağırır
            set_mode("MANUAL") vb. → send_abort() çağırır

        NOT: mode_code=2 → gcs_bridge_node.py'de tüm Bool'lar False → BT L8.
        Bu güvenlik durumunda BT drone'a aktif komut göndermez.
        """
        success = self._send_command_long(self.CMD_MISSION_MODE, param1=2.0)
        if success:
            self.status_message.emit(
                "[GÜVENLİK] BT durdurma komutu gönderildi "
                "(mode_code=2 → tüm flagler False → L8 Devriye)"
            )
