from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QStackedWidget, QScrollArea, QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from src.motor_descuentos.compartido.tarjeta_modulo import TarjetaModulo
from src.motor_descuentos.compartido.shell_modulo import envolver_modulo, QSS_MODULO


MODULOS = (
    ("ofertas", "🏷️", "Ofertas por producto", "Carga precios promo. No imprime ni toca la TV."),
    ("combos", "🎁", "Combos", "Varios artículos, un precio. Independiente de ofertas."),
    ("publicidad", "📺", "Publicidad TV", "Qué producto se inserta en la cartelería. No cambia precios."),
    ("imprenta", "🖨️", "Imprenta / PDF", "Solo PDF para clientes. Lee ofertas, no las edita."),
    ("mayoreo", "📦", "Mayoreo", "Se carga en Inventario. Acá no se mezcla con promos."),
)


class Admin2Ofertas(QWidget):
    """Hub: un módulo vivo a la vez. Al volver se destruye para no cruzar estado."""
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("HubPromociones")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#HubPromociones { background: #F8FAFC; }" + QSS_MODULO)
        self._modulo_vivo = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        root.addWidget(self.stack)
        self.stack.addWidget(self._armar_hub())

    def _armar_hub(self):
        page = QWidget()
        page.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        nav = QFrame()
        nav.setFixedHeight(72)
        nav.setStyleSheet("QFrame { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }")
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(24, 0, 24, 0)
        back = QPushButton("← Panel admin")
        back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #1E293B; font-weight: 700; border: 1px solid #CBD5E1;"
            " border-radius: 8px; padding: 10px 18px; }"
            "QPushButton:hover { background: #F1F5F9; }"
        )
        back.clicked.connect(self.request_dashboard.emit)
        tit = QLabel("Motor de promociones")
        tit.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A; background: transparent;")
        sub = QLabel("Cada tarjeta es un módulo aparte. No se cruzan.")
        sub.setStyleSheet("font-size: 12px; color: #64748B; background: transparent;")
        col = QVBoxLayout()
        col.setSpacing(0)
        col.addWidget(tit)
        col.addWidget(sub)
        nl.addWidget(back)
        nl.addSpacing(18)
        nl.addLayout(col)
        nl.addStretch()
        lay.addWidget(nav)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #F8FAFC; }")
        wrap = QWidget()
        wrap.setStyleSheet("background: #F8FAFC;")
        grid = QGridLayout(wrap)
        grid.setContentsMargins(28, 28, 28, 28)
        grid.setSpacing(16)
        for i, (codigo, ico, titulo, subtitulo) in enumerate(MODULOS):
            card = TarjetaModulo(codigo, ico, titulo, subtitulo)
            card.clicked.connect(lambda c=codigo: self._abrir(c))
            grid.addWidget(card, i // 3, i % 3)
        grid.setRowStretch(2, 1)
        scroll.setWidget(wrap)
        lay.addWidget(scroll, 1)
        return page

    def _cerrar_modulo(self):
        w = self._modulo_vivo
        self._modulo_vivo = None
        if w is None:
            return
        self.stack.removeWidget(w)
        w.deleteLater()
        self.stack.setCurrentIndex(0)

    def _ir_hub(self):
        self._cerrar_modulo()

    def _abrir(self, codigo):
        self._cerrar_modulo()
        w = self._crear_pagina(codigo)
        self._modulo_vivo = w
        self.stack.addWidget(w)
        self.stack.setCurrentWidget(w)

    def _crear_pagina(self, codigo):
        if codigo == "ofertas":
            from src.motor_descuentos.ofertas.vista import TallerOfertas
            w = TallerOfertas()
            w.setObjectName("ModuloPromoAislado")
            w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            w.request_back.connect(self._ir_hub)
            return w
        if codigo == "combos":
            from src.motor_descuentos.combos.vista import DialogoCombos
            return envolver_modulo("Combos", DialogoCombos(), self._ir_hub)
        if codigo == "publicidad":
            from src.motor_descuentos.publicidad.vista import DialogGestorPublicidad
            return envolver_modulo("Publicidad TV", DialogGestorPublicidad(), self._ir_hub)
        if codigo == "imprenta":
            from src.motor_descuentos.imprenta.vista import PaginaImprenta
            return PaginaImprenta(self._ir_hub)
        if codigo == "mayoreo":
            from src.motor_descuentos.mayoreo.vista import PaginaMayoreo
            return PaginaMayoreo(self._ir_hub)
        return QWidget()
