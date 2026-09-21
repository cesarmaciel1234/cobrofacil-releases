from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt

from src.cajero.paso5_terminal.dialogos.dialogo_editar_cantidad.logica.teclas import aplicar_tecla
from src.cajero.paso5_terminal.dialogos.dialogo_editar_cantidad.logica.valor import leer_cantidad
from src.cajero.paso5_terminal.dialogos.dialogo_editar_cantidad.ui.armar import armar_cuerpo


class DialogoEditarCantidad(QDialog):
    def __init__(self, cant_actual, nombre, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setObjectName("TerminalDialogoEditarCantidad")
        if parent is not None:
            w = max(820, int(parent.width() * 0.42))
            h = max(480, int(parent.height() * 0.44))
            w = min(w, max(640, parent.width() - 80))
            h = min(h, max(400, parent.height() - 80))
        else:
            w, h = 860, 520
        self.setFixedSize(w, h)
        self.spin = armar_cuerpo(self, cant_actual, nombre)
        self.spin.setFocus()
        self.spin.selectAll()

    def keyPressEvent(self, event):
        if not aplicar_tecla(self, event):
            super().keyPressEvent(event)

    def get_value(self):
        return leer_cantidad(self.spin)
