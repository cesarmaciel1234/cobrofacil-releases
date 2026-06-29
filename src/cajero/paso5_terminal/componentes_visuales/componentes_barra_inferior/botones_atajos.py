from PyQt6.QtWidgets import QScrollArea, QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal

class BotonesAtajos(QScrollArea):
    tecla_f_presionada = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("TerminalScrollAtajos")
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.contenedor_atajos = QWidget()
        self.contenedor_atajos.setObjectName("TerminalContenedorAtajos")
        layout_atajos = QHBoxLayout(self.contenedor_atajos)
        layout_atajos.setSpacing(8)
        layout_atajos.setContentsMargins(0, 0, 0, 0)

        atajos = [
            ("F1", "Buscar Producto (F1)"),
            ("F12", "Cobrar Venta (F12)"),
            ("F3", "Ver Historial del Día (F3)"),
            ("F4", "Cierre de Turno / Caja (F4)"),
            ("F5", "Retiro de Efectivo (F5)"),
            ("F6", "Ingreso de Efectivo (F6)"),
            ("F7", "Leer Báscula (F7)"),
            ("F8", "Ticket en Espera (F8)"),
                        ("F11", "Llamar Supervisor (F11)"),
        ]

        self.botones_f = []
        for texto, tooltip in atajos:
            btn = QPushButton(texto)
            btn.setProperty("is_shortcut", "true")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setFixedSize(45, 40)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, t=texto: self.tecla_f_presionada.emit(t))
            layout_atajos.addWidget(btn)
            self.botones_f.append(btn)

        self.setWidget(self.contenedor_atajos)
