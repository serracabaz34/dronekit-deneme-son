from PyQt5.QtWidgets import *
from arayuz_backend import arayuzBackend

uygulama = QApplication([])
pencere = arayuzBackend()
pencere.show()
uygulama.exec()
