# -*- coding: utf-8 -*-
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)


class HojaSuelta(QMainWindow):
    cerrado = pyqtSignal(int)

    def __init__(self, index: int, titulo: str, modulo: QWidget, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self._index = int(index)
        self._modulo = modulo
        self._aviso = False
        self.setWindowTitle(f"{titulo} · Admin")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        cuerpo = QWidget()
        cuerpo.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(cuerpo)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        barra = QWidget()
        barra.setFixedHeight(44)
        barra.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        b = QHBoxLayout(barra)
        b.setContentsMargins(16, 0, 12, 0)
        nom = QLabel(titulo)
        nom.setStyleSheet("color: #0F172A; font-size: 15px; font-weight: 800; background: transparent;")
        b.addWidget(nom)
        b.addStretch()
        traer = QPushButton("Traer al hub")
        traer.setCursor(Qt.CursorShape.PointingHandCursor)
        traer.setFixedHeight(32)
        traer.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 0 12px; font-size: 12px; font-weight: 700; }"
            "QPushButton:hover { background: #E2E8F0; }"
        )
        traer.clicked.connect(self.close)
        b.addWidget(traer)
        lay.addWidget(barra)

        modulo.setParent(None)
        modulo.setVisible(True)
        modulo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lay.addWidget(modulo, 1)
        modulo.show()
        self.setCentralWidget(cuerpo)

    def closeEvent(self, event):
        if not self._aviso:
            self._aviso = True
            self.cerrado.emit(self._index)
        super().closeEvent(event)
