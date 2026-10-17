"""Tarjeta de galería: casillero, miniatura, borrar."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QToolButton

from src.carteleria.creador_png.panel_vitrina.galeria.thumbs import pixmap_rapido


class TarjetaPng(QFrame):
    elegida = pyqtSignal(str)
    borrar = pyqtSignal(str)

    def __init__(self, filename: str, fpath: str, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.fpath = fpath
        self.setObjectName("TarjetaPng")
        self.setFixedSize(148, 176)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._marcar(False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 8)
        lay.setSpacing(4)

        top = QHBoxLayout()
        self.chk = QCheckBox()
        self.chk.setToolTip("Marcar para borrar varios")
        self.chk.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del = QToolButton()
        btn_del.setText("✕")
        btn_del.setToolTip("Eliminar este PNG")
        btn_del.setFixedSize(22, 22)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet(
            "QToolButton { background: #FEE2E2; color: #B91C1C; border: none; "
            "border-radius: 6px; font-weight: 800; font-size: 11px; }"
            "QToolButton:hover { background: #FECACA; }"
        )
        btn_del.clicked.connect(lambda: self.borrar.emit(self.filename))
        top.addWidget(self.chk)
        top.addStretch()
        top.addWidget(btn_del)
        lay.addLayout(top)

        self.lbl_img = QLabel("…")
        self.lbl_img.setFixedSize(128, 112)
        self.lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_img.setStyleSheet("background: #F1F5F9; border-radius: 8px; color: #94A3B8;")
        lay.addWidget(self.lbl_img, 0, Qt.AlignmentFlag.AlignCenter)

        nombre = filename.rsplit(".", 1)[0].replace("_", " ")
        self.lbl_nom = QLabel(nombre)
        self.lbl_nom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nom.setWordWrap(True)
        self.lbl_nom.setStyleSheet("font-size: 11px; font-weight: 700; color: #334155;")
        lay.addWidget(self.lbl_nom)

        self.setToolTip(filename)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.elegida.emit(self.filename)
        super().mousePressEvent(event)

    def pintar_thumb(self):
        pm = pixmap_rapido(self.fpath, 112)
        if pm.isNull():
            self.lbl_img.setText("—")
            return
        self.lbl_img.setPixmap(pm)
        self.lbl_img.setText("")

    def _marcar(self, on: bool):
        if on:
            self.setStyleSheet(
                "QFrame#TarjetaPng { background: #EFF6FF; border: 2px solid #2563EB; border-radius: 12px; }"
            )
        else:
            self.setStyleSheet(
                "QFrame#TarjetaPng { background: #F8FAFC; border: 2px solid #E2E8F0; border-radius: 12px; }"
                "QFrame#TarjetaPng:hover { border-color: #93C5FD; }"
            )

    def set_elegida(self, on: bool):
        self._marcar(on)
