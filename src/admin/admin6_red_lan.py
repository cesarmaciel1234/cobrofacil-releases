"""Panel dedicado de red LAN / multicaja. (Wrapper que usa el componente unificado)"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from src.ui_components.red_lan_panel import SharedRedLanPanel

class Admin6RedLan(QWidget):
    request_dashboard = pyqtSignal()
    request_screen    = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # Instanciar el panel compartido indicando que se deben mostrar los botones de administrador
        self.panel = SharedRedLanPanel(self, show_admin_buttons=True)
        
        # Reconectar señales
        self.panel.request_dashboard.connect(self.request_dashboard.emit)
        self.panel.request_screen.connect(self.request_screen.emit)
        
        root.addWidget(self.panel)