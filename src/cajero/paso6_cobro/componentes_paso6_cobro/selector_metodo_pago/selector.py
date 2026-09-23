"""Junta las dos filas. El clic avisa a la ventana de cobro."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago.grilla.filas import (
    METODOS,
    es_de_arriba,
)
from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago.tarjeta.pieza import (
    armar_tarjeta,
)
from src.config import config


class SelectorMetodoPago(QWidget):
    metodo_seleccionado = pyqtSignal(str)

    def __init__(self, parent=None, ancho=280, alto=220, separacion=20):
        super().__init__(parent)
        self.btns = {}
        self.metodos = list(METODOS)
        self._ancho = ancho
        self._alto = alto

        caja = QVBoxLayout(self)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.fila_arriba = QHBoxLayout()
        self.fila_arriba.setSpacing(separacion)
        self.fila_arriba.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fila_abajo = QHBoxLayout()
        self.fila_abajo.setSpacing(separacion)
        self.fila_abajo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caja.addLayout(self.fila_arriba)
        caja.addSpacing(separacion)
        caja.addLayout(self.fila_abajo)

        self._armar()

    def _armar(self):
        oscuro = config.get("theme", "light") == "dark"
        for indice, (icono, texto, clave) in enumerate(self.metodos):
            pieza = armar_tarjeta(
                icono, texto, clave, oscuro, self.metodo_seleccionado.emit,
                self._ancho, self._alto,
            )
            self.btns[clave] = pieza
            fila = self.fila_arriba if es_de_arriba(indice) else self.fila_abajo
            fila.addWidget(pieza["frame"])

    def get_botones(self):
        return self.btns
