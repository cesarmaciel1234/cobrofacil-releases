from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap

class CyberNodeCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, origen, role, is_active=True):
        super().__init__()
        self.origen = origen
        self.role = role
        self.is_active = is_active
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(140, 80)

        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(10, 10, 10, 10)
        self.lay.setSpacing(5)

        icon = "🛒" if "CAJA" in role else "📺" if "CARTEL" in role else "💻" if "ADMIN" in role else "⚙️"

        self.lbl_title = QLabel(f"{icon} {role}")
        self.lbl_title.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_origen = QLabel(origen.split('|')[0] if '|' in origen else origen)
        self.lbl_origen.setFont(QFont("Consolas", 7))
        self.lbl_origen.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_status = QLabel("● ONLINE")
        self.lbl_status.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lay.addWidget(self.lbl_title)
        self.lay.addWidget(self.lbl_origen)
        self.lay.addWidget(self.lbl_status)

        self.update_style()

    def update_style(self, selected=False):
        if not self.is_active:
            bg = "#1E1E1E"
            border = "#333333"
            color_title = "#666666"
            color_status = "#444444"
            status_txt = "○ OFFLINE"
        elif selected:
            bg = "rgba(16, 185, 129, 0.1)"
            border = "#10B981"
            color_title = "#10B981"
            color_status = "#34D399"
            status_txt = "● SELECTED"
        else:
            bg = "rgba(59, 130, 246, 0.05)"
            border = "#3B82F6"
            color_title = "#60A5FA"
            color_status = "#3B82F6"
            status_txt = "● ONLINE"

        self.setStyleSheet(f"""
            CyberNodeCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            CyberNodeCard:hover {{
                background-color: rgba(59, 130, 246, 0.15);
                border: 1px solid #60A5FA;
            }}
        """)
        self.lbl_title.setStyleSheet(f"color: {color_title}; border: none; background: transparent;")
        self.lbl_origen.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        self.lbl_status.setStyleSheet(f"color: {color_status}; border: none; background: transparent;")
        self.lbl_status.setText(status_txt)

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.origen)

