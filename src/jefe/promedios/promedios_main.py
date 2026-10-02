# -*- coding: utf-8 -*-
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from src.contabilidad.shared_globals import PAL

from .carne.ui_carne import UICarne
from .cerdo.ui_cerdo import UICerdo
from .pollo.ui_pollo import UIPollo

from src.base_de_datos.database import DatabaseManager
from src.jefe.promedios.motor_global_promedios import MotorPromedios
import hashlib

class PromediosMain(QWidget):
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

        nav = QFrame()
        nav.setFixedHeight(64)
        nav.setStyleSheet(f"background: {PAL['surface']}; border-bottom: 1px solid {PAL['border']};")
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(24, 0, 24, 0)
        
        btn_back = QPushButton("  Volver al Dashboard")
        btn_back.clicked.connect(self.request_dashboard.emit)
        btn_back.setStyleSheet(f"background: {PAL['border']}; border-radius: 8px; padding: 8px 16px; font-weight: bold;")
        
        lbl_title = QLabel(" Costos y Promedios")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        nav_lay.addWidget(btn_back)
        nav_lay.addWidget(lbl_title)
        nav_lay.addStretch()
        root.addWidget(nav)

        tabs_lay = QHBoxLayout()
        tabs_lay.setContentsMargins(28, 24, 28, 0)
        
        self.btn_carne = QPushButton("🥩 CARNE")
        self.btn_cerdo = QPushButton("🐖 CERDO")
        self.btn_pollo = QPushButton("🍗 POLLO")
        
        for b in [self.btn_carne, self.btn_cerdo, self.btn_pollo]:
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            tabs_lay.addWidget(b)
        tabs_lay.addStretch()
        
        self.btn_sync = QPushButton("🔄 Sincronizar")
        self.btn_export = QPushButton("💾 Exportar a Inventario")
        self.btn_redondear = QPushButton("Redondear Precios (500)")
        self.btn_pdf_int = QPushButton("📄 PDF Interno")
        self.btn_pdf_ext = QPushButton("📄 PDF Público")
        
        for b in [self.btn_sync, self.btn_export, self.btn_redondear, self.btn_pdf_int, self.btn_pdf_ext]:
            b.setStyleSheet(f"background: {PAL['primary']}; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold;")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            tabs_lay.addWidget(b)
        self.btn_redondear.setStyleSheet(f"background: {PAL['warning']}; color: #0F172A; border-radius: 8px; padding: 8px 16px; font-weight: bold;")
        self.btn_sync.setStyleSheet(f"background: {PAL['success']}; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold;")
        
        # Connect Actions
        self.btn_redondear.clicked.connect(lambda: self.stack.currentWidget().redondear())
        self.btn_sync.clicked.connect(self._action_sincronizar)
        self.btn_export.clicked.connect(self._action_exportar)
        self.btn_pdf_int.clicked.connect(self._action_pdf_interno)
        self.btn_pdf_ext.clicked.connect(self._action_pdf_clientes)

        root.addLayout(tabs_lay)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self.stack = QStackedWidget()
        self.ui_carne = UICarne()
        self.ui_cerdo = UICerdo()
        self.ui_pollo = UIPollo()
        
        self.stack.addWidget(self.ui_carne)
        self.stack.addWidget(self.ui_cerdo)
        self.stack.addWidget(self.ui_pollo)
        
        scroll.setWidget(self.stack)
        
        lay_content = QVBoxLayout()
        lay_content.setContentsMargins(28, 24, 28, 28)
        lay_content.addWidget(scroll)
        
        root.addLayout(lay_content)

        self.btn_carne.clicked.connect(lambda: self._switch_tab(0))
        self.btn_cerdo.clicked.connect(lambda: self._switch_tab(1))
        self.btn_pollo.clicked.connect(lambda: self._switch_tab(2))
        self._switch_tab(0)

    def _switch_tab(self, idx):
        self.stack.setCurrentIndex(idx)
        active = f"QPushButton {{ background: {PAL['primary']}; color: white; border-radius: 8px; padding: 12px 24px; font-weight: bold; }}"
        inactive = "QPushButton { background: #E2E8F0; color: #0F172A; border: 1px solid #94A3B8; border-radius: 8px; padding: 12px 24px; font-weight: bold; }"
        
        self.btn_carne.setStyleSheet(active if idx == 0 else inactive)
        self.btn_cerdo.setStyleSheet(active if idx == 1 else inactive)
        self.btn_pollo.setStyleSheet(active if idx == 2 else inactive)

    def _action_sincronizar(self):
        w = self.stack.currentWidget()
        db = DatabaseManager()
        try:
            actualizados = MotorPromedios.sincronizar_inventario(db, w._tipo_promedio, {w._tipo_promedio: w.get_state()})
            # This logic triggers reloads if needed, but for now we just show it.
            QMessageBox.information(self, "Sincronizado", f"Se han importado los precios de {actualizados} cortes desde el inventario.")
            # Note: We don't auto-reload the whole base, just inform. The user can click Repartir or Sinc will have updated the local table directly if implemented.
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo la sincronización: {e}")

    def _action_exportar(self):
        pwd, ok = QInputDialog.getText(self, "Exportar Inventario", "Ingrese contraseña de Jefe para autorizar:", QLineEdit.EchoMode.Password)
        if not ok or not pwd: return

        db = DatabaseManager()
        pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
        res = db.execute_query("SELECT rol FROM usuarios WHERE (pin = ? OR password_hash = ?)", (pwd, pwd_hash))
        if not res or res[0]['rol'] != 'jefe':
            QMessageBox.critical(self, "Acceso Denegado", "Contraseña incorrecta o el usuario no es Jefe.")
            return

        w = self.stack.currentWidget()
        try:
            actualizados = MotorPromedios.exportar_a_inventario(db, w._tipo_promedio, {w._tipo_promedio: w.get_state()})
            QMessageBox.information(self, "Éxito", f"Se exportaron los precios de {actualizados} cortes al inventario general.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo la exportación: {e}")

    def _action_pdf_interno(self):
        w = self.stack.currentWidget()
        try:
            from src.creador_pdf_global.motor_pdf_promedios import exportar_pdf_interno
            k = float(w._prom_kilos.text().replace(',', '.') or 0)
            m = float(w._prom_merma.text().replace(',', '.') or 0)
            p = float(w._prom_precio.text().replace(',', '.') or 0)
            exportar_pdf_interno(w._prom_tabla, w._input_proveedor.text(), w._input_fecha.date().toString("yyyy-MM-dd"), k, m, p, self)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al abrir PDF interno: {e}")

    def _action_pdf_clientes(self):
        w = self.stack.currentWidget()
        try:
            from src.creador_pdf_global.motor_pdf_promedios import exportar_pdf_clientes
            exportar_pdf_clientes(w._prom_tabla, w._input_proveedor.text(), w._input_fecha.date().toString("yyyy-MM-dd"), self)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al abrir PDF público: {e}")

    def cargar_datos(self):
        pass
