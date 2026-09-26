from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from src.motor_descuentos.compartido.shell_modulo import barra_modulo, QSS_MODULO


class PaginaMayoreo(QWidget):
    """Solo explicación. El precio de mayoreo se carga en Inventario."""

    def __init__(self, on_back, parent=None):
        super().__init__(parent)
        self.setObjectName("ModuloPromoAislado")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(QSS_MODULO)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(barra_modulo("Mayoreo", on_back))
        body = QLabel(
            "Este módulo no comparte pantalla con ofertas ni con el catálogo.\n\n"
            "Mayoreo es global (`MotorMayoreo`):\n"
            "1. Inventario → editar producto (cant. + precio mayoreo), o\n"
            "2. Jefe → Promedios → exportar cortes.\n"
            "3. En caja, al superar esa cantidad, aplica el precio mayoreo."
        )
        body.setWordWrap(True)
        body.setStyleSheet("padding: 32px; font-size: 14px; color: #334155; background: #F8FAFC;")
        body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        root.addWidget(body, 1)
