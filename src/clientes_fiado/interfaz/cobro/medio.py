"""El paréntesis del abono: llama al medio. No llama al paso 6."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.clientes_fiado.interfaz.cobro.medios.puerta import REGISTRO, cobrar
from src.utils.qt_compat import qt_exec

MEDIOS = tuple(REGISTRO)


class DialogoMedioAbono(QDialog):
    def __init__(self, parent=None, monto=0):
        super().__init__(parent)
        self.monto = monto
        self.resultado = None
        self.medio = ""
        self.setWindowTitle("Medio del pago")
        self.setModal(True)
        self.setStyleSheet("QDialog { background: #F8FAFC; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)
        titulo = QLabel("¿Con qué paga?")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #0F172A; font-size: 20px; font-weight: 800; background: transparent;")
        lay.addWidget(titulo)
        fila = QHBoxLayout()
        fila.setSpacing(8)
        for nombre in MEDIOS:
            if nombre == "Mixto":
                continue
            boton = QPushButton(nombre)
            boton.setMinimumHeight(52)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setStyleSheet(
                "QPushButton { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;"
                " border-radius: 12px; font-size: 14px; font-weight: 800; padding: 8px 14px; }"
                "QPushButton:hover { background: #EFF6FF; border-color: #1D4ED8; }"
            )
            boton.clicked.connect(lambda _=False, n=nombre: self._elegir(n))
            fila.addWidget(boton)
        lay.addLayout(fila)
        mixto = QPushButton("Mixto")
        mixto.setMinimumHeight(52)
        mixto.setCursor(Qt.CursorShape.PointingHandCursor)
        mixto.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;"
            " border-radius: 12px; font-size: 14px; font-weight: 800; padding: 8px 14px; }"
            "QPushButton:hover { background: #EFF6FF; border-color: #1D4ED8; }"
        )
        mixto.clicked.connect(lambda: self._elegir("Mixto"))
        lay.addWidget(mixto)

    def _elegir(self, nombre):
        if nombre == "Mixto":
            from src.clientes_fiado.interfaz.cobro.medios.hoja import pedir_partes

            resultado = pedir_partes(self, self.monto)
        else:
            resultado = cobrar(nombre, self.monto)
        if not resultado or not resultado.ok:
            return
        self.resultado = resultado
        self.medio = resultado.medio
        self.accept()


def pedir_medio(parent=None, monto=0):
    dlg = DialogoMedioAbono(parent, monto)
    if qt_exec(dlg) and dlg.resultado and dlg.resultado.ok:
        return dlg.resultado
    return None
