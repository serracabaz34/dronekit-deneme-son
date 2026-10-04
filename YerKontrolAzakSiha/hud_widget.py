# hud_widget.py
# hud_widget.py
import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont,
    QPolygon
)
from PyQt5.QtCore import Qt, QRectF, QPoint

RAD2DEG = 57.29577951308232


class HudWidget(QWidget):
    """
    Mission Planner benzeri HUD (QPainter):
    - Sky/Ground + horizon (roll rotate, pitch translate)
    - Pitch ladder (MP benzeri)
    - Üstte Heading band (kayan)
    - Solda Speed tape
    - Sağda Altitude tape
    - Merkezde flight path marker + crosshair
    - Sol altta AS/GS, sağ altta ALT, üstte DISARMED/ARMED
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(480, 320)

        # telemetry
        self.roll_deg = 0.0
        self.pitch_deg = 0.0
        self.yaw_deg = 0.0
        self.airspeed = 0.0
        self.groundspeed = 0.0
        self.altitude = 0.0

        self.status_text = "DISARMED"
        self.mode_text = ""
        self.warn_text = ""

        # tuning
        self.px_per_deg = 4.2  # pitch scaling

    def set_telemetry(self, roll_deg=None, pitch_deg=None, yaw_deg=None,
                      airspeed=None, groundspeed=None, altitude=None,
                      status_text=None, mode_text=None, warn_text=None):
        if roll_deg is not None: self.roll_deg = float(roll_deg)
        if pitch_deg is not None: self.pitch_deg = float(pitch_deg)
        if yaw_deg is not None: self.yaw_deg = float(yaw_deg) % 360.0
        if airspeed is not None: self.airspeed = float(airspeed)
        if groundspeed is not None: self.groundspeed = float(groundspeed)
        if altitude is not None: self.altitude = float(altitude)
        if status_text is not None: self.status_text = str(status_text)
        if mode_text is not None: self.mode_text = str(mode_text)
        if warn_text is not None: self.warn_text = str(warn_text)
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        # ---- Layout oranları (MP hissi için) ----
        band_h = int(h * 0.11)
        tape_w = int(w * 0.10)

        # HUD tüm alanı kaplasın (siyah boşluk olmasın)
        hud_rect = QRectF(0, 0, w, h)

        # background
        p.fillRect(0, 0, w, h, QColor(35, 35, 35))


        # --- 1) Attitude katmanı: sadece hud_rect içinde çiz ---
        p.save()
        p.setClipRect(hud_rect)

        cx = hud_rect.center().x()
        cy = hud_rect.center().y()

        p.translate(cx, cy)
        p.rotate(-self.roll_deg)  # roll
        p.translate(0, self.pitch_deg * self.px_per_deg)  # pitch

        # sky/ground
        big = max(w, h) * 3
        sky = QRectF(-big/2, -big/2, big, big/2)
        ground = QRectF(-big/2, 0, big, big/2)
        p.fillRect(sky, QColor(90, 150, 230))
        p.fillRect(ground, QColor(120, 95, 45))

        # horizon line
        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.drawLine(int(-big/2), 0, int(big/2), 0)

        # pitch ladder
        self._draw_pitch_ladder_mp(p, hud_rect.width(), hud_rect.height())

        p.restore()

        # --- 2) Overlay: heading band + tapes + center markers ---
        # --- 2) Overlay: heading band + tapes + bank arc ---
        pad = 8
        sky_offset = int(h * 0.04)  # sky içine indirme miktarı

        band_rect = QRectF(
            pad,
            sky_offset,
            hud_rect.width() - 2 * pad,
            band_h
        )
        self._draw_heading_band(p, band_rect)

        left_tape = QRectF(pad, band_rect.bottom() + 6, tape_w, hud_rect.height() - (band_rect.bottom() + 6) - pad)
        right_tape = QRectF(hud_rect.width() - tape_w - pad, band_rect.bottom() + 6, tape_w,
                            hud_rect.height() - (band_rect.bottom() + 6) - pad)

        self._draw_speed_tape(p, left_tape)
        self._draw_alt_tape(p, right_tape)

        self._draw_bank_arc(p, hud_rect, band_rect)

        # merkez markerlar hud_rect içinde
        self._draw_center_overlay(p, hud_rect)

        # alt yazılar
        self._draw_status_texts(p, w, h, hud_rect)

        p.end()

    # ---------------- visuals ----------------
    def _draw_panel_frame(self, p: QPainter, rect: QRectF):
        p.setPen(QPen(QColor(80, 120, 170, 120), 2))
        p.setBrush(QBrush(QColor(0, 0, 0, 0)))
        p.drawRoundedRect(rect.adjusted(-3, -3, 3, 3), 6, 6)

    def _draw_pitch_ladder_mp(self, p: QPainter, rw: float, rh: float):
        """
        Daha sade HUD pitch ladder:
        - Sadece: 10, 0, -10, -20, -30 etiketli
        - Çizgiler daha kısa ve daha az
        """
        white = QColor(245, 245, 245, 220)
        p.setPen(QPen(white, 2))
        p.setFont(QFont("Arial", 10, QFont.Bold))

        half = min(rw, rh) * 0.22  # daha kısa çizgiler

        levels = [10, 0, -10, -20, -30]
        for deg in levels:
            y = -deg * self.px_per_deg

            # 0 çizgisi kalın
            if deg == 0:
                p.setPen(QPen(QColor(255, 255, 255, 230), 3))
            else:
                p.setPen(QPen(white, 2))

            p.drawLine(int(-half), int(y), int(half), int(y))

            # sadece 0 dışındakilere sayı bas
            if deg != 0:
                p.drawText(int(-half - 36), int(y + 5), f"{deg}")
                p.drawText(int(half + 10), int(y + 5), f"{deg}")

    def _draw_heading_band(self, p: QPainter, rect: QRectF):
        # band background
        p.setPen(Qt.NoPen)
        # Şeffaf overlay band
        p.setBrush(QBrush(QColor(230, 230, 230, 110)))  # alpha 0-255
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, 6, 6)

        # ticks
        p.setPen(QPen(QColor(20, 20, 20, 200), 2))
        p.setFont(QFont("Arial", 10, QFont.Bold))

        center_x = rect.center().x()
        # 5° tick spacing
        px_per_deg = rect.width() / 90.0  # ekranda ~90 derece göster
        start_deg = self.yaw_deg - 45
        end_deg = self.yaw_deg + 45

        # major ticks 10°, minor 5°
        d = int(math.floor(start_deg / 5) * 5)
        while d <= end_deg:
            x = center_x + (d - self.yaw_deg) * px_per_deg
            if rect.left() <= x <= rect.right():
                is10 = (d % 10 == 0)
                tick_h = rect.height() * (0.55 if is10 else 0.35)
                p.drawLine(int(x), int(rect.bottom()), int(x), int(rect.bottom() - tick_h))

                if is10:
                    label = self._heading_label(d % 360)
                    p.drawText(int(x - 12), int(rect.top() + 16), label)
            d += 5

        # center caret (kırmızı üçgen)
        p.setBrush(QBrush(QColor(255, 0, 0)))
        p.setPen(Qt.NoPen)
        tri = QPolygon([
            QPoint(int(center_x), int(rect.bottom() - 2)),
            QPoint(int(center_x - 7), int(rect.bottom() - 14)),
            QPoint(int(center_x + 7), int(rect.bottom() - 14)),
        ])
        p.drawPolygon(tri)

        # HDG text
        p.setPen(QPen(QColor(0, 0, 0), 1))
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(int(rect.center().x() - 35), int(rect.top() + rect.height() - 4), f"HDG {self.yaw_deg:05.1f}")

    def _heading_label(self, deg: float) -> str:
        # MP gibi N/E/S/W + ara değerler
        d = int(round(deg)) % 360
        if d == 0: return "N"
        if d == 90: return "E"
        if d == 180: return "S"
        if d == 270: return "W"
        # ara etiketleri de ekleyelim
        if d == 45: return "NE"
        if d == 135: return "SE"
        if d == 225: return "SW"
        if d == 315: return "NW"
        return str(d)

    def _draw_speed_tape(self, p: QPainter, rect: QRectF):
        # Tape panel
        p.setPen(QPen(QColor(0, 0, 0), 1))
        # Şeffaf overlay panel
        p.setBrush(QBrush(QColor(235, 235, 235, 110)))
        p.setPen(QPen(QColor(0, 0, 0, 120), 1))
        p.drawRoundedRect(rect, 6, 6)

        # İç pencere (tam boy değil!)
        win_h = rect.height() * 0.62
        win = QRectF(rect.left() + 6, rect.center().y() - win_h / 2, rect.width() - 12, win_h)

        # pencere çerçevesi
        p.setBrush(QBrush(QColor(250, 250, 250, 140)))
        p.setPen(QPen(QColor(0, 0, 0, 140), 2))
        p.drawRoundedRect(win, 4, 4)

        # başlık
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(int(rect.left() + 10), int(rect.top() + 18), "AS")

        # Ölçek: sadece pencere içinde çiz (clip)
        p.save()
        p.setClipRect(win)

        base = self.airspeed
        px_per_unit = win.height() / 24.0  # pencerede yaklaşık 24 m/s görünür (MP gibi kompakt)

        # çizilecek aralık (base +-12)
        start = int(math.floor(base - 12))
        end = int(math.ceil(base + 12))

        p.setPen(QPen(QColor(0, 0, 0), 2))
        for v in range(start, end + 1):
            y = win.center().y() - (v - base) * px_per_unit
            if v % 5 == 0:
                tick = win.width() * 0.55
                p.drawLine(int(win.right() - tick), int(y), int(win.right()), int(y))
                p.setFont(QFont("Arial", 9, QFont.Bold))
                p.drawText(int(win.left() + 6), int(y + 4), f"{v}")
            else:
                tick = win.width() * 0.30
                p.drawLine(int(win.right() - tick), int(y), int(win.right()), int(y))

        p.restore()

        # Orta “ok” (sabit pointer)
        p.setPen(QPen(QColor(0, 0, 0), 2))
        mid_y = win.center().y()
        p.drawLine(int(win.right() - win.width() * 0.18), int(mid_y), int(win.right()), int(mid_y))

        # Büyük değer kutusu
        box = QRectF(rect.left() + 8, rect.center().y() - 16, rect.width() - 16, 32)
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.setPen(QPen(QColor(0, 0, 0), 2))
        p.drawRect(box)
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.drawText(box, Qt.AlignCenter, f"{self.airspeed:.1f}")

    def _draw_alt_tape(self, p: QPainter, rect: QRectF):
        p.setPen(QPen(QColor(0, 0, 0), 1))
        p.setBrush(QBrush(QColor(235, 235, 235, 110)))
        p.setPen(QPen(QColor(0, 0, 0, 120), 1))
        p.drawRoundedRect(rect, 6, 6)

        win_h = rect.height() * 0.62
        win = QRectF(rect.left() + 6, rect.center().y() - win_h / 2, rect.width() - 12, win_h)

        p.setBrush(QBrush(QColor(250, 250, 250, 140)))
        p.setPen(QPen(QColor(0, 0, 0, 140), 2))
        p.drawRoundedRect(win, 4, 4)

        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(int(rect.left() + 10), int(rect.top() + 18), "ALT")

        p.save()
        p.setClipRect(win)

        base = self.altitude
        px_per_m = win.height() / 80.0  # pencerede ~80m görünür

        start = int(math.floor(base - 40))
        end = int(math.ceil(base + 40))

        p.setPen(QPen(QColor(0, 0, 0), 2))
        for v in range(start, end + 1, 2):  # 2m adım (daha sık ama az yazı)
            y = win.center().y() - (v - base) * px_per_m
            if v % 10 == 0:
                tick = win.width() * 0.55
                p.drawLine(int(win.left()), int(y), int(win.left() + tick), int(y))
                p.setFont(QFont("Arial", 9, QFont.Bold))
                p.drawText(int(win.left() + tick + 4), int(y + 4), f"{v}")
            else:
                tick = win.width() * 0.30
                p.drawLine(int(win.left()), int(y), int(win.left() + tick), int(y))

        p.restore()

        # Sabit pointer çizgisi
        p.setPen(QPen(QColor(0, 0, 0), 2))
        mid_y = win.center().y()
        p.drawLine(int(win.left()), int(mid_y), int(win.left() + win.width() * 0.18), int(mid_y))

        # Değer kutusu
        box = QRectF(rect.left() + 8, rect.center().y() - 16, rect.width() - 16, 32)
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.setPen(QPen(QColor(0, 0, 0), 2))
        p.drawRect(box)
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.drawText(box, Qt.AlignCenter, f"{self.altitude:.1f}")

    def _draw_center_overlay(self, p: QPainter, hud_rect: QRectF):
        # crosshair + flight path marker (Mission Planner hissi)
        cx = hud_rect.center().x()
        cy = hud_rect.center().y()

        # crosshair (kırmızı/yeşil karışık istemiyorsan tek renk yapabiliriz)
        p.setPen(QPen(QColor(255, 0, 0), 2))
        p.drawLine(int(cx - 55), int(cy), int(cx - 15), int(cy))
        p.drawLine(int(cx + 15), int(cy), int(cx + 55), int(cy))
        p.drawLine(int(cx), int(cy - 12), int(cx), int(cy + 12))

        # flight path marker (yeşil küçük)
        p.setPen(QPen(QColor(0, 255, 0), 2))
        r = 10
        p.drawEllipse(QPoint(int(cx), int(cy)), r, r)
        p.drawLine(int(cx - 18), int(cy), int(cx - 6), int(cy))
        p.drawLine(int(cx + 6), int(cy), int(cx + 18), int(cy))

    def _draw_status_texts(self, p: QPainter, w: int, h: int, hud_rect: QRectF):
        # Üst sol: status
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.setPen(QPen(QColor(255, 0, 0), 2))
        p.drawText(int(hud_rect.left() + 8), int(hud_rect.top() + 18), self.status_text)

        # Üst sağ: mode (istersen)
        if self.mode_text:
            p.setPen(QPen(QColor(255, 255, 255), 1))
            p.setFont(QFont("Arial", 10, QFont.Bold))
            p.drawText(int(hud_rect.right() - 120), int(hud_rect.top() + 18), self.mode_text)

        # Alt sol: AS/GS
        p.setPen(QPen(QColor(255, 255, 255), 1))
        p.setFont(QFont("Arial", 10))
        p.drawText(int(hud_rect.left() + 8), int(hud_rect.bottom() - 28), f"AS {self.airspeed:.1f} m/s")
        p.drawText(int(hud_rect.left() + 8), int(hud_rect.bottom() - 10), f"GS {self.groundspeed:.1f} m/s")

        # Alt sağ: ALT
        p.drawText(int(hud_rect.right() - 140), int(hud_rect.bottom() - 10), f"ALT {self.altitude:.1f} m")

        # Warn
        if self.warn_text:
            p.setPen(QPen(QColor(255, 120, 120), 2))
            p.setFont(QFont("Arial", 10, QFont.Bold))
            p.drawText(int(hud_rect.left() + 8), int(hud_rect.bottom() - 46), self.warn_text)

    def _draw_bank_arc(self, p: QPainter, hud_rect: QRectF, band_rect: QRectF):
        """
        Taşmayan, üstte yay üzerinde tick + etiketli bank göstergesi
        Etiketler: 60 45 30 20 10 0 10 20 30 45 60
        """
        # sadece üst band bölgesinde kalsın
        p.save()
        p.setClipRect(hud_rect)

        cx = hud_rect.center().x()
        top = band_rect.bottom() + 80  # band’in hemen altından başlasın
        r = min(hud_rect.width(), hud_rect.height()) * 0.30
        arc_cy = top + r * 0.55

        rect = QRectF(cx - r, arc_cy - r, 2 * r, 2 * r)

        # Yay çizgisi (tek)
        # Ana yay çizgisi (ticklerin "zemini")
        p.setPen(QPen(QColor(255, 255, 255, 120), 6))
        #p.drawArc(rect, int(210 * 16), int(120 * 16))

        p.setPen(QPen(QColor(255, 255, 255, 230), 2))
        # p.drawArc(rect, int(210 * 16), int(120 * 16))

        # Tick'ler + etiketler
        ticks = [60, 45, 30, 20, 10, 0, 10, 20, 30, 45, 60]
        angles = [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]

        p.setPen(QPen(QColor(255, 255, 255, 220), 3))
        p.setFont(QFont("Arial", 9, QFont.Bold))

        for deg, lab in zip(angles, ticks):
            ang = math.radians(270 + deg)

            outer = r - 1  # yay çizgisine yapışık
            inner = outer - (16 if lab in (0, 30, 60) else 12)

            x1 = cx + math.cos(ang) * outer
            y1 = arc_cy + math.sin(ang) * outer
            x2 = cx + math.cos(ang) * inner
            y2 = arc_cy + math.sin(ang) * inner
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

            # etiketleri yay üzerinde göster (0 hariç küçük yaz)
            if lab != 0:
                tx = cx + math.cos(ang) * (r - 28)
                ty = arc_cy + math.sin(ang) * (r - 28)
                p.drawText(int(tx - 10), int(ty + 4), f"{lab}")

        # Üst kırmızı pointer
        p.setBrush(QBrush(QColor(255, 0, 0)))
        p.setPen(Qt.NoPen)
        tri = QPolygon([
            QPoint(int(cx), int(arc_cy - r - 2)),
            QPoint(int(cx - 9), int(arc_cy - r + 16)),
            QPoint(int(cx + 9), int(arc_cy - r + 16)),
        ])
        p.drawPolygon(tri)

        p.restore()