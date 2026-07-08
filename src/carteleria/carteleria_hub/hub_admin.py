from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor
from src.carteleria.carteleria_hub.hub_principal import HubCard

class CarteleriaAdminHub(QWidget):
    request_back = pyqtSignal()
    request_config = pyqtSignal()
    request_lan = pyqtSignal()
    request_inventario = pyqtSignal()
    request_promos = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setObjectName("AdminHero")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 16, 24, 16)
        
        btn_back = QPushButton("← Volver")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.clicked.connect(self.request_back.emit)
        
        title = QLabel("⚙️ TV Admin - Panel de Control")
        title.setStyleSheet("font-size: 22px; font-weight: bold; border: none; background: transparent;")
        
        h.addWidget(btn_back)
        h.addStretch()
        h.addWidget(title)
        h.addStretch()
        root.addWidget(header)
        
        # Body
        body = QVBoxLayout()
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        grid = QGridLayout()
        grid.setSpacing(30)
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_config = HubCard("Cartelería Config", "🛠️", "#FFF1F2", "#9F1239", "Mensajes y autorización IP")
        card_config.clicked.connect(self.request_config.emit)
        
        card_lan = HubCard("Servidor LAN", "🌐", "#F0F9FF", "#0369A1", "Maestra / Esclava")
        card_lan.clicked.connect(self.request_lan.emit)
        
        card_inv = HubCard("Gestión de Inventario", "📦", "#F0FDF4", "#15803D", "Stock y productos")
        card_inv.clicked.connect(self.request_inventario.emit)
        
        card_promos = HubCard("Motor de Promociones", "🏷️", "#FFFBEB", "#B45309", "Gestión de Reglas de Precio")
        card_promos.clicked.connect(self.request_promos.emit)
        
        grid.addWidget(card_inv, 0, 0)
        grid.addWidget(card_promos, 0, 1)
        grid.addWidget(card_config, 1, 0)
        grid.addWidget(card_lan, 1, 1)
        
        body.addLayout(grid)
        root.addLayout(body)
