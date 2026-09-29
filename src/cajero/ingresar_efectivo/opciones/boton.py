"""Una de las tres opciones: Cambio, Fiado u Otros."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QKeyEvent
from PyQt6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout


class _TarjetaOpcion(QPushButton):
    def focusInEvent(self, event):
        self._marcar(event.reason() != Qt.FocusReason.MouseFocusReason)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._marcar(False)
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (
            Qt.Key.Key_Left,
            Qt.Key.Key_Up,
            Qt.Key.Key_Right,
            Qt.Key.Key_Down,
        ) and self._opciones:
            paso = -1 if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up) else 1
            siguiente = (self._opciones.index(self) + paso) % len(self._opciones)
            self._marcar(False)
            destino = self._opciones[siguiente]
            destino._marcar(True)
            destino.setFocus(Qt.FocusReason.TabFocusReason)
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self._marcar(True)
        super().keyPressEvent(event)

    def establecer_opciones(self, opciones):
        self._opciones = tuple(opciones)

    def _marcar(self, marcada):
        if self.property("resaltada") == marcada:
            return
        self.setProperty("resaltada", marcada)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


def boton_opcion(icono, titulo, color, descripcion):
    btn = _TarjetaOpcion()
    btn._opciones = ()
    btn.setMinimumHeight(280)
    btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    btn.setAccessibleName(titulo.title())
    btn.setAccessibleDescription(descripcion)
    btn.setProperty("resaltada", False)
    acento = QColor(color)
    fondo_icono = acento.lighter(178).name()
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #FFFFFF;
            border: 1px solid #DCE4EF;
            border-radius: 20px;
        }}
        QPushButton[resaltada="true"] {{
            background-color: {acento.lighter(178).name()};
            border: 4px solid {color};
        }}
        QPushButton:pressed {{
            background-color: {acento.lighter(165).name()};
        }}
        QPushButton[resaltada="true"] QLabel#OpcionIcono {{
            background: {color};
            border: 2px solid {color};
        }}
        QPushButton[resaltada="true"] QLabel#OpcionTitulo {{
            color: {color};
        }}
    """)

    caja = QVBoxLayout(btn)
    caja.setAlignment(Qt.AlignmentFlag.AlignCenter)
    caja.setContentsMargins(18, 24, 18, 24)
    caja.setSpacing(16)
    dibujo = QLabel(icono)
    dibujo.setObjectName("OpcionIcono")
    dibujo.setFixedSize(82, 82)
    dibujo.setStyleSheet(
        f"font-size: 42px; border: 1px solid {acento.lighter(155).name()}; "
        f"border-radius: 41px; background: {fondo_icono};"
    )
    dibujo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    nombre = QLabel(titulo)
    nombre.setObjectName("OpcionTitulo")
    nombre.setStyleSheet(
        f"font-weight: 900; font-size: 21px; color: {color}; "
        "letter-spacing: 1px; border: none; background: transparent;"
    )
    nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ayuda = QLabel(descripcion)
    ayuda.setWordWrap(True)
    ayuda.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ayuda.setStyleSheet(
        "font-size: 13px; font-weight: 500; color: #64748B; "
        "border: none; background: transparent;"
    )
    caja.addWidget(dibujo)
    caja.addWidget(nombre)
    caja.addWidget(ayuda)
    return btn
