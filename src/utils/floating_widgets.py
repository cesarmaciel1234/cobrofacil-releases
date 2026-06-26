import src.utils.qt_compat  # noqa: F401 — enums Qt6 en namespace Qt
from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PyQt6.QtGui import QColor, QCursor

class BotonFlotanteRegreso(QPushButton):
    """
    BURBUJA DE RETORNO ASISTENTE ELITE 2026 - MODO BOMBERO
    Diseño circular con parpadeo de sirena y lógica inteligente de arrastre.
    """
    clicked_return = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("🚨", parent)
        self.setFixedSize(65, 65)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setCursor(Qt.PointingHandCursor)
        
        # Sombra profunda para estética Midnight Premium
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

        self.old_pos = None
        self.press_pos = None
        self._emergency_state = False
        
        # Timer de Parpadeo "Bombero" (Frecuencia de sirena)
        self.timer_flash = QTimer(self)
        self.timer_flash.timeout.connect(self._toggle_flash)
        self.timer_flash.start(400)

    def _toggle_flash(self):
        self._emergency_state = not self._emergency_state
        if self._emergency_state:
            # Rojo Sirena
            style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EF4444, stop:1 #B91C1C); border: 3px solid white;"
        else:
            # Azul Policial
            style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3B82F6, stop:1 #1E40AF); border: 3px solid #60A5FA;"
        
        self.setStyleSheet(f"""
            QPushButton {{
                {style}
                color: white; font-size: 32px; font-weight: bold;
                border-radius: 32px;
            }}
            QPushButton:hover {{
                border-color: #FEE2E2;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            self.press_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Si el ratón se soltó, evaluar si fue arrastre o click real
        if event.button() == Qt.LeftButton:
            if self.press_pos:
                # Calcular distancia recorrida en píxeles (Manhattan Length)
                dist = (event.globalPosition().toPoint() - self.press_pos).manhattanLength()
                if dist <= 20: # Si se movió menos de 20px (ajustado para táctil), es un click real (retorno)
                    self.clicked_return.emit()
        self.old_pos = None
        self.press_pos = None
        super().mouseReleaseEvent(event)

# BotonFlotanteCajon ha sido eliminado y fusionado con BotonFlotanteRegreso para unificar el flujo de trabajo.
