from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


def armar_cabecera(on_salir):
    header = QFrame()
    header.setFixedHeight(70)
    h_layout = QHBoxLayout(header)
    h_layout.setContentsMargins(30, 0, 30, 0)

    lbl_icon = QLabel()
    lbl_icon.setObjectName("HistorialIcon")
    h_layout.addWidget(lbl_icon)

    lbl_titulo = QLabel("HISTORIAL DE CAJA - TURNO ACTUAL")
    lbl_titulo.setObjectName("HistorialTitle")
    h_layout.addWidget(lbl_titulo)
    h_layout.addStretch()

    btn_close = QPushButton("Salir")
    btn_close.setObjectName("BtnCloseHist")
    btn_close.setFixedWidth(120)
    btn_close.setFixedHeight(40)
    btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_close.clicked.connect(on_salir)
    h_layout.addWidget(btn_close)
    return header
