from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal, Qt

_ACENTOS = {
    "catalogo": "#2563EB",
    "excel": "#0F766E",
    "deptos": "#7C3AED",
    "iva": "#D97706",
    "pdf": "#DB2777",
    "importar": "#2563EB",
    "exportar": "#0F766E",
    "nube": "#7C3AED",
    "unificar": "#C2410C",
    "ofertas": "#2563EB",
    "combos": "#DB2777",
    "publicidad": "#7C3AED",
    "imprenta": "#0F766E",
    "mayoreo": "#D97706",
    "general": "#2563EB",
    "pers": "#DB2777",
    "disp": "#0F766E",
    "serv": "#7C3AED",
    "mant": "#D97706",
}


class TarjetaModulo(QFrame):
    clicked = pyqtSignal()

    def __init__(self, codigo, icono, titulo, subtitulo, parent=None):
        super().__init__(parent)
        self.codigo = codigo
        accent = _ACENTOS.get(codigo, "#2563EB")
        self.setObjectName("TarjetaModuloPromo")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(292, 178)
        self.setStyleSheet(f"""
            QFrame#TarjetaModuloPromo {{
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-left: 5px solid {accent};
                border-radius: 14px;
            }}
            QFrame#TarjetaModuloPromo:hover {{
                background: #F8FAFC;
                border: 1px solid {accent};
                border-left: 5px solid {accent};
            }}
            QFrame#TarjetaModuloPromo QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(8)

        badge = QLabel(icono)
        badge.setFixedSize(44, 44)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"font-size: 22px; background: {accent}22; border-radius: 12px; border: none;"
        )
        tit = QLabel(titulo)
        tit.setWordWrap(True)
        tit.setStyleSheet(
            "font-size: 16px; font-weight: 800; color: #0F172A; background: transparent; border: none;"
        )
        sub = QLabel(subtitulo)
        sub.setWordWrap(True)
        sub.setStyleSheet(
            "font-size: 12px; color: #64748B; background: transparent; border: none;"
        )
        for w in (badge, tit, sub):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        top = QHBoxLayout()
        top.addWidget(badge)
        top.addStretch()
        lay.addLayout(top)
        lay.addWidget(tit)
        lay.addWidget(sub)
        lay.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self.clicked.emit()
        super().mousePressEvent(event)
