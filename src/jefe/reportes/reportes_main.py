import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QStackedWidget, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

class ReportesMain(QWidget):
    request_dashboard = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Top Bar for Navigation
        top_bar = QWidget()
        top_bar.setFixedHeight(55)
        top_bar.setStyleSheet("background-color: rgba(255, 255, 255, 0.85); border-bottom: 1px solid #E2E8F0;")
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(20, 0, 20, 0)
        top_lay.setSpacing(15)

        self.btn_volver = QPushButton("← VOLVER")
        self.btn_volver.setCursor(Qt.PointingHandCursor)
        self.btn_volver.clicked.connect(self.request_dashboard.emit)
        top_lay.addWidget(self.btn_volver)
        top_lay.addSpacing(15)

        self.btn_ventas = QPushButton("📉 REPORTE FINANCIERO")
        self.btn_auditoria = QPushButton("🔍 AUDITORÍA DE VENTAS")
        self.btn_historial = QPushButton("🕰️ HISTORIAL")

        # Styling
        btn_style = """
            QPushButton {
                background: transparent;
                font-weight: 700;
                border-radius: 12px;
                padding: 8px 18px;
                font-size: 12px;
                border: none;
                color: #1E293B;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """
        for btn in [self.btn_volver, self.btn_ventas, self.btn_auditoria, self.btn_historial]:
            btn.setStyleSheet(btn_style)
            top_lay.addWidget(btn)
        
        top_lay.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_lay.addWidget(top_bar)

        # Stacked Widget
        self.stack_views = QStackedWidget()
        main_lay.addWidget(self.stack_views)

        # Load Modules
        self.setup_ventas_ui()
        self.setup_audit_ui()
        self.setup_historial_ui()

        # Connections
        self.btn_ventas.clicked.connect(self._show_ventas_tab)
        self.btn_auditoria.clicked.connect(self._show_auditoria_tab)
        self.btn_historial.clicked.connect(self._show_historial_tab)

        self._show_ventas_tab()

    def _show_ventas_tab(self):
        self.stack_views.setCurrentIndex(0)
        self._update_tab_buttons()

    def _show_auditoria_tab(self):
        self.stack_views.setCurrentIndex(1)
        self._update_tab_buttons()

    def _show_historial_tab(self):
        self.stack_views.setCurrentIndex(2)
        self._update_tab_buttons()

    def _update_tab_buttons(self):
        active_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5);
                color: white;
                font-weight: 800;
                border-radius: 12px;
                padding: 8px 18px;
                font-size: 12px;
                border: none;
            }
        """
        inactive_style = """
            QPushButton {
                background: transparent;
                color: #1E293B;
                font-weight: 700;
                border-radius: 12px;
                padding: 8px 18px;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """
        idx = self.stack_views.currentIndex()
        self.btn_ventas.setStyleSheet(active_style if idx == 0 else inactive_style)
        self.btn_auditoria.setStyleSheet(active_style if idx == 1 else inactive_style)
        self.btn_historial.setStyleSheet(active_style if idx == 2 else inactive_style)

    def setup_ventas_ui(self):
        from src.jefe.reportes.vista_financiero import VistaFinanciero
        self.tab_ventas = VistaFinanciero()
        self.stack_views.addWidget(self.tab_ventas)

    def setup_audit_ui(self):
        from src.jefe.reportes.vista_auditoria import VistaAuditoria
        self.tab_auditoria = VistaAuditoria()
        self.stack_views.addWidget(self.tab_auditoria)

    def setup_historial_ui(self):
        from src.jefe.reportes.vista_historial import VistaHistorial
        self.tab_historial = VistaHistorial(self)
        self.stack_views.addWidget(self.tab_historial)