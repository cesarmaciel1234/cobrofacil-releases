"""Una de las tres opciones: Cambio, Fiado u Otros."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout


def boton_opcion(icono, titulo, _color):
    btn = QPushButton()
    btn.setMinimumHeight(280)
    btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton {
            background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 20px;
        }
        QPushButton:hover { border: 2px solid #0F172A; }
    """)

    caja = QVBoxLayout(btn)
    caja.setAlignment(Qt.AlignmentFlag.AlignCenter)
    caja.setContentsMargins(16, 28, 16, 28)
    caja.setSpacing(14)
    dibujo = QLabel(icono)
    dibujo.setStyleSheet("font-size: 56px; border: none; background: transparent;")
    dibujo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    nombre = QLabel(titulo)
    nombre.setStyleSheet(
        "font-weight: 800; font-size: 20px; color: #0F172A; "
        "letter-spacing: 1px; border: none; background: transparent;"
    )
    nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
    caja.addWidget(dibujo)
    caja.addWidget(nombre)
    return btn
