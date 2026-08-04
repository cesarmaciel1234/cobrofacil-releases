"""Sección de configuración — card liviana sin sombras."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout
from PyQt6.QtCore import Qt
from src.admin.configuracion.componentes.config_button import ConfigButton


class ConfigCategory(QWidget):
    def __init__(self, title, items, callback=None, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName("ConfigCategoryCard")
        card.setStyleSheet("""
            QFrame#ConfigCategoryCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 16)
        lay.setSpacing(12)

        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(
            "font-family: 'Segoe UI'; font-size: 12px; font-weight: 800; "
            "color: #64748B; letter-spacing: 1px; background: transparent; border: none;"
        )
        lay.addWidget(lbl_title)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setAlignment(Qt.AlignmentFlag.AlignLeft)

        row, col = 0, 0
        max_cols = 7

        for icon, text in items:
            btn = ConfigButton(icon, text)
            if callback:
                btn.clicked.connect(lambda checked=False, t=text: callback(t))
            grid.addWidget(btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        lay.addLayout(grid)
        root.addWidget(card)
        root.addSpacing(14)
