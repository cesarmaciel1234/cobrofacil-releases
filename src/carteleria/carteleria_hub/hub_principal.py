from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor

class HubCard(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, title, icon, color_bg, color_txt, desc=""):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(f"""
            QFrame {{
                background: {color_bg};
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.1);
            }}
            QFrame:hover {{
                border: 2px solid {color_txt};
            }}
        """)
        self.setFixedSize(280, 180)
        
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color_txt}; background: transparent; border: none;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(f"font-size: 12px; color: {color_txt}; opacity: 0.8; background: transparent; border: none;")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lay.addWidget(lbl_icon)
        lay.addSpacing(10)
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_desc)

    def mousePressEvent(self, event):
        self.clicked.emit()

class CarteleriaHubMenu(QWidget):
    request_back = pyqtSignal()
    request_launch_tv = pyqtSignal()
    request_admin = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setObjectName("AdminHero")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 16, 24, 16)
        
        btn_back = QPushButton("← Volver al Dashboard")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.clicked.connect(self.request_back.emit)
        
        title = QLabel("📺 Cartelería Hub")
        title.setStyleSheet("font-size: 22px; font-weight: bold; border: none; background: transparent;")
        
        h.addWidget(btn_back)
        h.addStretch()
        h.addWidget(title)
        h.addStretch()
        root.addWidget(header)
        
        # Body
        body = QVBoxLayout()
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        row = QHBoxLayout()
        row.setSpacing(40)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_tv = HubCard("Lanzar TV", "📺", "#EFF6FF", "#1D4ED8", "Abre la cartelería real a pantalla completa")
        card_tv.clicked.connect(self.request_launch_tv.emit)
        
        card_admin = HubCard("TV Admin", "⚙️", "#FEF2F2", "#B91C1C", "Configura la TV, Inventario y Descuentos")
        card_admin.clicked.connect(self.request_admin.emit)
        
        row.addWidget(card_tv)
        row.addWidget(card_admin)
        
        body.addLayout(row)
        root.addLayout(body)
