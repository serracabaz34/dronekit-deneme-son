from PyQt5.QtCore import QThread, pyqtSignal
import time


class TelemetryService(QThread):

    airspeed_changed = pyqtSignal(float)
    altitude_changed = pyqtSignal(float)
    heading_changed = pyqtSignal(float)
    pitch_roll_changed = pyqtSignal(float, float)

    def __init__(self, vehicle):
        super().__init__()
        self.vehicle = vehicle
        self._running = True

    def run(self):
        while self._running:

            if self.vehicle:

                # Airspeed
                airspeed = self.vehicle.airspeed or 0
                self.airspeed_changed.emit(airspeed)

                # Altitude
                altitude = self.vehicle.location.global_relative_frame.alt or 0
                self.altitude_changed.emit(altitude)

                # Heading
                heading = self.vehicle.heading or 0
                self.heading_changed.emit(heading)

                # Pitch / Roll
                pitch = self.vehicle.attitude.pitch
                roll = self.vehicle.attitude.roll
                self.pitch_roll_changed.emit(pitch, roll)

            time.sleep(0.2)

    def stop(self):
        self._running = False