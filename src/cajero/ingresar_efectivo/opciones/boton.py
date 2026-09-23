"""Una de las tres opciones: Cambio, Fiado u Otros."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout


def boton_opcion(icono, titulo, color):
    btn = QPushButton()
    btn.setFixedHeight(80)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setCheckable(True)
    btn.setAutoExclusive(True)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: white; border: 2px solid #e2e8f0; border-radius: 12px; text-align: center;
        }}
        QPushButton:hover {{ border-color: {color}; background: #f8fafc; }}
        QPushButton:checked {{ border-color: {color}; background: {color}; color: white; }}
    """)

    caja = QVBoxLayout(btn)
    caja.setAlignment(Qt.AlignmentFlag.AlignCenter)
    dibujo = QLabel(icono)
    dibujo.setStyleSheet("font-size: 24px; border: none; background: transparent;")
    dibujo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    nombre = QLabel(titulo)
    nombre.setStyleSheet("font-weight: 900; font-size: 12px; border: none; background: transparent;")
    nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
    caja.addWidget(dibujo)
    caja.addWidget(nombre)
    return btn
