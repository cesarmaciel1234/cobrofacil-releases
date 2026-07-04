from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
import sys
import random
import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea, QLineEdit, QProgressBar, QGridLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
try:
    from src.base_de_datos.database import db_manager
    from src.config import config
except ImportError:
    from database import db_manager


from src.admin.ai_boss.componentes.ai_bubble import AIBubble

class AIBubble(QPushButton):
    """
    Burbuja flotante interactiva que permite invocar al AI Boss desde cualquier pantalla.
    Diseño premium con efecto de pulsación.
    """
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("🧠", parent)
        self.setFixedSize(60, 60)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                
                color: #1e293b;
                font-size: 30px;
                border-radius: 30px;
                border: 2px solid #a855f7;
            }
            QPushButton:hover {
                
                border-
            }
        """)
        
        # Efecto de sombra/resplandor
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(168, 85, 247, 150))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
        
        # Timer para animación de pulsación sutil
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.animate_pulse)
        self.pulse_timer.start(1000)
        self.pulse_scale = 1.0
        self.growing = True

    def animate_pulse(self):
        if self.growing:
            self.pulse_scale += 0.05
            if self.pulse_scale >= 1.1: self.growing = False
        else:
            self.pulse_scale -= 0.05
            if self.pulse_scale <= 1.0: self.growing = True
        
        self.shadow.setBlurRadius(int(15 * self.pulse_scale))
        self.update()

    def mousePressEvent(self, event):
        # Permitir que el botón sea arrastrable en el futuro (opcional)
        super().mousePressEvent(event)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = Admin12AIBoss()
    win.showMaximized()
    sys.exit(qt_exec(app))