from dronekit import VehicleMode, LocationGlobalRelative, Command
import time
import math
from pymavlink import mavutil


def meters_to_lat(m):
    return m / 111111.0


def meters_to_lon(m, lat_deg):
    return m / (111111.0 * math.cos(math.radians(lat_deg)))


class FlightController:
    def __init__(self, vehicle):
        self.vehicle = vehicle

        # Safety eşikleri
        self.batt_crit = 20
        self.signal_crit = 25

        self.force_rtl = False
        self.landing_active = False

    def _set_mode(self, mode_name: str, timeout=10):
        self.vehicle.mode = VehicleMode(mode_name)
        t0 = time.time()
        while self.vehicle.mode.name != mode_name:
            if time.time() - t0 > timeout:
                raise RuntimeError(f"Mode değişmedi: {mode_name} (şu an: {self.vehicle.mode.name})")
            time.sleep(0.2)

    def _clear_landing_sequence(self):
        try:
            cmds = self.vehicle.commands
            cmds.download()
            cmds.wait_ready(timeout=3)
        except Exception:
            pass

        # next'i sıfırla (mission pointer)
        try:
            self.vehicle.commands.next = 0
        except Exception:
            pass

        # misyonu tamamen temizlemeyi dene
        try:
            self.vehicle.commands.clear()
            self.vehicle.commands.upload()
        except Exception:
            # Her firmware/bağlantıda clear/upload kusursuz çalışmayabilir
            pass

        self.landing_active = False
        # force_rtl'yi burada sıfırlamak mantıklı (yeni uçuş)
        self.force_rtl = False

    def safety_check(self, battery_percent, signal_percent):
        if self.force_rtl:
            return

        batt_bad = battery_percent is not None and battery_percent < self.batt_crit
        sig_bad = signal_percent is not None and signal_percent < self.signal_crit

        if batt_bad or sig_bad:
            reason = []
            if batt_bad:
                reason.append(f"BAT<{self.batt_crit}%")
            if sig_bad:
                reason.append(f"SIG<{self.signal_crit}%")

            print("ACİL DURUM! -> RTL |", ",".join(reason))
            self.force_rtl = True
            self.landing_active = False
            self._set_mode("RTL", timeout=10)

    def otonom_kalkis(self, target_altitude=30):
        """
        Sadece uçağı Arm eder, TAKEOFF moduna alır ve belirlenen kalkış irtifasına tırmanmasını sağlar.
        Herhangi bir rota/waypoint takibi yapmaz ve RTL moduna geçmez.
        """
        v = self.vehicle

        # Önceki görev veya iniş sekansını temizle
        self._clear_landing_sequence()

        print("TAKEOFF moduna alınıyor...")
        self._set_mode("TAKEOFF", timeout=10)

        t0 = time.time()
        while not v.is_armable and time.time() - t0 < 10:
            print("Armable bekleniyor... (GPS/EKF/kalibrasyon)")
            time.sleep(1)

        print("Motor arm ediliyor...")
        v.armed = True

        t0 = time.time()
        while not v.armed and time.time() - t0 < 10:
            print("Armlanamadı, bekleniyor... (PreArm mesajlarına bak)")
            time.sleep(1)

        if not v.armed:
            raise RuntimeError("Arm başarısız. Mission Planner'da çıkan PreArm sebebini kontrol et.")

        print(f"Kalkış yapılıyor. Tırmanış bekleniyor (Hedef irtifa: ~{target_altitude}m)...")

        # Uçağın güvenli bir şekilde kalkış yapıp irtifa alması için bekleme
        t0 = time.time()
        while time.time() - t0 < 8:
            curr_alt = v.location.global_relative_frame.alt if v.location.global_relative_frame else 0
            print(f"Anlık İrtifa: {curr_alt:.1f}m")
            time.sleep(1.5)

        print("Sadece kalkış işlemi tamamlandı. Araç komut bekleme modunda/FBWA/TAKEOFF tırmanışında devam ediyor.")

    def goto_offset(self, d_north_m=30, d_east_m=30, alt=60):
        v = self.vehicle
        loc = v.location.global_relative_frame

        # gps koordinatına dönüştürme
        lat = float(loc.lat) + meters_to_lat(d_north_m)
        lon = float(loc.lon) + meters_to_lon(d_east_m, float(loc.lat))

        target = LocationGlobalRelative(lat, lon, alt)
        print("Waypoint'e gidiliyor:", lat, lon, alt)
        v.simple_goto(target)

    def rtl(self):
        print("RTL moda geçiliyor...")
        self.landing_active = False
        self.force_rtl = True
        self._set_mode("RTL", timeout=10)

    def planli_inis(self, land_lat=None, land_lon=None, approach_alt=60, approach_dist_m=300):
        """
        Aracı AUTOLAND uçuş moduna alarak otomatik iniş sürecini başlatır
        ve arayüz/konsol çıktılarını bu modla senkronize eder.
        """
        print("Otomatik İniş (AUTOLAND) süreci başlatılıyor...")

        # Özel bir koordinat verildiyse önce aracı yaklaşma pozisyonuna yönlendir
        if land_lat is not None and land_lon is not None:
            print(f"Hedef iniş koordinatına yönlendiriliyor: {land_lat}, {land_lon}")
            target_location = LocationGlobalRelative(float(land_lat), float(land_lon), approach_alt)
            self.vehicle.simple_goto(target_location)
            time.sleep(2)

        self.landing_active = True
        self.force_rtl = False

        # Uçuş modunu AUTOLAND olarak ayarla
        success = self._set_mode("AUTOLAND", timeout=10)

        # Otopilottaki anlık aktif modu doğrula
        current_mode = getattr(self.vehicle.mode, 'name', 'UNKNOWN')

        if success or current_mode == "AUTOLAND":
            print(f"Başarılı: Araç {current_mode} moduna alındı. Otomatik iniş yapılıyor...")
            return True
        else:
            print(f"HATA: Mod değiştirilemedi! Mevcut Mod: {current_mode}")
            return False