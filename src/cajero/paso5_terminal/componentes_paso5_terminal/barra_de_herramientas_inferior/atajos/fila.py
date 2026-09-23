from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QScrollArea, QSizePolicy, QWidget

from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.atajos.cobrar import (
    TeclaCobrar,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.atajos.tecla import (
    TeclaAtajo,
)

_TECLAS = (
    ("F1", "Buscar Producto (F1)"),
    ("F3", "Ver Historial del Día (F3)"),
    ("F4", "Cierre de Turno / Caja (F4)"),
    ("F5", "Retiro de Efectivo (F5)"),
    ("F6", "Ingreso de Efectivo (F6)"),
    ("F7", "Leer Báscula (F7)"),
    ("F8", "Ticket en Espera (F8)"),
    ("F11", "Llamar Supervisor (F11)"),
)


class BotonesAtajos(QScrollArea):
    tecla_f_presionada = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("TerminalScrollAtajos")
        self.setStyleSheet(
            "QScrollArea { background: transparent; border: none; } "
            "QWidget#TerminalContenedorAtajos { background: transparent; }"
        )
        self.viewport().setAutoFillBackground(False)
        self.viewport().setStyleSheet("background: transparent;")
        self.setFixedHeight(52)

        self.contenedor_atajos = QWidget()
        self.contenedor_atajos.setObjectName("TerminalContenedorAtajos")
        layout_atajos = QHBoxLayout(self.contenedor_atajos)
        layout_atajos.setSpacing(8)
        layout_atajos.setContentsMargins(0, 0, 0, 0)

        self.botones_f = []
        for texto, tooltip in _TECLAS:
            btn = TeclaAtajo(texto, tooltip)
            btn.clicked.connect(lambda checked, t=texto: self.tecla_f_presionada.emit(t))
            layout_atajos.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)
            self.botones_f.append(btn)

        cobrar = TeclaCobrar()
        cobrar.clicked.connect(lambda: self.tecla_f_presionada.emit("F12"))
        layout_atajos.addWidget(cobrar, 0, Qt.AlignmentFlag.AlignVCenter)
        self.botones_f.append(cobrar)
        self.setWidget(self.contenedor_atajos)
        self.setMinimumWidth(layout_atajos.sizeHint().width())
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
