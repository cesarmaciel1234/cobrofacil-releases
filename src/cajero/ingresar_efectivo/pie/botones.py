"""Cancelar y confirmar. No decide el monto."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QPushButton


def fila_pie(al_cancelar, al_confirmar):
    fila = QHBoxLayout()
    fila.setSpacing(14)

    cancelar = QPushButton("  ESC  Cancelar")
    cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
    cancelar.setStyleSheet(
        "QPushButton { background: #FEE2E2; color: #DC2626; font-weight: 800; "
        "font-size: 14px; padding: 14px; border-radius: 12px; border: none; }"
        "QPushButton:hover { background: #FCA5A5; color: #991B1B; }"
    )
    cancelar.clicked.connect(al_cancelar)

    confirmar = QPushButton("✅ CONFIRMAR")
    confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
    confirmar.setStyleSheet(
        "QPushButton { background: #3B82F6; color: white; font-weight: 900; font-size: 14px; "
        "padding: 14px; border-radius: 12px; border: none; letter-spacing: 1px; }"
        "QPushButton:hover { background: #2563EB; }"
    )
    confirmar.clicked.connect(al_confirmar)

    fila.addWidget(cancelar, 1)
    fila.addWidget(confirmar, 1)
    return fila
