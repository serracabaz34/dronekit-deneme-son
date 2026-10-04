from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QFont, QColor, QRadialGradient,QPainterPath,QLinearGradient,QPolygonF
from PyQt5.QtCore import Qt,QRectF,QPointF
import math
class AirspeedGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
class AirspeedGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.max_value = 40
        self.setMinimumSize(200, 200)

    from PyQt5.QtWidgets import QWidget
    from PyQt5.QtGui import QPainter, QPen, QFont, QColor, QRadialGradient, QPainterPath, QLinearGradient, QPolygonF
    from PyQt5.QtCore import Qt, QRectF, QPointF
    import math
    class AirspeedGauge(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

    class AirspeedGauge(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.value = 0
            self.max_value = 40
            self.setMinimumSize(200, 200)

        def setValue(self, val):
            self.value = max(0, min(val, self.max_value))
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            radius = min(w, h) / 2 - 10
            cx, cy = w / 2, h / 2

            # -------------------------
            # METAL DIŞ ÇERÇEVE
            # -------------------------
            outerGradient = QRadialGradient(cx, cy, radius)
            outerGradient.setColorAt(0, QColor(120, 120, 120))
            outerGradient.setColorAt(1, QColor(40, 40, 40))

            painter.setBrush(outerGradient)
            painter.setPen(QPen(QColor(30, 30, 30), 4))
            painter.drawEllipse(cx - radius, cy - radius,
                                radius * 2, radius * 2)

            # -------------------------
            # İÇ PANEL (Koyu Gri)
            # -------------------------
            inner_radius = radius - 8
            panelGradient = QRadialGradient(cx, cy, inner_radius)
            panelGradient.setColorAt(0, QColor(70, 70, 70))
            panelGradient.setColorAt(1, QColor(25, 25, 25))

            painter.setBrush(panelGradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # -------------------------
            # RENK BANDI (ARC)
            # -------------------------
            arc_rect = QRectF(cx - inner_radius + 10,
                              cy - inner_radius + 10,
                              (inner_radius - 10) * 2,
                              (inner_radius - 10) * 2)

            def drawArc(start_val, end_val, color):
                start_angle = 225 - (270 * start_val / self.max_value)
                span_angle = - (270 * (end_val - start_val) / self.max_value)

                painter.setPen(QPen(color, 6))
                painter.drawArc(arc_rect,
                                int(start_angle * 16),
                                int(span_angle * 16))

            drawArc(0, 10, QColor(200, 0, 0))  # kırmızı
            drawArc(10, 25, QColor(0, 180, 0))  # yeşil
            drawArc(25, 35, QColor(255, 200, 0))  # sarı
            drawArc(35, 40, QColor(200, 0, 0))  # kırmızı

            # -------------------------
            # TICK ÇİZGİLERİ
            # -------------------------
            for i in range(self.max_value + 1):
                angle = 225 - (270 * i / self.max_value)
                rad = math.radians(angle)

                length = 15 if i % 5 == 0 else 8
                width = 2 if i % 5 == 0 else 1

                x1 = cx + (inner_radius - length) * math.cos(rad)
                y1 = cy - (inner_radius - length) * math.sin(rad)
                x2 = cx + inner_radius * math.cos(rad)
                y2 = cy - inner_radius * math.sin(rad)

                painter.setPen(QPen(Qt.white, width))
                painter.drawLine(x1, y1, x2, y2)

            # -------------------------
            # SAYILAR
            # -------------------------
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.setPen(Qt.white)

            for i in range(0, self.max_value + 1, 5):
                angle = 225 - (270 * i / self.max_value)
                rad = math.radians(angle)

                x_text = cx + (inner_radius - 30) * math.cos(rad) - 10
                y_text = cy - (inner_radius - 30) * math.sin(rad) + 5

                painter.drawText(x_text, y_text, str(i))

            # -------------------------
            # İBRE
            # -------------------------
            angle = 225 - (270 * self.value / self.max_value)
            rad = math.radians(angle)

            x_end = cx + (inner_radius - 25) * math.cos(rad)
            y_end = cy - (inner_radius - 25) * math.sin(rad)

            painter.setPen(QPen(Qt.white, 4))
            painter.drawLine(cx, cy, x_end, y_end)

            painter.setBrush(Qt.white)
            painter.drawEllipse(cx - 5, cy - 5, 10, 10)

            # -------------------------
            # CAM YANSIMA EFEKTİ
            # -------------------------
            glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
            glass.setColorAt(0, QColor(255, 255, 255, 60))
            glass.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(glass)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

    # =====================================================
    #                    ALTIMETER
    # =====================================================

    class AltimeterGauge(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.altitude = 0
            self.setMinimumSize(200, 200)

        def setAltitude(self, value):
            self.altitude = max(0, value)
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            radius = min(w, h) / 2 - 10
            cx, cy = w / 2, h / 2

            # ----- Metal Çerçeve
            outerGradient = QRadialGradient(cx, cy, radius)
            outerGradient.setColorAt(0, QColor(130, 130, 130))
            outerGradient.setColorAt(1, QColor(50, 50, 50))

            painter.setBrush(outerGradient)
            painter.setPen(QPen(QColor(30, 30, 30), 4))
            painter.drawEllipse(cx - radius, cy - radius,
                                radius * 2, radius * 2)

            # ----- İç Panel (Simsiyah değil)
            inner_radius = radius - 8
            panelGradient = QRadialGradient(cx, cy, inner_radius)
            panelGradient.setColorAt(0, QColor(70, 70, 70))
            panelGradient.setColorAt(1, QColor(35, 35, 35))

            painter.setBrush(panelGradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # ----- Skala 0-9
            painter.setPen(QPen(Qt.white, 2))
            painter.setFont(QFont("Arial", 10, QFont.Bold))

            for i in range(10):
                angle = 90 - (360 * i / 10)
                rad = math.radians(angle)

                x1 = cx + (inner_radius - 15) * math.cos(rad)
                y1 = cy - (inner_radius - 15) * math.sin(rad)
                x2 = cx + inner_radius * math.cos(rad)
                y2 = cy - inner_radius * math.sin(rad)
                painter.drawLine(x1, y1, x2, y2)

                x_text = cx + (inner_radius - 30) * math.cos(rad) - 8
                y_text = cy - (inner_radius - 30) * math.sin(rad) + 5
                painter.drawText(x_text, y_text, str(i))

            # ----- ALT Yazısı
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            painter.drawText(cx - 15, cy + 5, "ALT")

            # ----- Uzun İbre (100m)
            angle_long = 90 - (360 * (self.altitude % 1000) / 1000)
            rad_long = math.radians(angle_long)

            x_long = cx + (inner_radius - 20) * math.cos(rad_long)
            y_long = cy - (inner_radius - 20) * math.sin(rad_long)

            painter.setPen(QPen(Qt.white, 3))
            painter.drawLine(cx, cy, x_long, y_long)

            # ----- Kısa İbre (1000m)
            angle_short = 90 - (360 * (self.altitude % 10000) / 10000)
            rad_short = math.radians(angle_short)

            x_short = cx + (inner_radius - 50) * math.cos(rad_short)
            y_short = cy - (inner_radius - 50) * math.sin(rad_short)

            painter.setPen(QPen(Qt.white, 5))
            painter.drawLine(cx, cy, x_short, y_short)

            painter.setBrush(Qt.white)
            painter.drawEllipse(cx - 5, cy - 5, 10, 10)

            # ----- Cam Efekti
            glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
            glass.setColorAt(0, QColor(255, 255, 255, 50))
            glass.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(glass)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius,
                                cy - inner_radius,
                                inner_radius * 2,
                                inner_radius * 2)

    # =====================================================
    #          VERTICAL SPEED INDICATOR (VSI)
    # =====================================================
    class VerticalSpeedGauge(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.vspeed = 0
            self.min_value = -20
            self.max_value = 20

            self.setMinimumSize(210, 210)
            self.setMaximumSize(240, 240)

        def setVerticalSpeed(self, value):
            self.vspeed = max(self.min_value, min(value, self.max_value))
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            cx = w / 2
            cy = h / 2
            radius = min(w, h) / 2 - 10

            # ===== METAL ÇERÇEVE =====
            metal = QRadialGradient(cx, cy, radius)
            metal.setColorAt(0, QColor(150, 150, 150))
            metal.setColorAt(1, QColor(60, 60, 60))

            painter.setBrush(metal)
            painter.setPen(QPen(QColor(25, 25, 25), 4))
            painter.drawEllipse(cx - radius, cy - radius,
                                radius * 2, radius * 2)

            # ===== PANEL =====
            inner_radius = radius - 8

            panel = QRadialGradient(cx, cy, inner_radius)
            panel.setColorAt(0, QColor(85, 85, 85))
            panel.setColorAt(1, QColor(30, 30, 30))

            painter.setBrush(panel)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # ===== 240° YAY =====
            start_angle = 210
            span_angle = 240

            # ===== SKALA =====
            for value in range(self.min_value, self.max_value + 1, 5):

                ratio = (value - self.min_value) / (self.max_value - self.min_value)
                angle = start_angle - (span_angle * ratio)
                rad = math.radians(angle)

                # Tick
                if value == 0:
                    tick_length = 22
                    painter.setPen(QPen(Qt.white, 3))
                else:
                    tick_length = 18
                    painter.setPen(QPen(Qt.white, 2))

                x1 = cx + (inner_radius - tick_length) * math.cos(rad)
                y1 = cy - (inner_radius - tick_length) * math.sin(rad)
                x2 = cx + inner_radius * math.cos(rad)
                y2 = cy - inner_radius * math.sin(rad)

                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

                # ===== SAYILAR =====
                painter.setPen(Qt.white)

                if value == 0:
                    font = QFont("Segoe UI", 11, QFont.Bold)
                else:
                    font = QFont("Segoe UI", 10, QFont.Bold)

                painter.setFont(font)

                text_radius = inner_radius - 30  # tick'e yakın
                tx = cx + text_radius * math.cos(rad)
                ty = cy - text_radius * math.sin(rad)

                rect = QRectF(tx - 22, ty - 16, 44, 32)
                painter.drawText(rect, Qt.AlignCenter, str(value))

            # ===== ORTA YAZI =====
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
            painter.drawText(QRectF(cx - 40, cy - 18, 80, 30),
                             Qt.AlignCenter, "VSI")

            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(QRectF(cx - 40, cy + 5, 80, 25),
                             Qt.AlignCenter, "m/s")

            # ===== İBRE =====
            ratio = (self.vspeed - self.min_value) / (self.max_value - self.min_value)
            angle = start_angle - (span_angle * ratio)
            rad = math.radians(angle)

            needle_length = inner_radius - 35
            nx = cx + needle_length * math.cos(rad)
            ny = cy - needle_length * math.sin(rad)

            painter.setPen(QPen(Qt.white, 4))
            painter.drawLine(int(cx), int(cy), int(nx), int(ny))

            painter.setBrush(Qt.white)
            painter.drawEllipse(int(cx - 5), int(cy - 5), 10, 10)

            # ===== CAM EFEKTİ =====
            glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
            glass.setColorAt(0, QColor(255, 255, 255, 35))
            glass.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(glass)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius,
                                cy - inner_radius,
                                inner_radius * 2,
                                inner_radius * 2)

    class AttitudeIndicator(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.pitch = 0
            self.roll = 0

            # Bir tık daha küçültüldü
            self.setFixedSize(195, 195)

        def setAttitude(self, pitch, roll):
            self.pitch = max(-25, min(25, pitch))
            self.roll = max(-45, min(45, roll))
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            cx = w / 2
            cy = h / 2
            radius = min(w, h) / 2 - 5

            # ================= METAL FRAME =================
            frameGradient = QRadialGradient(cx, cy, radius)
            frameGradient.setColorAt(0.0, QColor(100, 100, 100))
            frameGradient.setColorAt(1.0, QColor(25, 25, 25))

            painter.setBrush(frameGradient)
            painter.setPen(QPen(QColor(20, 20, 20), 3))
            painter.drawEllipse(cx - radius, cy - radius,
                                radius * 2, radius * 2)

            inner_radius = radius - 9

            # İç siyah halka
            painter.setBrush(QColor(18, 18, 18))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # ================= HORIZON DRAW =================
            painter.save()

            clipPath = QPainterPath()
            clipPath.addEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)
            painter.setClipPath(clipPath)

            painter.translate(cx, cy)
            painter.rotate(-self.roll)

            pitch_scale = 3.2
            pitch_offset = self.pitch * pitch_scale

            # SKY
            skyGradient = QLinearGradient(0, -inner_radius, 0, 0)
            skyGradient.setColorAt(0, QColor(25, 110, 210))
            skyGradient.setColorAt(1, QColor(120, 180, 255))

            painter.setBrush(skyGradient)
            painter.drawRect(-inner_radius * 2,
                             -inner_radius * 2 + pitch_offset,
                             inner_radius * 4,
                             inner_radius * 2)

            # GROUND
            groundGradient = QLinearGradient(0, 0, 0, inner_radius)
            groundGradient.setColorAt(0, QColor(170, 110, 60))
            groundGradient.setColorAt(1, QColor(100, 60, 30))

            painter.setBrush(groundGradient)
            painter.drawRect(-inner_radius * 2,
                             pitch_offset,
                             inner_radius * 4,
                             inner_radius * 2)

            # Horizon line
            painter.setPen(QPen(Qt.white, 2))
            painter.drawLine(-inner_radius * 2, pitch_offset,
                             inner_radius * 2, pitch_offset)

            # ================= PITCH LINES =================
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.setPen(QPen(Qt.white, 2))

            for angle in [-20, -10, 10, 20]:
                y = pitch_offset - (angle * pitch_scale)

                painter.drawLine(-30, y, 30, y)

                text = str(abs(angle))

                painter.drawText(QRectF(-55, y - 8, 25, 16),
                                 Qt.AlignCenter, text)

                painter.drawText(QRectF(30, y - 8, 25, 16),
                                 Qt.AlignCenter, text)

            painter.restore()

            # ================= AIRCRAFT SYMBOL =================
            painter.setPen(QPen(QColor(255, 215, 0), 3))
            painter.drawLine(cx - 25, cy, cx + 25, cy)
            painter.drawLine(cx, cy, cx, cy + 8)

            # ================= GLASS EFFECT =================
            glass = QRadialGradient(cx - 25, cy - 25, inner_radius)
            glass.setColorAt(0, QColor(255, 255, 255, 35))
            glass.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(glass)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius,
                                cy - inner_radius,
                                inner_radius * 2,
                                inner_radius * 2)

    class CompassIndicator(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.heading = 0
            self.setFixedSize(195, 195)

        def setHeading(self, heading):
            self.heading = heading % 360
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            cx = w / 2
            cy = h / 2
            radius = min(w, h) / 2 - 5
            inner_radius = radius - 12

            # FRAME
            painter.setBrush(QColor(60, 60, 60))
            painter.setPen(QPen(QColor(20, 20, 20), 3))
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

            # INNER
            painter.setBrush(QColor(15, 15, 15))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # ================= ROTATING DISC =================
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(-self.heading)

            font = QFont("Arial", 9, QFont.Bold)
            painter.setFont(font)

            for deg in range(0, 360, 3):

                painter.save()
                painter.rotate(deg)

                if deg % 30 == 0:

                    # Üçgen marker
                    painter.setBrush(Qt.white)
                    painter.setPen(Qt.NoPen)

                    triangle = QPolygonF([
                        QPointF(0, -inner_radius + 4),
                        QPointF(-6, -inner_radius + 18),
                        QPointF(6, -inner_radius + 18)
                    ])
                    painter.drawPolygon(triangle)

                    # SAYI (DAHA DIŞA ALINDI)
                    value = deg // 10
                    painter.setPen(Qt.white)

                    painter.drawText(-12,
                                     -inner_radius + 22,  # <-- BURAYI 32'den 22'ye çektik
                                     24,
                                     20,
                                     Qt.AlignCenter,
                                     str(value))

                else:
                    painter.setPen(QPen(Qt.white, 1))
                    painter.drawLine(0,
                                     -inner_radius + 8,
                                     0,
                                     -inner_radius + 16)

                painter.restore()

            painter.restore()

            # ================= SABİT UÇAK =================
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.white)

            plane = QPainterPath()

            plane.moveTo(cx, cy - 38)
            plane.lineTo(cx - 12, cy - 10)
            plane.lineTo(cx - 40, cy - 2)
            plane.lineTo(cx - 38, cy + 4)
            plane.lineTo(cx - 10, cy + 2)
            plane.lineTo(cx - 6, cy + 22)
            plane.lineTo(cx - 12, cy + 26)
            plane.lineTo(cx - 12, cy + 32)
            plane.lineTo(cx + 12, cy + 32)
            plane.lineTo(cx + 12, cy + 26)
            plane.lineTo(cx + 6, cy + 22)
            plane.lineTo(cx + 10, cy + 2)
            plane.lineTo(cx + 38, cy + 4)
            plane.lineTo(cx + 40, cy - 2)
            plane.lineTo(cx + 12, cy - 10)
            plane.closeSubpath()

            painter.drawPath(plane)

            # ÜST REFERANS
            painter.setPen(QPen(Qt.white, 4))
            painter.drawLine(cx - 14,
                             cy - inner_radius + 2,
                             cx + 14,
                             cy - inner_radius + 2)

    class TurnCoordinatorIndicator(QWidget):
        def __init__(self):
            super().__init__()
            self.setMinimumSize(200, 200)
            self.bank_angle = 0
            self.slip = 0

        def setBankAngle(self, angle):
            self.bank_angle = max(-30, min(30, angle))
            self.update()

        def setSlip(self, value):
            self.slip = max(-1, min(1, value))
            self.update()

        def paintEvent(self, event):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            cx = w / 2
            cy = h / 2
            radius = min(w, h) / 2 - 6

            # ================= FRAME =================
            frame_grad = QRadialGradient(cx, cy, radius)
            frame_grad.setColorAt(0.75, QColor(70, 70, 70))
            frame_grad.setColorAt(1.0, QColor(30, 30, 30))

            p.setBrush(frame_grad)
            p.setPen(QPen(QColor(25, 25, 25), 3))
            p.drawEllipse(cx - radius, cy - radius,
                          radius * 2, radius * 2)

            # ================= INNER PANEL =================
            inner = radius - 10
            p.setBrush(QColor(18, 18, 18))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - inner, cy - inner,
                          inner * 2, inner * 2)

            # ================= ÜST REFERANS BLOKLARI =================
            p.setPen(QPen(Qt.white, 5))
            top_y = cy - inner + 40

            p.drawLine(cx - 50, top_y, cx - 30, top_y)
            p.drawLine(cx + 30, top_y, cx + 50, top_y)

            # ================= DÖNEN UÇAK =================
            p.save()
            p.translate(cx, cy - 5)
            p.rotate(self.bank_angle)

            p.setPen(Qt.NoPen)
            p.setBrush(Qt.white)

            plane = QPainterPath()
            plane.moveTo(0, -22)
            plane.lineTo(-8, -4)
            plane.lineTo(-42, 2)
            plane.lineTo(-40, 6)
            plane.lineTo(-6, 4)
            plane.lineTo(-4, 15)
            plane.lineTo(4, 15)
            plane.lineTo(6, 4)
            plane.lineTo(40, 6)
            plane.lineTo(42, 2)
            plane.lineTo(8, -4)
            plane.closeSubpath()

            p.drawPath(plane)
            p.restore()

            # ================= YAZILAR =================
            p.setPen(Qt.white)

            font_title = QFont("Arial", 8, QFont.Bold)
            p.setFont(font_title)
            p.drawText(cx - 60, cy + 18, 120, 18,
                       Qt.AlignCenter, "TURN COORDINATOR")

            font_small = QFont("Arial", 8, QFont.Bold)
            p.setFont(font_small)
            p.drawText(cx - 25, cy + 32, 50, 16,
                       Qt.AlignCenter, "2 MIN")

            # ================= SLIP TUBE =================
            tube_w = 90
            tube_h = 16

            tube_rect = QRectF(cx - tube_w / 2,
                               cy + 50,
                               tube_w,
                               tube_h)

            p.setBrush(QColor(230, 230, 230))
            p.setPen(QPen(Qt.white, 1))
            p.drawRoundedRect(tube_rect, 8, 8)

            # Orta referans çizgileri
            p.setPen(QPen(Qt.black, 2))
            p.drawLine(cx - 12, cy + 50,
                       cx - 12, cy + 66)

            p.drawLine(cx + 12, cy + 50,
                       cx + 12, cy + 66)

            # ================= TOP =================
            ball_offset = self.slip * (tube_w / 2 - 15)

            p.setBrush(QColor(40, 40, 40))
            p.setPen(Qt.NoPen)

            p.drawEllipse(cx - 7 + ball_offset,
                          cy + 53,
                          14,
                          14)

            # ================= L - R =================
            font_lr = QFont("Arial", 10, QFont.Bold)
            p.setFont(font_lr)
            p.setPen(Qt.white)

            p.drawText(cx - 50, cy + 82, "L")
            p.drawText(cx + 38, cy + 82, "R")
            self.value = 0
            self.max_value = 40
            self.setMinimumSize(200, 200)

        def setValue(self, val):
            self.value = max(0, min(val, self.max_value))
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            radius = min(w, h) / 2 - 10
            cx, cy = w / 2, h / 2

            # -------------------------
            # METAL DIŞ ÇERÇEVE
            # -------------------------
            outerGradient = QRadialGradient(cx, cy, radius)
            outerGradient.setColorAt(0, QColor(120, 120, 120))
            outerGradient.setColorAt(1, QColor(40, 40, 40))

            painter.setBrush(outerGradient)
            painter.setPen(QPen(QColor(30, 30, 30), 4))
            painter.drawEllipse(cx - radius, cy - radius,
                                radius * 2, radius * 2)

            # -------------------------
            # İÇ PANEL (Koyu Gri)
            # -------------------------
            inner_radius = radius - 8
            panelGradient = QRadialGradient(cx, cy, inner_radius)
            panelGradient.setColorAt(0, QColor(70, 70, 70))
            panelGradient.setColorAt(1, QColor(25, 25, 25))

            painter.setBrush(panelGradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # -------------------------
            # RENK BANDI (ARC)
            # -------------------------
            arc_rect = QRectF(cx - inner_radius + 10,
                              cy - inner_radius + 10,
                              (inner_radius - 10) * 2,
                              (inner_radius - 10) * 2)

            def drawArc(start_val, end_val, color):
                start_angle = 225 - (270 * start_val / self.max_value)
                span_angle = - (270 * (end_val - start_val) / self.max_value)

                painter.setPen(QPen(color, 6))
                painter.drawArc(arc_rect,
                                int(start_angle * 16),
                                int(span_angle * 16))

            drawArc(0, 10, QColor(200, 0, 0))  # kırmızı
            drawArc(10, 25, QColor(0, 180, 0))  # yeşil
            drawArc(25, 35, QColor(255, 200, 0))  # sarı
            drawArc(35, 40, QColor(200, 0, 0))  # kırmızı

            # -------------------------
            # TICK ÇİZGİLERİ
            # -------------------------
            for i in range(self.max_value + 1):
                angle = 225 - (270 * i / self.max_value)
                rad = math.radians(angle)

                length = 15 if i % 5 == 0 else 8
                width = 2 if i % 5 == 0 else 1

                x1 = cx + (inner_radius - length) * math.cos(rad)
                y1 = cy - (inner_radius - length) * math.sin(rad)
                x2 = cx + inner_radius * math.cos(rad)
                y2 = cy - inner_radius * math.sin(rad)

                painter.setPen(QPen(Qt.white, width))
                painter.drawLine(x1, y1, x2, y2)

            # -------------------------
            # SAYILAR
            # -------------------------
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.setPen(Qt.white)

            for i in range(0, self.max_value + 1, 5):
                angle = 225 - (270 * i / self.max_value)
                rad = math.radians(angle)

                x_text = cx + (inner_radius - 30) * math.cos(rad) - 10
                y_text = cy - (inner_radius - 30) * math.sin(rad) + 5

                painter.drawText(x_text, y_text, str(i))

            # -------------------------
            # İBRE
            # -------------------------
            angle = 225 - (270 * self.value / self.max_value)
            rad = math.radians(angle)

            x_end = cx + (inner_radius - 25) * math.cos(rad)
            y_end = cy - (inner_radius - 25) * math.sin(rad)

            painter.setPen(QPen(Qt.white, 4))
            painter.drawLine(cx, cy, x_end, y_end)

            painter.setBrush(Qt.white)
            painter.drawEllipse(cx - 5, cy - 5, 10, 10)

            # -------------------------
            # CAM YANSIMA EFEKTİ
            # -------------------------
            glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
            glass.setColorAt(0, QColor(255, 255, 255, 60))
            glass.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(glass)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

    # =====================================================
    #                    ALTIMETER
    # =====================================================

    class AltimeterGauge(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.altitude = 0
            self.setMinimumSize(200, 200)

        def setAltitude(self, value):
            self.altitude = max(0, value)
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            radius = min(w, h) / 2 - 10
            cx, cy = w / 2, h / 2

            # ----- Metal Çerçeve
            outerGradient = QRadialGradient(cx, cy, radius)
            outerGradient.setColorAt(0, QColor(130, 130, 130))
            outerGradient.setColorAt(1, QColor(50, 50, 50))

            painter.setBrush(outerGradient)
            painter.setPen(QPen(QColor(30, 30, 30), 4))
            painter.drawEllipse(cx - radius, cy - radius,
                                radius * 2, radius * 2)

            # ----- İç Panel (Simsiyah değil)
            inner_radius = radius - 8
            panelGradient = QRadialGradient(cx, cy, inner_radius)
            panelGradient.setColorAt(0, QColor(70, 70, 70))
            panelGradient.setColorAt(1, QColor(35, 35, 35))

            painter.setBrush(panelGradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # ----- Skala 0-9
            painter.setPen(QPen(Qt.white, 2))
            painter.setFont(QFont("Arial", 10, QFont.Bold))

            for i in range(10):
                angle = 90 - (360 * i / 10)
                rad = math.radians(angle)

                x1 = cx + (inner_radius - 15) * math.cos(rad)
                y1 = cy - (inner_radius - 15) * math.sin(rad)
                x2 = cx + inner_radius * math.cos(rad)
                y2 = cy - inner_radius * math.sin(rad)
                painter.drawLine(x1, y1, x2, y2)

                x_text = cx + (inner_radius - 30) * math.cos(rad) - 8
                y_text = cy - (inner_radius - 30) * math.sin(rad) + 5
                painter.drawText(x_text, y_text, str(i))

            # ----- ALT Yazısı
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            painter.drawText(cx - 15, cy + 5, "ALT")

            # ----- Uzun İbre (100m)
            angle_long = 90 - (360 * (self.altitude % 1000) / 1000)
            rad_long = math.radians(angle_long)

            x_long = cx + (inner_radius - 20) * math.cos(rad_long)
            y_long = cy - (inner_radius - 20) * math.sin(rad_long)

            painter.setPen(QPen(Qt.white, 3))
            painter.drawLine(cx, cy, x_long, y_long)

            # ----- Kısa İbre (1000m)
            angle_short = 90 - (360 * (self.altitude % 10000) / 10000)
            rad_short = math.radians(angle_short)

            x_short = cx + (inner_radius - 50) * math.cos(rad_short)
            y_short = cy - (inner_radius - 50) * math.sin(rad_short)

            painter.setPen(QPen(Qt.white, 5))
            painter.drawLine(cx, cy, x_short, y_short)

            painter.setBrush(Qt.white)
            painter.drawEllipse(cx - 5, cy - 5, 10, 10)

            # ----- Cam Efekti
            glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
            glass.setColorAt(0, QColor(255, 255, 255, 50))
            glass.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(glass)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius,
                                cy - inner_radius,
                                inner_radius * 2,
                                inner_radius * 2)

    # =====================================================
    #          VERTICAL SPEED INDICATOR (VSI)
    # =====================================================
    class VerticalSpeedGauge(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.vspeed = 0
            self.min_value = -20
            self.max_value = 20

            self.setMinimumSize(210, 210)
            self.setMaximumSize(240, 240)

        def setVerticalSpeed(self, value):
            self.vspeed = max(self.min_value, min(value, self.max_value))
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            cx = w / 2
            cy = h / 2
            radius = min(w, h) / 2 - 10

            # ===== METAL ÇERÇEVE =====
            metal = QRadialGradient(cx, cy, radius)
            metal.setColorAt(0, QColor(150, 150, 150))
            metal.setColorAt(1, QColor(60, 60, 60))

            painter.setBrush(metal)
            painter.setPen(QPen(QColor(25, 25, 25), 4))
            painter.drawEllipse(cx - radius, cy - radius,
                                radius * 2, radius * 2)

            # ===== PANEL =====
            inner_radius = radius - 8

            panel = QRadialGradient(cx, cy, inner_radius)
            panel.setColorAt(0, QColor(85, 85, 85))
            panel.setColorAt(1, QColor(30, 30, 30))

            painter.setBrush(panel)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # ===== 240° YAY =====
            start_angle = 210
            span_angle = 240

            # ===== SKALA =====
            for value in range(self.min_value, self.max_value + 1, 5):

                ratio = (value - self.min_value) / (self.max_value - self.min_value)
                angle = start_angle - (span_angle * ratio)
                rad = math.radians(angle)

                # Tick
                if value == 0:
                    tick_length = 22
                    painter.setPen(QPen(Qt.white, 3))
                else:
                    tick_length = 18
                    painter.setPen(QPen(Qt.white, 2))

                x1 = cx + (inner_radius - tick_length) * math.cos(rad)
                y1 = cy - (inner_radius - tick_length) * math.sin(rad)
                x2 = cx + inner_radius * math.cos(rad)
                y2 = cy - inner_radius * math.sin(rad)

                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

                # ===== SAYILAR =====
                painter.setPen(Qt.white)

                if value == 0:
                    font = QFont("Segoe UI", 11, QFont.Bold)
                else:
                    font = QFont("Segoe UI", 10, QFont.Bold)

                painter.setFont(font)

                text_radius = inner_radius - 30  # tick'e yakın
                tx = cx + text_radius * math.cos(rad)
                ty = cy - text_radius * math.sin(rad)

                rect = QRectF(tx - 22, ty - 16, 44, 32)
                painter.drawText(rect, Qt.AlignCenter, str(value))

            # ===== ORTA YAZI =====
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
            painter.drawText(QRectF(cx - 40, cy - 18, 80, 30),
                             Qt.AlignCenter, "VSI")

            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(QRectF(cx - 40, cy + 5, 80, 25),
                             Qt.AlignCenter, "m/s")

            # ===== İBRE =====
            ratio = (self.vspeed - self.min_value) / (self.max_value - self.min_value)
            angle = start_angle - (span_angle * ratio)
            rad = math.radians(angle)

            needle_length = inner_radius - 35
            nx = cx + needle_length * math.cos(rad)
            ny = cy - needle_length * math.sin(rad)

            painter.setPen(QPen(Qt.white, 4))
            painter.drawLine(int(cx), int(cy), int(nx), int(ny))

            painter.setBrush(Qt.white)
            painter.drawEllipse(int(cx - 5), int(cy - 5), 10, 10)

            # ===== CAM EFEKTİ =====
            glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
            glass.setColorAt(0, QColor(255, 255, 255, 35))
            glass.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(glass)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius,
                                cy - inner_radius,
                                inner_radius * 2,
                                inner_radius * 2)

    class AttitudeIndicator(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.pitch = 0
            self.roll = 0

            # Bir tık daha küçültüldü
            self.setFixedSize(195, 195)

        def setAttitude(self, pitch, roll):
            self.pitch = max(-25, min(25, pitch))
            self.roll = max(-45, min(45, roll))
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            cx = w / 2
            cy = h / 2
            radius = min(w, h) / 2 - 5

            # ================= METAL FRAME =================
            frameGradient = QRadialGradient(cx, cy, radius)
            frameGradient.setColorAt(0.0, QColor(100, 100, 100))
            frameGradient.setColorAt(1.0, QColor(25, 25, 25))

            painter.setBrush(frameGradient)
            painter.setPen(QPen(QColor(20, 20, 20), 3))
            painter.drawEllipse(cx - radius, cy - radius,
                                radius * 2, radius * 2)

            inner_radius = radius - 9

            # İç siyah halka
            painter.setBrush(QColor(18, 18, 18))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # ================= HORIZON DRAW =================
            painter.save()

            clipPath = QPainterPath()
            clipPath.addEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)
            painter.setClipPath(clipPath)

            painter.translate(cx, cy)
            painter.rotate(-self.roll)

            pitch_scale = 3.2
            pitch_offset = self.pitch * pitch_scale

            # SKY
            skyGradient = QLinearGradient(0, -inner_radius, 0, 0)
            skyGradient.setColorAt(0, QColor(25, 110, 210))
            skyGradient.setColorAt(1, QColor(120, 180, 255))

            painter.setBrush(skyGradient)
            painter.drawRect(-inner_radius * 2,
                             -inner_radius * 2 + pitch_offset,
                             inner_radius * 4,
                             inner_radius * 2)

            # GROUND
            groundGradient = QLinearGradient(0, 0, 0, inner_radius)
            groundGradient.setColorAt(0, QColor(170, 110, 60))
            groundGradient.setColorAt(1, QColor(100, 60, 30))

            painter.setBrush(groundGradient)
            painter.drawRect(-inner_radius * 2,
                             pitch_offset,
                             inner_radius * 4,
                             inner_radius * 2)

            # Horizon line
            painter.setPen(QPen(Qt.white, 2))
            painter.drawLine(-inner_radius * 2, pitch_offset,
                             inner_radius * 2, pitch_offset)

            # ================= PITCH LINES =================
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.setPen(QPen(Qt.white, 2))

            for angle in [-20, -10, 10, 20]:
                y = pitch_offset - (angle * pitch_scale)

                painter.drawLine(-30, y, 30, y)

                text = str(abs(angle))

                painter.drawText(QRectF(-55, y - 8, 25, 16),
                                 Qt.AlignCenter, text)

                painter.drawText(QRectF(30, y - 8, 25, 16),
                                 Qt.AlignCenter, text)

            painter.restore()

            # ================= AIRCRAFT SYMBOL =================
            painter.setPen(QPen(QColor(255, 215, 0), 3))
            painter.drawLine(cx - 25, cy, cx + 25, cy)
            painter.drawLine(cx, cy, cx, cy + 8)

            # ================= GLASS EFFECT =================
            glass = QRadialGradient(cx - 25, cy - 25, inner_radius)
            glass.setColorAt(0, QColor(255, 255, 255, 35))
            glass.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(glass)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius,
                                cy - inner_radius,
                                inner_radius * 2,
                                inner_radius * 2)

    class CompassIndicator(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.heading = 0
            self.setFixedSize(195, 195)

        def setHeading(self, heading):
            self.heading = heading % 360
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            cx = w / 2
            cy = h / 2
            radius = min(w, h) / 2 - 5
            inner_radius = radius - 12

            # FRAME
            painter.setBrush(QColor(60, 60, 60))
            painter.setPen(QPen(QColor(20, 20, 20), 3))
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

            # INNER
            painter.setBrush(QColor(15, 15, 15))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                                inner_radius * 2, inner_radius * 2)

            # ================= ROTATING DISC =================
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(-self.heading)

            font = QFont("Arial", 9, QFont.Bold)
            painter.setFont(font)

            for deg in range(0, 360, 3):

                painter.save()
                painter.rotate(deg)

                if deg % 30 == 0:

                    # Üçgen marker
                    painter.setBrush(Qt.white)
                    painter.setPen(Qt.NoPen)

                    triangle = QPolygonF([
                        QPointF(0, -inner_radius + 4),
                        QPointF(-6, -inner_radius + 18),
                        QPointF(6, -inner_radius + 18)
                    ])
                    painter.drawPolygon(triangle)

                    # SAYI (DAHA DIŞA ALINDI)
                    value = deg // 10
                    painter.setPen(Qt.white)

                    painter.drawText(-12,
                                     -inner_radius + 22,  # <-- BURAYI 32'den 22'ye çektik
                                     24,
                                     20,
                                     Qt.AlignCenter,
                                     str(value))

                else:
                    painter.setPen(QPen(Qt.white, 1))
                    painter.drawLine(0,
                                     -inner_radius + 8,
                                     0,
                                     -inner_radius + 16)

                painter.restore()

            painter.restore()

            # ================= SABİT UÇAK =================
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.white)

            plane = QPainterPath()

            plane.moveTo(cx, cy - 38)
            plane.lineTo(cx - 12, cy - 10)
            plane.lineTo(cx - 40, cy - 2)
            plane.lineTo(cx - 38, cy + 4)
            plane.lineTo(cx - 10, cy + 2)
            plane.lineTo(cx - 6, cy + 22)
            plane.lineTo(cx - 12, cy + 26)
            plane.lineTo(cx - 12, cy + 32)
            plane.lineTo(cx + 12, cy + 32)
            plane.lineTo(cx + 12, cy + 26)
            plane.lineTo(cx + 6, cy + 22)
            plane.lineTo(cx + 10, cy + 2)
            plane.lineTo(cx + 38, cy + 4)
            plane.lineTo(cx + 40, cy - 2)
            plane.lineTo(cx + 12, cy - 10)
            plane.closeSubpath()

            painter.drawPath(plane)

            # ÜST REFERANS
            painter.setPen(QPen(Qt.white, 4))
            painter.drawLine(cx - 14,
                             cy - inner_radius + 2,
                             cx + 14,
                             cy - inner_radius + 2)

    class TurnCoordinatorIndicator(QWidget):
        def __init__(self):
            super().__init__()
            self.setMinimumSize(200, 200)
            self.bank_angle = 0
            self.slip = 0

        def setBankAngle(self, angle):
            self.bank_angle = max(-30, min(30, angle))
            self.update()

        def setSlip(self, value):
            self.slip = max(-1, min(1, value))
            self.update()

        def paintEvent(self, event):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()
            cx = w / 2
            cy = h / 2
            radius = min(w, h) / 2 - 6

            # ================= FRAME =================
            frame_grad = QRadialGradient(cx, cy, radius)
            frame_grad.setColorAt(0.75, QColor(70, 70, 70))
            frame_grad.setColorAt(1.0, QColor(30, 30, 30))

            p.setBrush(frame_grad)
            p.setPen(QPen(QColor(25, 25, 25), 3))
            p.drawEllipse(cx - radius, cy - radius,
                          radius * 2, radius * 2)

            # ================= INNER PANEL =================
            inner = radius - 10
            p.setBrush(QColor(18, 18, 18))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - inner, cy - inner,
                          inner * 2, inner * 2)

            # ================= ÜST REFERANS BLOKLARI =================
            p.setPen(QPen(Qt.white, 5))
            top_y = cy - inner + 40

            p.drawLine(cx - 50, top_y, cx - 30, top_y)
            p.drawLine(cx + 30, top_y, cx + 50, top_y)

            # ================= DÖNEN UÇAK =================
            p.save()
            p.translate(cx, cy - 5)
            p.rotate(self.bank_angle)

            p.setPen(Qt.NoPen)
            p.setBrush(Qt.white)

            plane = QPainterPath()
            plane.moveTo(0, -22)
            plane.lineTo(-8, -4)
            plane.lineTo(-42, 2)
            plane.lineTo(-40, 6)
            plane.lineTo(-6, 4)
            plane.lineTo(-4, 15)
            plane.lineTo(4, 15)
            plane.lineTo(6, 4)
            plane.lineTo(40, 6)
            plane.lineTo(42, 2)
            plane.lineTo(8, -4)
            plane.closeSubpath()

            p.drawPath(plane)
            p.restore()

            # ================= YAZILAR =================
            p.setPen(Qt.white)

            font_title = QFont("Arial", 8, QFont.Bold)
            p.setFont(font_title)
            p.drawText(cx - 60, cy + 18, 120, 18,
                       Qt.AlignCenter, "TURN COORDINATOR")

            font_small = QFont("Arial", 8, QFont.Bold)
            p.setFont(font_small)
            p.drawText(cx - 25, cy + 32, 50, 16,
                       Qt.AlignCenter, "2 MIN")

            # ================= SLIP TUBE =================
            tube_w = 90
            tube_h = 16

            tube_rect = QRectF(cx - tube_w / 2,
                               cy + 50,
                               tube_w,
                               tube_h)

            p.setBrush(QColor(230, 230, 230))
            p.setPen(QPen(Qt.white, 1))
            p.drawRoundedRect(tube_rect, 8, 8)

            # Orta referans çizgileri
            p.setPen(QPen(Qt.black, 2))
            p.drawLine(cx - 12, cy + 50,
                       cx - 12, cy + 66)

            p.drawLine(cx + 12, cy + 50,
                       cx + 12, cy + 66)

            # ================= TOP =================
            ball_offset = self.slip * (tube_w / 2 - 15)

            p.setBrush(QColor(40, 40, 40))
            p.setPen(Qt.NoPen)

            p.drawEllipse(cx - 7 + ball_offset,
                          cy + 53,
                          14,
                          14)

            # ================= L - R =================
            font_lr = QFont("Arial", 10, QFont.Bold)
            p.setFont(font_lr)
            p.setPen(Qt.white)

            p.drawText(cx - 50, cy + 82, "L")
            p.drawText(cx + 38, cy + 82, "R")
    def setValue(self, val):
        self.value = max(0, min(val, self.max_value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        radius = min(w, h) / 2 - 10
        cx, cy = w / 2, h / 2

        # -------------------------
        # METAL DIŞ ÇERÇEVE
        # -------------------------
        outerGradient = QRadialGradient(cx, cy, radius)
        outerGradient.setColorAt(0, QColor(120, 120, 120))
        outerGradient.setColorAt(1, QColor(40, 40, 40))

        painter.setBrush(outerGradient)
        painter.setPen(QPen(QColor(30, 30, 30), 4))
        painter.drawEllipse(cx - radius, cy - radius,
                            radius * 2, radius * 2)

        # -------------------------
        # İÇ PANEL (Koyu Gri)
        # -------------------------
        inner_radius = radius - 8
        panelGradient = QRadialGradient(cx, cy, inner_radius)
        panelGradient.setColorAt(0, QColor(70, 70, 70))
        panelGradient.setColorAt(1, QColor(25, 25, 25))

        painter.setBrush(panelGradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)

        # -------------------------
        # RENK BANDI (ARC)
        # -------------------------
        arc_rect = QRectF(cx - inner_radius + 10,
                          cy - inner_radius + 10,
                          (inner_radius - 10) * 2,
                          (inner_radius - 10) * 2)

        def drawArc(start_val, end_val, color):
            start_angle = 225 - (270 * start_val / self.max_value)
            span_angle = - (270 * (end_val - start_val) / self.max_value)

            painter.setPen(QPen(color, 6))
            painter.drawArc(arc_rect,
                            int(start_angle * 16),
                            int(span_angle * 16))

        drawArc(0, 10, QColor(200, 0, 0))  # kırmızı
        drawArc(10, 25, QColor(0, 180, 0))  # yeşil
        drawArc(25, 35, QColor(255, 200, 0))  # sarı
        drawArc(35, 40, QColor(200, 0, 0))  # kırmızı

        # -------------------------
        # TICK ÇİZGİLERİ
        # -------------------------
        for i in range(self.max_value + 1):
            angle = 225 - (270 * i / self.max_value)
            rad = math.radians(angle)

            length = 15 if i % 5 == 0 else 8
            width = 2 if i % 5 == 0 else 1

            x1 = cx + (inner_radius - length) * math.cos(rad)
            y1 = cy - (inner_radius - length) * math.sin(rad)
            x2 = cx + inner_radius * math.cos(rad)
            y2 = cy - inner_radius * math.sin(rad)

            painter.setPen(QPen(Qt.white, width))
            painter.drawLine(x1, y1, x2, y2)

        # -------------------------
        # SAYILAR
        # -------------------------
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.setPen(Qt.white)

        for i in range(0, self.max_value + 1, 5):
            angle = 225 - (270 * i / self.max_value)
            rad = math.radians(angle)

            x_text = cx + (inner_radius - 30) * math.cos(rad) - 10
            y_text = cy - (inner_radius - 30) * math.sin(rad) + 5

            painter.drawText(x_text, y_text, str(i))

        # -------------------------
        # İBRE
        # -------------------------
        angle = 225 - (270 * self.value / self.max_value)
        rad = math.radians(angle)

        x_end = cx + (inner_radius - 25) * math.cos(rad)
        y_end = cy - (inner_radius - 25) * math.sin(rad)

        painter.setPen(QPen(Qt.white, 4))
        painter.drawLine(cx, cy, x_end, y_end)

        painter.setBrush(Qt.white)
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)

        # -------------------------
        # CAM YANSIMA EFEKTİ
        # -------------------------
        glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
        glass.setColorAt(0, QColor(255, 255, 255, 60))
        glass.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setBrush(glass)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)


# =====================================================
#                    ALTIMETER
# =====================================================

class AltimeterGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.altitude = 0
        self.setMinimumSize(200, 200)

    def setAltitude(self, value):
        self.altitude = max(0, value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        radius = min(w, h) / 2 - 10
        cx, cy = w / 2, h / 2

        # ----- Metal Çerçeve
        outerGradient = QRadialGradient(cx, cy, radius)
        outerGradient.setColorAt(0, QColor(130, 130, 130))
        outerGradient.setColorAt(1, QColor(50, 50, 50))

        painter.setBrush(outerGradient)
        painter.setPen(QPen(QColor(30, 30, 30), 4))
        painter.drawEllipse(cx - radius, cy - radius,
                            radius * 2, radius * 2)

        # ----- İç Panel (Simsiyah değil)
        inner_radius = radius - 8
        panelGradient = QRadialGradient(cx, cy, inner_radius)
        panelGradient.setColorAt(0, QColor(70, 70, 70))
        panelGradient.setColorAt(1, QColor(35, 35, 35))

        painter.setBrush(panelGradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)

        # ----- Skala 0-9
        painter.setPen(QPen(Qt.white, 2))
        painter.setFont(QFont("Arial", 10, QFont.Bold))

        for i in range(10):
            angle = 90 - (360 * i / 10)
            rad = math.radians(angle)

            x1 = cx + (inner_radius - 15) * math.cos(rad)
            y1 = cy - (inner_radius - 15) * math.sin(rad)
            x2 = cx + inner_radius * math.cos(rad)
            y2 = cy - inner_radius * math.sin(rad)
            painter.drawLine(x1, y1, x2, y2)

            x_text = cx + (inner_radius - 30) * math.cos(rad) - 8
            y_text = cy - (inner_radius - 30) * math.sin(rad) + 5
            painter.drawText(x_text, y_text, str(i))

        # ----- ALT Yazısı
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(cx - 15, cy + 5, "ALT")

        # ----- Uzun İbre (100m)
        angle_long = 90 - (360 * (self.altitude % 1000) / 1000)
        rad_long = math.radians(angle_long)

        x_long = cx + (inner_radius - 20) * math.cos(rad_long)
        y_long = cy - (inner_radius - 20) * math.sin(rad_long)

        painter.setPen(QPen(Qt.white, 3))
        painter.drawLine(cx, cy, x_long, y_long)

        # ----- Kısa İbre (1000m)
        angle_short = 90 - (360 * (self.altitude % 10000) / 10000)
        rad_short = math.radians(angle_short)

        x_short = cx + (inner_radius - 50) * math.cos(rad_short)
        y_short = cy - (inner_radius - 50) * math.sin(rad_short)

        painter.setPen(QPen(Qt.white, 5))
        painter.drawLine(cx, cy, x_short, y_short)

        painter.setBrush(Qt.white)
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)

        # ----- Cam Efekti
        glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
        glass.setColorAt(0, QColor(255, 255, 255, 50))
        glass.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setBrush(glass)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius,
                            cy - inner_radius,
                            inner_radius * 2,
                            inner_radius * 2)

 # =====================================================
        #          VERTICAL SPEED INDICATOR (VSI)
        # =====================================================
class VerticalSpeedGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.vspeed = 0
        self.min_value = -20
        self.max_value = 20

        self.setMinimumSize(210, 210)
        self.setMaximumSize(240, 240)

    def setVerticalSpeed(self, value):
        self.vspeed = max(self.min_value, min(value, self.max_value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 10

        # ===== METAL ÇERÇEVE =====
        metal = QRadialGradient(cx, cy, radius)
        metal.setColorAt(0, QColor(150,150,150))
        metal.setColorAt(1, QColor(60,60,60))

        painter.setBrush(metal)
        painter.setPen(QPen(QColor(25,25,25), 4))
        painter.drawEllipse(cx - radius, cy - radius,
                            radius*2, radius*2)

        # ===== PANEL =====
        inner_radius = radius - 8

        panel = QRadialGradient(cx, cy, inner_radius)
        panel.setColorAt(0, QColor(85,85,85))
        panel.setColorAt(1, QColor(30,30,30))

        painter.setBrush(panel)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius*2, inner_radius*2)

        # ===== 240° YAY =====
        start_angle = 210
        span_angle = 240

        # ===== SKALA =====
        for value in range(self.min_value, self.max_value + 1, 5):

            ratio = (value - self.min_value) / (self.max_value - self.min_value)
            angle = start_angle - (span_angle * ratio)
            rad = math.radians(angle)

            # Tick
            if value == 0:
                tick_length = 22
                painter.setPen(QPen(Qt.white, 3))
            else:
                tick_length = 18
                painter.setPen(QPen(Qt.white, 2))

            x1 = cx + (inner_radius - tick_length) * math.cos(rad)
            y1 = cy - (inner_radius - tick_length) * math.sin(rad)
            x2 = cx + inner_radius * math.cos(rad)
            y2 = cy - inner_radius * math.sin(rad)

            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            # ===== SAYILAR =====
            painter.setPen(Qt.white)

            if value == 0:
                font = QFont("Segoe UI", 11, QFont.Bold)
            else:
                font = QFont("Segoe UI", 10, QFont.Bold)

            painter.setFont(font)

            text_radius = inner_radius - 30  # tick'e yakın
            tx = cx + text_radius * math.cos(rad)
            ty = cy - text_radius * math.sin(rad)

            rect = QRectF(tx - 22, ty - 16, 44, 32)
            painter.drawText(rect, Qt.AlignCenter, str(value))

        # ===== ORTA YAZI =====
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(QRectF(cx - 40, cy - 18, 80, 30),
                         Qt.AlignCenter, "VSI")

        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRectF(cx - 40, cy + 5, 80, 25),
                         Qt.AlignCenter, "m/s")

        # ===== İBRE =====
        ratio = (self.vspeed - self.min_value) / (self.max_value - self.min_value)
        angle = start_angle - (span_angle * ratio)
        rad = math.radians(angle)

        needle_length = inner_radius - 35
        nx = cx + needle_length * math.cos(rad)
        ny = cy - needle_length * math.sin(rad)

        painter.setPen(QPen(Qt.white, 4))
        painter.drawLine(int(cx), int(cy), int(nx), int(ny))

        painter.setBrush(Qt.white)
        painter.drawEllipse(int(cx - 5), int(cy - 5), 10, 10)

        # ===== CAM EFEKTİ =====
        glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
        glass.setColorAt(0, QColor(255,255,255,35))
        glass.setColorAt(1, QColor(255,255,255,0))

        painter.setBrush(glass)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius,
                            cy - inner_radius,
                            inner_radius*2,
                            inner_radius*2)

class AttitudeIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.pitch = 0
        self.roll = 0

        # Bir tık daha küçültüldü
        self.setFixedSize(195, 195)

    def setAttitude(self, pitch, roll):
        self.pitch = max(-25, min(25, pitch))
        self.roll = max(-45, min(45, roll))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 5

        # ================= METAL FRAME =================
        frameGradient = QRadialGradient(cx, cy, radius)
        frameGradient.setColorAt(0.0, QColor(100, 100, 100))
        frameGradient.setColorAt(1.0, QColor(25, 25, 25))

        painter.setBrush(frameGradient)
        painter.setPen(QPen(QColor(20, 20, 20), 3))
        painter.drawEllipse(cx - radius, cy - radius,
                            radius * 2, radius * 2)

        inner_radius = radius - 9

        # İç siyah halka
        painter.setBrush(QColor(18, 18, 18))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)

        # ================= HORIZON DRAW =================
        painter.save()

        clipPath = QPainterPath()
        clipPath.addEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)
        painter.setClipPath(clipPath)

        painter.translate(cx, cy)
        painter.rotate(-self.roll)

        pitch_scale = 3.2
        pitch_offset = self.pitch * pitch_scale

        # SKY
        skyGradient = QLinearGradient(0, -inner_radius, 0, 0)
        skyGradient.setColorAt(0, QColor(25, 110, 210))
        skyGradient.setColorAt(1, QColor(120, 180, 255))

        painter.setBrush(skyGradient)
        painter.drawRect(-inner_radius * 2,
                         -inner_radius * 2 + pitch_offset,
                         inner_radius * 4,
                         inner_radius * 2)

        # GROUND
        groundGradient = QLinearGradient(0, 0, 0, inner_radius)
        groundGradient.setColorAt(0, QColor(170, 110, 60))
        groundGradient.setColorAt(1, QColor(100, 60, 30))

        painter.setBrush(groundGradient)
        painter.drawRect(-inner_radius * 2,
                         pitch_offset,
                         inner_radius * 4,
                         inner_radius * 2)

        # Horizon line
        painter.setPen(QPen(Qt.white, 2))
        painter.drawLine(-inner_radius * 2, pitch_offset,
                         inner_radius * 2, pitch_offset)

        # ================= PITCH LINES =================
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.setPen(QPen(Qt.white, 2))

        for angle in [-20, -10, 10, 20]:
            y = pitch_offset - (angle * pitch_scale)

            painter.drawLine(-30, y, 30, y)

            text = str(abs(angle))

            painter.drawText(QRectF(-55, y - 8, 25, 16),
                             Qt.AlignCenter, text)

            painter.drawText(QRectF(30, y - 8, 25, 16),
                             Qt.AlignCenter, text)

        painter.restore()

        # ================= AIRCRAFT SYMBOL =================
        painter.setPen(QPen(QColor(255, 215, 0), 3))
        painter.drawLine(cx - 25, cy, cx + 25, cy)
        painter.drawLine(cx, cy, cx, cy + 8)

        # ================= GLASS EFFECT =================
        glass = QRadialGradient(cx - 25, cy - 25, inner_radius)
        glass.setColorAt(0, QColor(255, 255, 255, 35))
        glass.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setBrush(glass)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius,
                            cy - inner_radius,
                            inner_radius * 2,
                            inner_radius * 2)

class CompassIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.heading = 0
        self.setFixedSize(195, 195)

    def setHeading(self, heading):
        self.heading = heading % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 5
        inner_radius = radius - 12

        # FRAME
        painter.setBrush(QColor(60, 60, 60))
        painter.setPen(QPen(QColor(20, 20, 20), 3))
        painter.drawEllipse(cx-radius, cy-radius, radius*2, radius*2)

        # INNER
        painter.setBrush(QColor(15, 15, 15))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx-inner_radius, cy-inner_radius,
                            inner_radius*2, inner_radius*2)

        # ================= ROTATING DISC =================
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self.heading)

        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)

        for deg in range(0, 360, 3):

            painter.save()
            painter.rotate(deg)

            if deg % 30 == 0:

                # Üçgen marker
                painter.setBrush(Qt.white)
                painter.setPen(Qt.NoPen)

                triangle = QPolygonF([
                    QPointF(0, -inner_radius + 4),
                    QPointF(-6, -inner_radius + 18),
                    QPointF(6, -inner_radius + 18)
                ])
                painter.drawPolygon(triangle)

                # SAYI (DAHA DIŞA ALINDI)
                value = deg // 10
                painter.setPen(Qt.white)

                painter.drawText(-12,
                                 -inner_radius + 22,  # <-- BURAYI 32'den 22'ye çektik
                                 24,
                                 20,
                                 Qt.AlignCenter,
                                 str(value))

            else:
                painter.setPen(QPen(Qt.white, 1))
                painter.drawLine(0,
                                 -inner_radius + 8,
                                 0,
                                 -inner_radius + 16)

            painter.restore()

        painter.restore()

        # ================= SABİT UÇAK =================
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)

        plane = QPainterPath()

        plane.moveTo(cx, cy - 38)
        plane.lineTo(cx - 12, cy - 10)
        plane.lineTo(cx - 40, cy - 2)
        plane.lineTo(cx - 38, cy + 4)
        plane.lineTo(cx - 10, cy + 2)
        plane.lineTo(cx - 6, cy + 22)
        plane.lineTo(cx - 12, cy + 26)
        plane.lineTo(cx - 12, cy + 32)
        plane.lineTo(cx + 12, cy + 32)
        plane.lineTo(cx + 12, cy + 26)
        plane.lineTo(cx + 6, cy + 22)
        plane.lineTo(cx + 10, cy + 2)
        plane.lineTo(cx + 38, cy + 4)
        plane.lineTo(cx + 40, cy - 2)
        plane.lineTo(cx + 12, cy - 10)
        plane.closeSubpath()

        painter.drawPath(plane)

        # ÜST REFERANS
        painter.setPen(QPen(Qt.white, 4))
        painter.drawLine(cx - 14,
                         cy - inner_radius + 2,
                         cx + 14,
                         cy - inner_radius + 2)


class TurnCoordinatorIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 200)
        self.bank_angle = 0
        self.slip = 0

    def setBankAngle(self, angle):
        self.bank_angle = max(-30, min(30, angle))
        self.update()

    def setSlip(self, value):
        self.slip = max(-1, min(1, value))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 6

        # ================= FRAME =================
        frame_grad = QRadialGradient(cx, cy, radius)
        frame_grad.setColorAt(0.75, QColor(70, 70, 70))
        frame_grad.setColorAt(1.0, QColor(30, 30, 30))

        p.setBrush(frame_grad)
        p.setPen(QPen(QColor(25, 25, 25), 3))
        p.drawEllipse(cx - radius, cy - radius,
                      radius * 2, radius * 2)

        # ================= INNER PANEL =================
        inner = radius - 10
        p.setBrush(QColor(18, 18, 18))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - inner, cy - inner,
                      inner * 2, inner * 2)

        # ================= ÜST REFERANS BLOKLARI =================
        p.setPen(QPen(Qt.white, 5))
        top_y = cy - inner + 40

        p.drawLine(cx - 50, top_y, cx - 30, top_y)
        p.drawLine(cx + 30, top_y, cx + 50, top_y)

        # ================= DÖNEN UÇAK =================
        p.save()
        p.translate(cx, cy - 5)
        p.rotate(self.bank_angle)

        p.setPen(Qt.NoPen)
        p.setBrush(Qt.white)

        plane = QPainterPath()
        plane.moveTo(0, -22)
        plane.lineTo(-8, -4)
        plane.lineTo(-42, 2)
        plane.lineTo(-40, 6)
        plane.lineTo(-6, 4)
        plane.lineTo(-4, 15)
        plane.lineTo(4, 15)
        plane.lineTo(6, 4)
        plane.lineTo(40, 6)
        plane.lineTo(42, 2)
        plane.lineTo(8, -4)
        plane.closeSubpath()

        p.drawPath(plane)
        p.restore()

        # ================= YAZILAR =================
        p.setPen(Qt.white)

        font_title = QFont("Arial", 8, QFont.Bold)
        p.setFont(font_title)
        p.drawText(cx - 60, cy + 18, 120, 18,
                   Qt.AlignCenter, "TURN COORDINATOR")

        font_small = QFont("Arial", 8, QFont.Bold)
        p.setFont(font_small)
        p.drawText(cx - 25, cy + 32, 50, 16,
                   Qt.AlignCenter, "2 MIN")

        # ================= SLIP TUBE =================
        tube_w = 90
        tube_h = 16

        tube_rect = QRectF(cx - tube_w / 2,
                           cy + 50,
                           tube_w,
                           tube_h)

        p.setBrush(QColor(230, 230, 230))
        p.setPen(QPen(Qt.white, 1))
        p.drawRoundedRect(tube_rect, 8, 8)

        # Orta referans çizgileri
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(cx - 12, cy + 50,
                   cx - 12, cy + 66)

        p.drawLine(cx + 12, cy + 50,
                   cx + 12, cy + 66)

        # ================= TOP =================
        ball_offset = self.slip * (tube_w / 2 - 15)

        p.setBrush(QColor(40, 40, 40))
        p.setPen(Qt.NoPen)

        p.drawEllipse(cx - 7 + ball_offset,
                      cy + 53,
                      14,
                      14)

        # ================= L - R =================
        font_lr = QFont("Arial", 10, QFont.Bold)
        p.setFont(font_lr)
        p.setPen(Qt.white)

        p.drawText(cx - 50, cy + 82, "L")
        p.drawText(cx + 38, cy + 82, "R")
        self.value = 0
        self.max_value = 40
        self.setMinimumSize(200, 200)

    def setValue(self, val):
        self.value = max(0, min(val, self.max_value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        radius = min(w, h) / 2 - 10
        cx, cy = w / 2, h / 2

        # -------------------------
        # METAL DIŞ ÇERÇEVE
        # -------------------------
        outerGradient = QRadialGradient(cx, cy, radius)
        outerGradient.setColorAt(0, QColor(120, 120, 120))
        outerGradient.setColorAt(1, QColor(40, 40, 40))

        painter.setBrush(outerGradient)
        painter.setPen(QPen(QColor(30, 30, 30), 4))
        painter.drawEllipse(cx - radius, cy - radius,
                            radius * 2, radius * 2)

        # -------------------------
        # İÇ PANEL (Koyu Gri)
        # -------------------------
        inner_radius = radius - 8
        panelGradient = QRadialGradient(cx, cy, inner_radius)
        panelGradient.setColorAt(0, QColor(70, 70, 70))
        panelGradient.setColorAt(1, QColor(25, 25, 25))

        painter.setBrush(panelGradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)

        # -------------------------
        # RENK BANDI (ARC)
        # -------------------------
        arc_rect = QRectF(cx - inner_radius + 10,
                          cy - inner_radius + 10,
                          (inner_radius - 10) * 2,
                          (inner_radius - 10) * 2)

        def drawArc(start_val, end_val, color):
            start_angle = 225 - (270 * start_val / self.max_value)
            span_angle = - (270 * (end_val - start_val) / self.max_value)

            painter.setPen(QPen(color, 6))
            painter.drawArc(arc_rect,
                            int(start_angle * 16),
                            int(span_angle * 16))

        drawArc(0, 10, QColor(200, 0, 0))  # kırmızı
        drawArc(10, 25, QColor(0, 180, 0))  # yeşil
        drawArc(25, 35, QColor(255, 200, 0))  # sarı
        drawArc(35, 40, QColor(200, 0, 0))  # kırmızı

        # -------------------------
        # TICK ÇİZGİLERİ
        # -------------------------
        for i in range(self.max_value + 1):
            angle = 225 - (270 * i / self.max_value)
            rad = math.radians(angle)

            length = 15 if i % 5 == 0 else 8
            width = 2 if i % 5 == 0 else 1

            x1 = cx + (inner_radius - length) * math.cos(rad)
            y1 = cy - (inner_radius - length) * math.sin(rad)
            x2 = cx + inner_radius * math.cos(rad)
            y2 = cy - inner_radius * math.sin(rad)

            painter.setPen(QPen(Qt.white, width))
            painter.drawLine(x1, y1, x2, y2)

        # -------------------------
        # SAYILAR
        # -------------------------
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.setPen(Qt.white)

        for i in range(0, self.max_value + 1, 5):
            angle = 225 - (270 * i / self.max_value)
            rad = math.radians(angle)

            x_text = cx + (inner_radius - 30) * math.cos(rad) - 10
            y_text = cy - (inner_radius - 30) * math.sin(rad) + 5

            painter.drawText(x_text, y_text, str(i))

        # -------------------------
        # İBRE
        # -------------------------
        angle = 225 - (270 * self.value / self.max_value)
        rad = math.radians(angle)

        x_end = cx + (inner_radius - 25) * math.cos(rad)
        y_end = cy - (inner_radius - 25) * math.sin(rad)

        painter.setPen(QPen(Qt.white, 4))
        painter.drawLine(cx, cy, x_end, y_end)

        painter.setBrush(Qt.white)
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)

        # -------------------------
        # CAM YANSIMA EFEKTİ
        # -------------------------
        glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
        glass.setColorAt(0, QColor(255, 255, 255, 60))
        glass.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setBrush(glass)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)


# =====================================================
#                    ALTIMETER
# =====================================================

class AltimeterGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.altitude = 0
        self.setMinimumSize(200, 200)

    def setAltitude(self, value):
        self.altitude = max(0, value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        radius = min(w, h) / 2 - 10
        cx, cy = w / 2, h / 2

        # ----- Metal Çerçeve
        outerGradient = QRadialGradient(cx, cy, radius)
        outerGradient.setColorAt(0, QColor(130, 130, 130))
        outerGradient.setColorAt(1, QColor(50, 50, 50))

        painter.setBrush(outerGradient)
        painter.setPen(QPen(QColor(30, 30, 30), 4))
        painter.drawEllipse(cx - radius, cy - radius,
                            radius * 2, radius * 2)

        # ----- İç Panel (Simsiyah değil)
        inner_radius = radius - 8
        panelGradient = QRadialGradient(cx, cy, inner_radius)
        panelGradient.setColorAt(0, QColor(70, 70, 70))
        panelGradient.setColorAt(1, QColor(35, 35, 35))

        painter.setBrush(panelGradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)

        # ----- Skala 0-9
        painter.setPen(QPen(Qt.white, 2))
        painter.setFont(QFont("Arial", 10, QFont.Bold))

        for i in range(10):
            angle = 90 - (360 * i / 10)
            rad = math.radians(angle)

            x1 = cx + (inner_radius - 15) * math.cos(rad)
            y1 = cy - (inner_radius - 15) * math.sin(rad)
            x2 = cx + inner_radius * math.cos(rad)
            y2 = cy - inner_radius * math.sin(rad)
            painter.drawLine(x1, y1, x2, y2)

            x_text = cx + (inner_radius - 30) * math.cos(rad) - 8
            y_text = cy - (inner_radius - 30) * math.sin(rad) + 5
            painter.drawText(x_text, y_text, str(i))

        # ----- ALT Yazısı
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(cx - 15, cy + 5, "ALT")

        # ----- Uzun İbre (100m)
        angle_long = 90 - (360 * (self.altitude % 1000) / 1000)
        rad_long = math.radians(angle_long)

        x_long = cx + (inner_radius - 20) * math.cos(rad_long)
        y_long = cy - (inner_radius - 20) * math.sin(rad_long)

        painter.setPen(QPen(Qt.white, 3))
        painter.drawLine(cx, cy, x_long, y_long)

        # ----- Kısa İbre (1000m)
        angle_short = 90 - (360 * (self.altitude % 10000) / 10000)
        rad_short = math.radians(angle_short)

        x_short = cx + (inner_radius - 50) * math.cos(rad_short)
        y_short = cy - (inner_radius - 50) * math.sin(rad_short)

        painter.setPen(QPen(Qt.white, 5))
        painter.drawLine(cx, cy, x_short, y_short)

        painter.setBrush(Qt.white)
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)

        # ----- Cam Efekti
        glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
        glass.setColorAt(0, QColor(255, 255, 255, 50))
        glass.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setBrush(glass)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius,
                            cy - inner_radius,
                            inner_radius * 2,
                            inner_radius * 2)

 # =====================================================
        #          VERTICAL SPEED INDICATOR (VSI)
        # =====================================================
class VerticalSpeedGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.vspeed = 0
        self.min_value = -20
        self.max_value = 20

        self.setMinimumSize(210, 210)
        self.setMaximumSize(240, 240)

    def setVerticalSpeed(self, value):
        self.vspeed = max(self.min_value, min(value, self.max_value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 10

        # ===== METAL ÇERÇEVE =====
        metal = QRadialGradient(cx, cy, radius)
        metal.setColorAt(0, QColor(150,150,150))
        metal.setColorAt(1, QColor(60,60,60))

        painter.setBrush(metal)
        painter.setPen(QPen(QColor(25,25,25), 4))
        painter.drawEllipse(cx - radius, cy - radius,
                            radius*2, radius*2)

        # ===== PANEL =====
        inner_radius = radius - 8

        panel = QRadialGradient(cx, cy, inner_radius)
        panel.setColorAt(0, QColor(85,85,85))
        panel.setColorAt(1, QColor(30,30,30))

        painter.setBrush(panel)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius*2, inner_radius*2)

        # ===== 240° YAY =====
        start_angle = 210
        span_angle = 240

        # ===== SKALA =====
        for value in range(self.min_value, self.max_value + 1, 5):

            ratio = (value - self.min_value) / (self.max_value - self.min_value)
            angle = start_angle - (span_angle * ratio)
            rad = math.radians(angle)

            # Tick
            if value == 0:
                tick_length = 22
                painter.setPen(QPen(Qt.white, 3))
            else:
                tick_length = 18
                painter.setPen(QPen(Qt.white, 2))

            x1 = cx + (inner_radius - tick_length) * math.cos(rad)
            y1 = cy - (inner_radius - tick_length) * math.sin(rad)
            x2 = cx + inner_radius * math.cos(rad)
            y2 = cy - inner_radius * math.sin(rad)

            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            # ===== SAYILAR =====
            painter.setPen(Qt.white)

            if value == 0:
                font = QFont("Segoe UI", 11, QFont.Bold)
            else:
                font = QFont("Segoe UI", 10, QFont.Bold)

            painter.setFont(font)

            text_radius = inner_radius - 30  # tick'e yakın
            tx = cx + text_radius * math.cos(rad)
            ty = cy - text_radius * math.sin(rad)

            rect = QRectF(tx - 22, ty - 16, 44, 32)
            painter.drawText(rect, Qt.AlignCenter, str(value))

        # ===== ORTA YAZI =====
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(QRectF(cx - 40, cy - 18, 80, 30),
                         Qt.AlignCenter, "VSI")

        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRectF(cx - 40, cy + 5, 80, 25),
                         Qt.AlignCenter, "m/s")

        # ===== İBRE =====
        ratio = (self.vspeed - self.min_value) / (self.max_value - self.min_value)
        angle = start_angle - (span_angle * ratio)
        rad = math.radians(angle)

        needle_length = inner_radius - 35
        nx = cx + needle_length * math.cos(rad)
        ny = cy - needle_length * math.sin(rad)

        painter.setPen(QPen(Qt.white, 4))
        painter.drawLine(int(cx), int(cy), int(nx), int(ny))

        painter.setBrush(Qt.white)
        painter.drawEllipse(int(cx - 5), int(cy - 5), 10, 10)

        # ===== CAM EFEKTİ =====
        glass = QRadialGradient(cx - 40, cy - 40, inner_radius)
        glass.setColorAt(0, QColor(255,255,255,35))
        glass.setColorAt(1, QColor(255,255,255,0))

        painter.setBrush(glass)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius,
                            cy - inner_radius,
                            inner_radius*2,
                            inner_radius*2)

class AttitudeIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.pitch = 0
        self.roll = 0

        # Bir tık daha küçültüldü
        self.setFixedSize(195, 195)

    def setAttitude(self, pitch, roll):
        self.pitch = max(-25, min(25, pitch))
        self.roll = max(-45, min(45, roll))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 5

        # ================= METAL FRAME =================
        frameGradient = QRadialGradient(cx, cy, radius)
        frameGradient.setColorAt(0.0, QColor(100, 100, 100))
        frameGradient.setColorAt(1.0, QColor(25, 25, 25))

        painter.setBrush(frameGradient)
        painter.setPen(QPen(QColor(20, 20, 20), 3))
        painter.drawEllipse(cx - radius, cy - radius,
                            radius * 2, radius * 2)

        inner_radius = radius - 9

        # İç siyah halka
        painter.setBrush(QColor(18, 18, 18))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)

        # ================= HORIZON DRAW =================
        painter.save()

        clipPath = QPainterPath()
        clipPath.addEllipse(cx - inner_radius, cy - inner_radius,
                            inner_radius * 2, inner_radius * 2)
        painter.setClipPath(clipPath)

        painter.translate(cx, cy)
        painter.rotate(-self.roll)

        pitch_scale = 3.2
        pitch_offset = self.pitch * pitch_scale

        # SKY
        skyGradient = QLinearGradient(0, -inner_radius, 0, 0)
        skyGradient.setColorAt(0, QColor(25, 110, 210))
        skyGradient.setColorAt(1, QColor(120, 180, 255))

        painter.setBrush(skyGradient)
        painter.drawRect(-inner_radius * 2,
                         -inner_radius * 2 + pitch_offset,
                         inner_radius * 4,
                         inner_radius * 2)

        # GROUND
        groundGradient = QLinearGradient(0, 0, 0, inner_radius)
        groundGradient.setColorAt(0, QColor(170, 110, 60))
        groundGradient.setColorAt(1, QColor(100, 60, 30))

        painter.setBrush(groundGradient)
        painter.drawRect(-inner_radius * 2,
                         pitch_offset,
                         inner_radius * 4,
                         inner_radius * 2)

        # Horizon line
        painter.setPen(QPen(Qt.white, 2))
        painter.drawLine(-inner_radius * 2, pitch_offset,
                         inner_radius * 2, pitch_offset)

        # ================= PITCH LINES =================
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.setPen(QPen(Qt.white, 2))

        for angle in [-20, -10, 10, 20]:
            y = pitch_offset - (angle * pitch_scale)

            painter.drawLine(-30, y, 30, y)

            text = str(abs(angle))

            painter.drawText(QRectF(-55, y - 8, 25, 16),
                             Qt.AlignCenter, text)

            painter.drawText(QRectF(30, y - 8, 25, 16),
                             Qt.AlignCenter, text)

        painter.restore()

        # ================= AIRCRAFT SYMBOL =================
        painter.setPen(QPen(QColor(255, 215, 0), 3))
        painter.drawLine(cx - 25, cy, cx + 25, cy)
        painter.drawLine(cx, cy, cx, cy + 8)

        # ================= GLASS EFFECT =================
        glass = QRadialGradient(cx - 25, cy - 25, inner_radius)
        glass.setColorAt(0, QColor(255, 255, 255, 35))
        glass.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setBrush(glass)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_radius,
                            cy - inner_radius,
                            inner_radius * 2,
                            inner_radius * 2)

class CompassIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.heading = 0
        self.setFixedSize(195, 195)

    def setHeading(self, heading):
        self.heading = heading % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 5
        inner_radius = radius - 12

        # FRAME
        painter.setBrush(QColor(60, 60, 60))
        painter.setPen(QPen(QColor(20, 20, 20), 3))
        painter.drawEllipse(cx-radius, cy-radius, radius*2, radius*2)

        # INNER
        painter.setBrush(QColor(15, 15, 15))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx-inner_radius, cy-inner_radius,
                            inner_radius*2, inner_radius*2)

        # ================= ROTATING DISC =================
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self.heading)

        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)

        for deg in range(0, 360, 3):

            painter.save()
            painter.rotate(deg)

            if deg % 30 == 0:

                # Üçgen marker
                painter.setBrush(Qt.white)
                painter.setPen(Qt.NoPen)

                triangle = QPolygonF([
                    QPointF(0, -inner_radius + 4),
                    QPointF(-6, -inner_radius + 18),
                    QPointF(6, -inner_radius + 18)
                ])
                painter.drawPolygon(triangle)

                # SAYI (DAHA DIŞA ALINDI)
                value = deg // 10
                painter.setPen(Qt.white)

                painter.drawText(-12,
                                 -inner_radius + 22,  # <-- BURAYI 32'den 22'ye çektik
                                 24,
                                 20,
                                 Qt.AlignCenter,
                                 str(value))

            else:
                painter.setPen(QPen(Qt.white, 1))
                painter.drawLine(0,
                                 -inner_radius + 8,
                                 0,
                                 -inner_radius + 16)

            painter.restore()

        painter.restore()

        # ================= SABİT UÇAK =================
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)

        plane = QPainterPath()

        plane.moveTo(cx, cy - 38)
        plane.lineTo(cx - 12, cy - 10)
        plane.lineTo(cx - 40, cy - 2)
        plane.lineTo(cx - 38, cy + 4)
        plane.lineTo(cx - 10, cy + 2)
        plane.lineTo(cx - 6, cy + 22)
        plane.lineTo(cx - 12, cy + 26)
        plane.lineTo(cx - 12, cy + 32)
        plane.lineTo(cx + 12, cy + 32)
        plane.lineTo(cx + 12, cy + 26)
        plane.lineTo(cx + 6, cy + 22)
        plane.lineTo(cx + 10, cy + 2)
        plane.lineTo(cx + 38, cy + 4)
        plane.lineTo(cx + 40, cy - 2)
        plane.lineTo(cx + 12, cy - 10)
        plane.closeSubpath()

        painter.drawPath(plane)

        # ÜST REFERANS
        painter.setPen(QPen(Qt.white, 4))
        painter.drawLine(cx - 14,
                         cy - inner_radius + 2,
                         cx + 14,
                         cy - inner_radius + 2)


class TurnCoordinatorIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 200)
        self.bank_angle = 0
        self.slip = 0

    def setBankAngle(self, angle):
        self.bank_angle = max(-30, min(30, angle))
        self.update()

    def setSlip(self, value):
        self.slip = max(-1, min(1, value))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) / 2 - 6

        # ================= FRAME =================
        frame_grad = QRadialGradient(cx, cy, radius)
        frame_grad.setColorAt(0.75, QColor(70, 70, 70))
        frame_grad.setColorAt(1.0, QColor(30, 30, 30))

        p.setBrush(frame_grad)
        p.setPen(QPen(QColor(25, 25, 25), 3))
        p.drawEllipse(cx - radius, cy - radius,
                      radius * 2, radius * 2)

        # ================= INNER PANEL =================
        inner = radius - 10
        p.setBrush(QColor(18, 18, 18))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - inner, cy - inner,
                      inner * 2, inner * 2)

        # ================= ÜST REFERANS BLOKLARI =================
        p.setPen(QPen(Qt.white, 5))
        top_y = cy - inner + 40

        p.drawLine(cx - 50, top_y, cx - 30, top_y)
        p.drawLine(cx + 30, top_y, cx + 50, top_y)

        # ================= DÖNEN UÇAK =================
        p.save()
        p.translate(cx, cy - 5)
        p.rotate(self.bank_angle)

        p.setPen(Qt.NoPen)
        p.setBrush(Qt.white)

        plane = QPainterPath()
        plane.moveTo(0, -22)
        plane.lineTo(-8, -4)
        plane.lineTo(-42, 2)
        plane.lineTo(-40, 6)
        plane.lineTo(-6, 4)
        plane.lineTo(-4, 15)
        plane.lineTo(4, 15)
        plane.lineTo(6, 4)
        plane.lineTo(40, 6)
        plane.lineTo(42, 2)
        plane.lineTo(8, -4)
        plane.closeSubpath()

        p.drawPath(plane)
        p.restore()

        # ================= YAZILAR =================
        p.setPen(Qt.white)

        font_title = QFont("Arial", 8, QFont.Bold)
        p.setFont(font_title)
        p.drawText(cx - 60, cy + 18, 120, 18,
                   Qt.AlignCenter, "TURN COORDINATOR")

        font_small = QFont("Arial", 8, QFont.Bold)
        p.setFont(font_small)
        p.drawText(cx - 25, cy + 32, 50, 16,
                   Qt.AlignCenter, "2 MIN")

        # ================= SLIP TUBE =================
        tube_w = 90
        tube_h = 16

        tube_rect = QRectF(cx - tube_w / 2,
                           cy + 50,
                           tube_w,
                           tube_h)

        p.setBrush(QColor(230, 230, 230))
        p.setPen(QPen(Qt.white, 1))
        p.drawRoundedRect(tube_rect, 8, 8)

        # Orta referans çizgileri
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(cx - 12, cy + 50,
                   cx - 12, cy + 66)

        p.drawLine(cx + 12, cy + 50,
                   cx + 12, cy + 66)

        # ================= TOP =================
        ball_offset = self.slip * (tube_w / 2 - 15)

        p.setBrush(QColor(40, 40, 40))
        p.setPen(Qt.NoPen)

        p.drawEllipse(cx - 7 + ball_offset,
                      cy + 53,
                      14,
                      14)

        # ================= L - R =================
        font_lr = QFont("Arial", 10, QFont.Bold)
        p.setFont(font_lr)
        p.setPen(Qt.white)

        p.drawText(cx - 50, cy + 82, "L")
        p.drawText(cx + 38, cy + 82, "R")