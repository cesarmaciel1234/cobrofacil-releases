from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget


class BloqueEstado(QWidget):
    """Una línea: Estado: Cliente. El número de instalación no se muestra."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        prefijo = QLabel("Estado:")
        prefijo.setObjectName("TerminalCabeceraPrefijo")
        prefijo.setMinimumWidth(78)
        self.etiqueta_estado = QLabel("Maestra")
        self.etiqueta_estado.setObjectName("TerminalCabeceraEstado")
        self.etiqueta_instalacion = QLabel("")
        self.etiqueta_instalacion.setObjectName("TerminalCabeceraInstalacion")
        self.etiqueta_instalacion.hide()
        lay.addWidget(prefijo)
        lay.addWidget(self.etiqueta_estado)
        lay.addStretch()
