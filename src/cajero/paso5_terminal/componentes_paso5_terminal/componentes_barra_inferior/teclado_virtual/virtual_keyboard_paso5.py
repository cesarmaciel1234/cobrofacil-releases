from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint

from .keyboard_ui import init_ui, build_keys
from .keyboard_logic import handle_key_press

class VirtualKeyboardPaso5(QWidget):
    """
    Teclado Virtual Industrial para entornos táctiles de escritorio (Paso 5).
    Diseñado para flotar sobre la aplicación y enviar pulsaciones sin robar el foco.
    Estética de colores claros estilo Android (Gboard Light Theme).
    Tamaño fijo de 680x310px.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(680, 310)

        self.shift_active = False
        self.layout_mode = "abc"
        self.letter_buttons = {}
        self._drag_position = QPoint()

        init_ui(self)

    def set_layout_mode(self, mode):
        """Establece el layout ('abc' o '123') y reconstruye las teclas sin cambiar de tamaño."""
        if mode in ("abc", "123") and self.layout_mode != mode:
            self.layout_mode = mode
            if hasattr(self, 'keys_layout'):
                build_keys(self)

    def reposition_keyboard(self):
        """Calcula el tamaño y la posición ideal del teclado respecto a la ventana activa."""
        if hasattr(self, 'drag_bar'):
            self.drag_bar.show()

        active_win = QApplication.activeWindow() or self.parent()
        if active_win:
            win_geom = active_win.geometry()
            kb_width = 680
            kb_height = 310

            x = win_geom.x() + (win_geom.width() - kb_width) // 2
            y = win_geom.y() + win_geom.height() - kb_height - 15

            self.resize(kb_width, kb_height)
            self.move(x, y)

    def showEvent(self, event):
        self.reposition_keyboard()
        super().showEvent(event)

    def on_key_press(self, key_text):
        handle_key_press(self, key_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
