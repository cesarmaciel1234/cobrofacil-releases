from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class AvisoCierreAutomatico(QDialog):
    """Aviso de cierre de días anteriores. Grande, sobre el lanzador."""

    def __init__(self, monto, parent=None):
        super().__init__(parent)
        self._monto = float(monto or 0)
        self.setWindowTitle("Sistema de seguridad")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(760, 520)
        self.setModal(True)
        self._armar()

    def _armar(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(28, 28, 28, 28)

        self.tarjeta = QFrame()
        self.tarjeta.setObjectName("AvisoCierreTarjeta")
        self.tarjeta.setStyleSheet(
            "QFrame#AvisoCierreTarjeta {"
            "background: #FFFFFF; border-radius: 28px; border: none;"
            "}"
        )
        raiz.addWidget(self.tarjeta)

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(36)
        sombra.setOffset(0, 16)
        sombra.setColor(QColor(15, 23, 42, 48))
        self.tarjeta.setGraphicsEffect(sombra)

        lay = QVBoxLayout(self.tarjeta)
        lay.setContentsMargins(56, 44, 56, 40)
        lay.setSpacing(0)

        insignia = QLabel("i")
        insignia.setFixedSize(72, 72)
        insignia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        insignia.setStyleSheet(
            "background: #E0F2FE; color: #0369A1; border-radius: 36px;"
            "font-size: 34px; font-weight: 800; font-family: 'Segoe UI';"
        )
        lay.addWidget(insignia, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(22)

        kicker = QLabel("SISTEMA DE SEGURIDAD")
        kicker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kicker.setStyleSheet(
            "color: #0369A1; font-size: 13px; font-weight: 800;"
            "letter-spacing: 3px; background: transparent; border: none;"
            "font-family: 'Segoe UI';"
        )
        lay.addWidget(kicker)
        lay.addSpacing(10)

        titulo = QLabel("Ventas abiertas de días anteriores")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setWordWrap(True)
        titulo.setStyleSheet(
            "color: #0F172A; font-size: 28px; font-weight: 800;"
            "background: transparent; border: none; font-family: 'Segoe UI';"
        )
        lay.addWidget(titulo)
        lay.addSpacing(12)

        cuerpo = QLabel("El sistema ya cerró ese turno para que la caja de hoy empiece limpia.")
        cuerpo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cuerpo.setWordWrap(True)
        cuerpo.setStyleSheet(
            "color: #64748B; font-size: 18px; font-weight: 600;"
            "background: transparent; border: none; font-family: 'Segoe UI';"
        )
        lay.addWidget(cuerpo)
        lay.addSpacing(28)

        monto = QLabel(f"${self._monto:,.2f}")
        monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        monto.setStyleSheet(
            "color: #0F172A; font-size: 52px; font-weight: 800;"
            "background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 18px;"
            "padding: 18px 24px; font-family: 'Segoe UI';"
        )
        lay.addWidget(monto)
        lay.addSpacing(8)

        pie_monto = QLabel("CIERRE AUTOMÁTICO")
        pie_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pie_monto.setStyleSheet(
            "color: #94A3B8; font-size: 12px; font-weight: 800;"
            "letter-spacing: 2px; background: transparent; border: none;"
            "font-family: 'Segoe UI';"
        )
        lay.addWidget(pie_monto)
        lay.addStretch(1)
        lay.addSpacing(20)

        ok = QPushButton("OK")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.setFixedHeight(64)
        ok.setDefault(True)
        ok.setStyleSheet(
            "QPushButton {"
            "background: #0F172A; color: #FFFFFF; border: none; border-radius: 16px;"
            "font-size: 18px; font-weight: 800; letter-spacing: 1px;"
            "font-family: 'Segoe UI';"
            "}"
            "QPushButton:hover { background: #1E293B; }"
            "QPushButton:pressed { background: #020617; }"
        )
        ok.clicked.connect(self.accept)
        lay.addWidget(ok)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
            self.accept()
            return
        super().keyPressEvent(event)
