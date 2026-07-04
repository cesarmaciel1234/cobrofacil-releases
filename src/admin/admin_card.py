from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal, Qt

class AdminCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, icon, palette_name, sub, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            AdminCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            AdminCard:hover {
                background-color: #F8FAFC;
                border: 1px solid #94A3B8;
            }
        """)
        self.setFixedSize(170, 140)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #1E293B; background: transparent; border: none;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_sub = QLabel(sub)
        lbl_sub.setStyleSheet("font-size: 10px; color: #64748B; background: transparent; border: none;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lay.addWidget(lbl_icon)
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_sub)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
