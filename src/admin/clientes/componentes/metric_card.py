"""KPI de la cartera. Clicable: la pantalla decide qué filtro o diálogo abrir."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from src.admin.clientes.theme import _CLI
from src.utils.letra import QSS_KPI, QSS_ROTULO


class MetricCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, titulo, icon="", color="#3B82F6", hint="", parent=None):
        super().__init__(parent)
        self._color = color
        self._activo = False
        self.setFixedHeight(118)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(hint or "Clic para filtrar o abrir")
        self._aplicar_estilo(False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(14)

        if icon:
            icon_frame = QFrame()
            icon_frame.setFixedSize(52, 52)
            icon_frame.setStyleSheet(
                f"background: {color}18; border-radius: 14px; border: none;"
            )
            i_lay = QVBoxLayout(icon_frame)
            i_lay.setContentsMargins(0, 0, 0, 0)
            icon_lbl = QLabel(icon)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet(
                f"font-size: 24px; color: {color}; background: transparent; border: none;"
            )
            i_lay.addWidget(icon_lbl)
            lay.addWidget(icon_frame)

        v_lay = QVBoxLayout()
        v_lay.setSpacing(2)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_tit = QLabel(titulo.upper())
        self.lbl_tit.setStyleSheet(
            f"{QSS_ROTULO} color: {_CLI['text_sec']}; border: none;"
        )
        v_lay.addWidget(self.lbl_tit)

        self.lbl_val = QLabel("0")
        self.lbl_val.setStyleSheet(
            f"{QSS_KPI} color: {color}; border: none; font-size: 22px;"
        )
        v_lay.addWidget(self.lbl_val)

        self.lbl_sub = QLabel("")
        self.lbl_sub.setStyleSheet(
            f"color: {_CLI['text_sec']}; font-size: 11px; font-weight: 700; border: none;"
        )
        self.lbl_sub.hide()
        v_lay.addWidget(self.lbl_sub)

        lay.addLayout(v_lay, 1)

    def _aplicar_estilo(self, hover: bool):
        borde = self._color if (hover or self._activo) else _CLI["border"]
        fondo = "#FFFFFF" if not self._activo else f"{self._color}10"
        self.setStyleSheet(
            f"QFrame {{ background: {fondo}; border: 1px solid {borde}; "
            f"border-left: 5px solid {self._color}; border-radius: 16px; }}"
        )

    def set_activo(self, activo: bool):
        self._activo = bool(activo)
        self._aplicar_estilo(False)

    def enterEvent(self, event):
        self._aplicar_estilo(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._aplicar_estilo(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_valor(self, val, is_money=False, subtitulo=""):
        if is_money:
            self.lbl_val.setText(f"${float(val or 0):,.2f}")
        else:
            self.lbl_val.setText(str(val))
        if subtitulo:
            self.lbl_sub.setText(subtitulo)
            self.lbl_sub.show()
        else:
            self.lbl_sub.hide()
