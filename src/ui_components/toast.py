from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QPainter, QPainterPath

class Toast(QWidget):
    def __init__(self, parent, message, type="info", duration=3000):
        super().__init__(parent)
        self.message = message
        self.type = type
        self.duration = duration
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.setup_ui()
        self.position_widget(parent)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_in()
        
        QTimer.singleShot(self.duration, self.fade_out)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Color mapping
        colors = {
            "success": "#4CAF50",
            "error": "#F44336",
            "warning": "#FFC107",
            "info": "#03A9F4"
        }
        bg_color = colors.get(self.type, "#333333")
        
        # Determine icon
        icons = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        icon = icons.get(self.type, "ℹ️")
        
        # Main container with rounded corners and background
        self.container = QWidget(self)
        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 8px;
                color: white;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(15, 10, 15, 10)
        
        lbl_icon = QLabel(icon)
        lbl_message = QLabel(self.message)
        lbl_message.setWordWrap(True)
        
        container_layout.addWidget(lbl_icon)
        container_layout.addWidget(lbl_message)
        
        layout.addWidget(self.container)

    def position_widget(self, parent):
        if not parent:
            return
            
        # Position at bottom center of parent window
        parent_geo = parent.geometry()
        x = parent_geo.x() + (parent_geo.width() - self.sizeHint().width()) // 2
        y = parent_geo.y() + parent_geo.height() - self.sizeHint().height() - 50
        
        self.move(x, y)

    def fade_in(self):
        self.anim_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_in.setDuration(400)
        self.anim_in.setStartValue(0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim_in.start()
        self.show()

    def fade_out(self):
        self.anim_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_out.setDuration(400)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim_out.finished.connect(self.close)
        self.anim_out.start()

def show_toast(parent, message, type="info", duration=3000):
    t = Toast(parent, message, type, duration)
    return t
