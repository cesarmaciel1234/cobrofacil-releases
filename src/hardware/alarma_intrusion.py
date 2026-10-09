"""Toast de alarma de intrusión del cajón.

Módulo separado que muestra una alerta visual cuando el cajón se abre
manualmente con la llave (sin autorización). Corre por encima de todas
las ventanas sin interferir con el cajero.

Si el motor de alarma no funciona, no inyecta datos y no afecta el sistema.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
import logging

logger = logging.getLogger(__name__)


class ToastAlarmaIntrusion(QWidget):
    """Toast flotante de alarma de intrusión.

    Ventana sin marco que se superpone a todo mostrando la alerta de
    intrusión cuando el cajón se abre con la llave.
    """

    cerrar_senal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToastAlarmaIntrusion")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Configuración de duración (5 segundos por defecto)
        self._duracion = 5000
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._ocultar)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Etiqueta de alerta
        self.label = QLabel("⚠️ CAJÓN ABIERTO SIN AUTORIZACIÓN ⚠️")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(220, 38, 38, 240);
                color: white;
                font-size: 28px;
                font-weight: 900;
                padding: 20px 40px;
                border-radius: 15px;
                border: 4px solid white;
            }
        """)
        layout.addWidget(self.label)

        # Oculto por defecto
        self.hide()

    def mostrar(self, duracion_ms=5000):
        """Muestra el toast por el tiempo especificado."""
        try:
            self._duracion = duracion_ms
            self.adjustSize()

            # Centrar en pantalla
            if self.parent():
                geo = self.parent().geometry()
                x = geo.x() + (geo.width() - self.width()) // 2
                y = geo.y() + 50  # 50px desde el tope
            else:
                from PyQt6.QtWidgets import QApplication
                screen = QApplication.primaryScreen()
                geo = screen.availableGeometry()
                x = geo.x() + (geo.width() - self.width()) // 2
                y = geo.y() + 50

            self.move(x, y)
            self.show()
            self.raise_()

            # Iniciar timer para ocultar
            self._timer.start(self._duracion)
            logger.info("Toast de alarma de intrusión mostrado")
        except Exception as e:
            logger.error(f"Error al mostrar toast de alarma: {e}")

    def _ocultar(self):
        """Oculta el toast y emite señal de cierre."""
        try:
            self.hide()
            self.cerrar_senal.emit()
            logger.info("Toast de alarma de intrusión ocultado")
        except Exception as e:
            logger.error(f"Error al ocultar toast de alarma: {e}")

    def closeEvent(self, event):
        """Limpieza al cerrar."""
        try:
            if self._timer.isActive():
                self._timer.stop()
        except:
            pass
        event.accept()


# Instancia singleton del toast
_toast_instance = None


def mostrar_alarma_intrusion(duracion_ms=5000):
    """Muestra el toast de alarma de intrusión.

    Si ya hay un toast visible, lo reinicia con la nueva duración.

    Args:
        duracion_ms: Duración en milisegundos (default 5000 = 5 segundos)
    """
    global _toast_instance

    try:
        if _toast_instance is None:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is None:
                logger.warning("No hay QApplication activa, no se puede mostrar alarma")
                return

            # Usar la ventana activa como parent
            active_window = app.activeWindow()
            _toast_instance = ToastAlarmaIntrusion(active_window)

        if _toast_instance._timer.isActive():
            _toast_instance._timer.stop()

        _toast_instance.mostrar(duracion_ms)
    except Exception as e:
        logger.error(f"Error al mostrar alarma de intrusión: {e}")
        # No inyecta datos, el sistema sigue funcionando


def ocultar_alarma_intrusion():
    """Oculta el toast de alarma de intrusión si está visible."""
    global _toast_instance

    try:
        if _toast_instance is not None and _toast_instance.isVisible():
            _toast_instance._ocultar()
    except Exception as e:
        logger.error(f"Error al ocultar alarma de intrusión: {e}")


def limpiar():
    """Limpia la instancia singleton (para testing o reinicio)."""
    global _toast_instance

    try:
        if _toast_instance is not None:
            _toast_instance.close()
            _toast_instance.deleteLater()
        _toast_instance = None
    except Exception as e:
        logger.error(f"Error al limpiar alarma de intrusión: {e}")
