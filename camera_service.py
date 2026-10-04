from PyQt5.QtCore import QThread, pyqtSignal
import cv2


class CameraService(QThread):

    frame_ready = pyqtSignal(object)

    def __init__(self, source=0):
        super().__init__()
        self.source = source
        self._running = True

    def run(self):

        cap = cv2.VideoCapture(self.source)

        while self._running:
            ret, frame = cap.read()
            if ret:
                self.frame_ready.emit(frame)

        cap.release()

    def stop(self):
        self._running = False