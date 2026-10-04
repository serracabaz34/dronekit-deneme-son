from PyQt5.QtWidgets import *
from arayuzBackend import arayuz_backend

uygulama = QApplication([])
pencere = arayuz_backend()
pencere.show()
uygulama.exec()