from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

QSS_MODULO = """
QWidget#ModuloPromoAislado {
    background: #F8FAFC;
    font-family: 'Segoe UI', sans-serif;
    color: #0F172A;
}
QWidget#ModuloPromoAislado QLabel { color: #0F172A; }
QWidget#ModuloPromoAislado QLineEdit,
QWidget#ModuloPromoAislado QComboBox,
QWidget#ModuloPromoAislado QDoubleSpinBox,
QWidget#ModuloPromoAislado QSpinBox {
    background: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 10px;
}
QWidget#ModuloPromoAislado QListWidget,
QWidget#ModuloPromoAislado QTableWidget {
    background: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
}
"""


def barra_modulo(titulo, on_back):
    bar = QFrame()
    bar.setFixedHeight(72)
    bar.setStyleSheet("QFrame { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }")
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(20, 0, 20, 0)
    btn = QPushButton("← Módulos")
    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    btn.setStyleSheet(
        "QPushButton { background: #FFFFFF; color: #1E293B; font-weight: 700; border: 1px solid #CBD5E1;"
        " border-radius: 8px; padding: 10px 16px; }"
        "QPushButton:hover { background: #F1F5F9; }"
    )
    btn.clicked.connect(on_back)
    tit = QLabel(titulo)
    tit.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A; background: transparent;")
    lay.addWidget(btn)
    lay.addSpacing(16)
    lay.addWidget(tit)
    lay.addStretch()
    return bar


def envolver_modulo(titulo, cuerpo, on_back):
    page = QWidget()
    page.setObjectName("ModuloPromoAislado")
    page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    page.setStyleSheet(QSS_MODULO)
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)
    lay.addWidget(barra_modulo(titulo, on_back))
    lay.addWidget(cuerpo, 1)
    return page
