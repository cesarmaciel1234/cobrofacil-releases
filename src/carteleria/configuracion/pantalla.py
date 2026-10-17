from PyQt6.QtWidgets import QStackedWidget
from PyQt6.QtCore import pyqtSignal

from src.carteleria.configuracion.panel import CarteleriaConfigPanel


class Admin15Carteleria(QStackedWidget):
    request_dashboard = pyqtSignal()
    request_screen = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_panel = CarteleriaConfigPanel()
        self.addWidget(self.config_panel)
        self.setCurrentIndex(0)
        self.config_panel.request_back.connect(self.request_dashboard.emit)
