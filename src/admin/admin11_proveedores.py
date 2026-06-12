"""
admin11_proveedores.py — Gestión de Compras y Proveedores (Admin)
Módulo Unificado
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from src.utils.theme_manager import theme_manager
from src.vistas.proveedores import ModuloProveedoresUnificado

class Admin11Proveedores(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── NAVBAR ───────────────────────────────────────────────────────────
        nav = QFrame()
        nav.setObjectName("ProvNav")
        nav.setFixedHeight(60)
        nav.setStyleSheet(f"""
            QFrame#ProvNav {{
                background: {theme_manager.get_color('nav_bg')};
                border-bottom: 1px solid {theme_manager.get_color('nav_border')};
            }}
        """)
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(24, 0, 24, 0)
        nl.setSpacing(14)

        btn_back = QPushButton("← Volver")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setFixedHeight(34)
        btn_back.setStyleSheet("""
            QPushButton {
                background: #F8FAFC; color: #475569;
                border: 1px solid #E2E8F0; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background: #CBD5E1; color: #0F172A; }
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        nl.addWidget(btn_back)

        sep = QFrame(); sep.setFixedSize(1, 28)
        sep.setStyleSheet("background: #E2E8F0;")
        nl.addWidget(sep)

        lbl_title = QLabel("🚚  Compras y Proveedores (Carga Rápida)")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 900; color: #0F172A; background: transparent; border: none;")
        nl.addWidget(lbl_title)
        nl.addStretch()
        
        root.addWidget(nav)

        # ── MÓDULO UNIFICADO ───────────────────────────────────────────────────
        self.modulo_unificado = ModuloProveedoresUnificado(perfil="admin", db_jefe=None)
        
        # Le damos un layout con márgenes a la vista unificada
        content_area = QWidget()
        content_area.setStyleSheet("background: #F8FAFC;")
        c_lay = QVBoxLayout(content_area)
        c_lay.setContentsMargins(30, 30, 30, 30)
        c_lay.addWidget(self.modulo_unificado)
        
        root.addWidget(content_area)
