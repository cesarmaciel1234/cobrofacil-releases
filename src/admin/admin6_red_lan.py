"""Panel dedicado de red LAN / multicaja."""

from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor

from src.config import config
from src.base_de_datos.database import db_manager
from src.navigation.screen_indices import Screen


class Admin6RedLan(QWidget):
    request_dashboard = pyqtSignal()
    request_screen = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background: #F8FAFC; border-bottom: 1px solid #E2E8F0;")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 16, 24, 16)

        btn_back = QPushButton("← Dashboard")
        btn_back.setCursor(QCursor(Qt.PointingHandCursor))
        btn_back.setStyleSheet(
            "QPushButton { background: white; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 8px 16px; font-weight: 600; }"
            "QPushButton:hover { background: #F1F5F9; }"
        )
        btn_back.clicked.connect(self.request_dashboard.emit)
        h.addWidget(btn_back)

        title = QLabel("🌐 Servidor LAN / Multicaja")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0F172A; border: none;")
        h.addWidget(title)
        h.addStretch()
        root.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F1F5F9; border: none; }")

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(32, 24, 32, 32)
        lay.setSpacing(16)

        is_master = getattr(db_manager, "is_master", True)
        caja_id = config.get("caja_id", 1)
        db_engine = getattr(db_manager, "db_engine_type", "sqlite")
        db_host = config.get("db_host", "") or "localhost"
        modo = "PC MAESTRA (servidor)" if is_master else "PC ESCLAVA (terminal LAN)"

        status = QFrame()
        status.setStyleSheet(
            "QFrame { background: white; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        s_lay = QVBoxLayout(status)
        s_lay.setContentsMargins(20, 20, 20, 20)
        s_lay.setSpacing(8)

        for line in (
            f"Modo actual: {modo}",
            f"Motor de datos: {db_engine.upper()}",
            f"Host de red: {db_host}",
            f"ID de caja local: {caja_id}",
            "API de ventas LAN: http://127.0.0.1:8000/api/guardar_venta",
            "Descubrimiento UDP: puerto 37020",
        ):
            lbl = QLabel(line)
            lbl.setStyleSheet("font-size: 14px; color: #334155; border: none;")
            s_lay.addWidget(lbl)

        lay.addWidget(status)

        hint = QLabel(
            "Desde aquí administrás la identificación de cajas y la contraseña "
            "que usan las terminales secundarias para conectarse por red."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 13px; color: #64748B; border: none;")
        lay.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_cajas = QPushButton("📟 Administrar cajas")
        btn_cajas.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cajas.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: bold; "
            "padding: 12px 20px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_cajas.clicked.connect(self._open_administrar_cajas)
        btn_row.addWidget(btn_cajas)

        btn_pin = QPushButton("🔑 Contraseña PC esclava")
        btn_pin.setCursor(QCursor(Qt.PointingHandCursor))
        btn_pin.setStyleSheet(
            "QPushButton { background: #0D9488; color: white; font-weight: bold; "
            "padding: 12px 20px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #0F766E; }"
        )
        btn_pin.clicked.connect(self._open_pin_esclava)
        btn_row.addWidget(btn_pin)

        btn_cfg = QPushButton("⚙️ Configuración completa")
        btn_cfg.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cfg.setStyleSheet(
            "QPushButton { background: white; color: #334155; font-weight: 600; "
            "padding: 12px 20px; border-radius: 8px; border: 1px solid #CBD5E1; }"
            "QPushButton:hover { background: #F8FAFC; }"
        )
        btn_cfg.clicked.connect(lambda: self.request_screen.emit(Screen.CONFIGURACION))
        btn_row.addWidget(btn_cfg)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        lay.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

    def _open_administrar_cajas(self):
        from src.admin.admin5_configuracion import DialogoAdministrarCajas
        qt_exec(DialogoAdministrarCajas(self))

    def _open_pin_esclava(self):
        from src.admin.admin5_configuracion import DialogoPINLocal
        qt_exec(DialogoPINLocal(self))