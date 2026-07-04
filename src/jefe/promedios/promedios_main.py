import sys
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.jefe.vista_promedios import VistaPromediosMixin
from src.jefe.contabilidad.shared_globals import PAL

class PromediosMain(QWidget, VistaPromediosMixin):
    """
    Módulo independiente de Promedios.
    Se accede desde el Dashboard del Jefe.
    """
    request_dashboard = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PromediosMain")
        self.setStyleSheet(f"QWidget#PromediosMain {{ background: {PAL['bg']}; }}")
        
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── NAV BAR ──────────────────────────────────────────────────────────
        self.nav = QFrame()
        self.nav.setObjectName("PromediosNav")
        self.nav.setFixedHeight(64)
        self.nav.setStyleSheet(f"""
            QFrame#PromediosNav {{
                background: {PAL['surface']};
                border-bottom: 1px solid {PAL['border']};
            }}
        """)
        nav_lay = QHBoxLayout(self.nav)
        nav_lay.setContentsMargins(24, 0, 24, 0)
        nav_lay.setSpacing(16)

        # Botón Volver
        btn_back = QPushButton("⬅  Volver al Dashboard")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: {PAL['border']}; color: {PAL['text2']};
                border: none; border-radius: 8px;
                padding: 8px 16px; font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{
                background: {PAL['border2']}; color: {PAL['text']};
            }}
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        nav_lay.addWidget(btn_back)

        # Título
        lbl_title = QLabel("⚖️  Costos y Promedios")
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {PAL['text']};")
        nav_lay.addWidget(lbl_title)
        
        nav_lay.addStretch()

        root.addWidget(self.nav)

        # ── CONTENIDO ─────────────────────────────────────────────────────────
        # Este es el contenedor que usará _build_tab_promedios
        self._content_area = QWidget()
        self._content_lay = QVBoxLayout(self._content_area)
        self._content_lay.setContentsMargins(0, 0, 0, 0)
        
        root.addWidget(self._content_area)
        
        # Iniciar la construcción de la pestaña heredada del mixin
        self._build_tab_promedios()

    def _page(self):
        """
        Método requerido por VistaPromediosMixin para obtener el layout y el scroll
        donde debe inyectar sus widgets.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {PAL['bg']}; border: none; }}")
        inner = QWidget()
        inner.setStyleSheet(f"background: {PAL['bg']};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 24, 28, 28)
        lay.setSpacing(20)
        scroll.setWidget(inner)
        
        # Añadir el scroll al área de contenido de esta ventana
        self._content_lay.addWidget(scroll)
        
        return lay, scroll

    def cargar_datos(self):
        """Método llamado por el main_window al abrir esta pantalla."""
        pass
