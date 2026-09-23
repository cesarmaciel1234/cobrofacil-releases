from PyQt6.QtWidgets import QLabel

from src.cajero.paso5_terminal.componentes_paso5_terminal.cabecera_superior.linea import (
    LineaDato,
)


class BloqueEstado(LineaDato):
    """Estado: Cliente. El número de instalación no se muestra."""

    def __init__(self, parent=None):
        super().__init__("Estado:", parent)
        self.etiqueta_estado = self.valor
        self.etiqueta_estado.setObjectName("TerminalCabeceraEstado")
        self.etiqueta_estado.setText("Maestra")
        self.etiqueta_instalacion = QLabel("")
        self.etiqueta_instalacion.setObjectName("TerminalCabeceraInstalacion")
        self.etiqueta_instalacion.hide()
