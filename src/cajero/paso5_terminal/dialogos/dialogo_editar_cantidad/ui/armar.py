from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QDoubleSpinBox, QPushButton,
)
from PyQt6.QtCore import Qt

from src.cajero.paso5_terminal.dialogos.dialogo_editar_cantidad.ui.estilos import ESTILO_DIALOGO


def armar_cuerpo(dialogo, cant_actual, nombre):
    dialogo.setStyleSheet(ESTILO_DIALOGO)

    outer = QVBoxLayout(dialogo)
    outer.setContentsMargins(0, 0, 0, 0)

    box = QFrame()
    box.setObjectName("EditCantDialog")
    outer.addWidget(box)

    layout = QVBoxLayout(box)
    layout.setContentsMargins(40, 36, 40, 36)
    layout.setSpacing(20)

    lbl_prod = QLabel(f"MODIFICAR: {str(nombre or '').upper()}")
    lbl_prod.setObjectName("EditCantProducto")
    lbl_prod.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(lbl_prod)

    lbl_title = QLabel("CANTIDAD")
    lbl_title.setObjectName("EditCantTitle")
    lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(lbl_title)

    spin = QDoubleSpinBox()
    spin.setRange(0.001, 9999.999)
    spin.setDecimals(3)
    spin.setValue(cant_actual)
    spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
    spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    layout.addWidget(spin)

    btns = QHBoxLayout()
    btns.setSpacing(12)
    btn_ok = QPushButton("CONFIRMAR (ENTER)")
    btn_ok.setObjectName("EditCantOk")
    btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_ok.clicked.connect(dialogo.accept)

    btn_cancel = QPushButton("CANCELAR (ESC)")
    btn_cancel.setObjectName("EditCantCancel")
    btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_cancel.clicked.connect(dialogo.reject)

    btns.addWidget(btn_ok, 1)
    btns.addWidget(btn_cancel, 1)
    layout.addLayout(btns)
    return spin
