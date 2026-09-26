"""Reparte el abono en dos medios. No abre la venta."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from src.clientes_fiado.interfaz.cobro.medios.mixto import CLAVES, cobrar
from src.utils.dinero import redondear_dinero
from src.utils.qt_compat import qt_exec


class HojaMixtoAbono(QDialog):
    def __init__(self, monto, parent=None):
        super().__init__(parent)
        self.monto = redondear_dinero(monto)
        self.partes = None
        self.resultado = None
        self.setWindowTitle("Mixto")
        self.setModal(True)
        self.setStyleSheet("QDialog { background: #F8FAFC; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)
        titulo = QLabel(f"Repartí ${self.monto:,.2f} en dos medios")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #0F172A; font-size: 16px; font-weight: 800; background: transparent;")
        lay.addWidget(titulo)
        self.campos = {}
        for clave in CLAVES:
            fila = QHBoxLayout()
            nombre = QLabel(clave)
            nombre.setStyleSheet("color: #0F172A; font-weight: 800; background: transparent;")
            caja = QLineEdit()
            caja.setPlaceholderText("0.00")
            caja.setStyleSheet(
                "QLineEdit { background: white; color: #0F172A; border: 1px solid #CBD5E1;"
                " border-radius: 10px; padding: 8px; font-size: 16px; font-weight: 800; }"
            )
            self.campos[clave] = caja
            fila.addWidget(nombre, 1)
            fila.addWidget(caja, 1)
            lay.addLayout(fila)
        self.aviso = QLabel("")
        self.aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aviso.setStyleSheet("color: #DC2626; font-weight: 800; background: transparent;")
        lay.addWidget(self.aviso)
        confirmar = QPushButton("Confirmar")
        confirmar.setMinimumHeight(48)
        confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        confirmar.setStyleSheet(
            "QPushButton { background: #0F172A; color: white; border: none; border-radius: 12px;"
            " font-weight: 800; font-size: 14px; }"
        )
        confirmar.clicked.connect(self._confirmar)
        lay.addWidget(confirmar)

    def _confirmar(self):
        partes = {}
        for clave, caja in self.campos.items():
            texto = (caja.text() or "").strip().replace("$", "").replace(",", ".")
            if not texto:
                partes[clave] = 0
                continue
            try:
                partes[clave] = float(texto)
            except ValueError:
                self.aviso.setText("Hay un importe que no es un número.")
                return
        resultado = cobrar(self.monto, partes)
        if not resultado.ok:
            self.aviso.setText(resultado.detalle)
            return
        self.partes = partes
        self.resultado = resultado
        self.accept()


def pedir_partes(parent, monto):
    dlg = HojaMixtoAbono(monto, parent)
    if qt_exec(dlg) and dlg.resultado and dlg.resultado.ok:
        return dlg.resultado
    return None
