import os
import re
from datetime import datetime
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QPushButton, QComboBox,
                             QWidget, QScrollArea, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt

from src.admin.nexus_admin.vistas.componentes.panel_derecho.cyber_feed_item import CyberFeedItem

class NexusPanelDer(QFrame):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = False
        self.setStyleSheet("background-color: transparent;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- HEADER PESTAÑAS (FILTROS) ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)

        self.btn_tab_cobros = QPushButton("\U0001F4B5 COBROS")
        self.btn_tab_cajones = QPushButton("\U0001F4B0 CAJONES")
        self.btn_tab_alertas = QPushButton("\U0001F6A8 ALERTAS")
        self.btn_tab_acciones = QPushButton("\U0001F464 ACCIONES")

        self.tabs = [self.btn_tab_cobros, self.btn_tab_cajones, self.btn_tab_alertas, self.btn_tab_acciones]
        for idx, btn in enumerate(self.tabs):
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.cambiar_pestana(i))
            header_layout.addWidget(btn)

        header_layout.addStretch()

        self.cmb_fecha = QComboBox()
        self.cmb_fecha.addItems(["Hoy", "Ayer", "Esta Semana", "Este Mes", "Todos los Tiempos"])
        self.cmb_fecha.setMinimumWidth(130)
        self.cmb_fecha.currentIndexChanged.connect(self.filtrar_auditoria)
        header_layout.addWidget(self.cmb_fecha)

        self.btn_exportar = QPushButton("\U0001F4E5 EXPORTAR")
        self.btn_exportar.setCursor(Qt.PointingHandCursor)
        self.btn_exportar.setStyleSheet("QPushButton { background: #10B981; color: white; font-weight: bold; border-radius: 6px; padding: 6px 12px; font-size: 11px; } QPushButton:hover { background: #059669; }")
        self.btn_exportar.clicked.connect(self._exportar_auditoria_excel)
        header_layout.addWidget(self.btn_exportar)

        main_layout.addLayout(header_layout)

        # --- BODY CONTENEDOR PRINCIPAL ---
        self.body_container = QWidget()
        body_layout = QVBoxLayout(self.body_container)
        body_layout.setContentsMargins(10, 10, 10, 10)


        self.scroll_eventos = QScrollArea()
        self.scroll_eventos.setWidgetResizable(True)
        self.scroll_eventos.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#feed_container { background: transparent; }")

        self.feed_container = QWidget()
        self.feed_container.setObjectName("feed_container")
        self.feed_layout = QVBoxLayout(self.feed_container)
        self.feed_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(2)

        self.scroll_eventos.setWidget(self.feed_container)
        self.scroll_eventos.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)

        body_layout.addWidget(self.scroll_eventos)
        main_layout.addWidget(self.body_container)

        self.caja_filter = 0  # Asegurar que sea int desde el inicio
        self.active_query = ""
        self.active_params = []
        self.offset = 0
        self.total_logs_count = 0

        # Initialize default theme styles
        self.update_theme('light')

    def update_theme(self, theme):
        self.is_dark_theme = (theme == 'dark')
        if theme == 'dark':
            self.body_container.setStyleSheet("background-color: #0F172A; border-radius: 8px; border-top-left-radius: 0px; border: 1px solid #1E293B;")
            self.cmb_fecha.setStyleSheet("QComboBox { background: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 6px 10px; font-size: 11px; color: #F8FAFC; } QComboBox:focus { border-color: #38BDF8; background: #0F172A; } QComboBox QAbstractItemView { background-color: #1E293B; color: #F8FAFC; selection-background-color: #38BDF8; selection-color: white; }")
        else:
            self.body_container.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; border-top-left-radius: 0px; border: 1px solid #E2E8F0;")
            self.cmb_fecha.setStyleSheet("QComboBox { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 10px; font-size: 11px; color: #0F172A; font-weight: 500; } QComboBox:focus { border-color: #38BDF8; } QComboBox QAbstractItemView { background-color: #FFFFFF; color: #0F172A; selection-background-color: #38BDF8; selection-color: white; }")

        if hasattr(self, 'active_tab_index'):
            self.cambiar_pestana(self.active_tab_index)
        else:
            self.cambiar_pestana(0)

    def cambiar_pestana(self, index):
        self.active_tab_index = index
        is_dark = self.is_dark_theme

        for i, btn in enumerate(self.tabs):
            if i == index:
                if is_dark:
                    btn.setStyleSheet("QPushButton { background-color: #0F172A; color: #F8FAFC; border: 1px solid #1E293B; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 8px 15px; font-weight: 800; font-size: 11px; }")
                else:
                    btn.setStyleSheet("QPushButton { background-color: #FFFFFF; color: #0F172A; border: 1px solid #E2E8F0; border-bottom: 2px solid #FFFFFF; border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 8px 15px; font-weight: 800; font-size: 11px; }")
            else:
                if is_dark:
                    btn.setStyleSheet("QPushButton { background-color: #1E293B; color: #64748B; border: 1px solid #1E293B; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 8px 15px; font-weight: 600; font-size: 11px; } QPushButton:hover { color: #38BDF8; }")
                else:
                    btn.setStyleSheet("QPushButton { background-color: #F1F5F9; color: #64748B; border: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 8px 15px; font-weight: 600; font-size: 11px; } QPushButton:hover { color: #3B82F6; background-color: #E2E8F0; }")

        # 0=COBROS, 1=CAJONES, 2=ALERTAS, 3=ACCIONES


        self.filtrar_auditoria()

    def agregar_log(self, src, payload, fg_color):
        tipo = "EVENTO"
        payload_upper = payload.upper()
        if "[VENTA]" in payload_upper: tipo = "VENTA"
        elif "ALERTA" in payload_upper or "CRITIC" in payload_upper: tipo = "ALERTA_SEGURIDAD"
        elif "INTERVENCION" in payload_upper or "INTERVENCI" in payload_upper: tipo = "INTERVENCION"
        elif "APERTURA" in payload_upper: tipo = "APERTURA"
        elif "CIERRE" in payload_upper: tipo = "CIERRE_Z"

        tab = getattr(self, 'active_tab_index', 0)
        # 0=COBROS, 1=CAJONES, 2=ALERTAS, 3=ACCIONES
        if tab == 0 and tipo != "VENTA":
            return
        if tab == 1 and tipo not in ["APERTURA", "CIERRE_Z", "CIERRE_AUTO", "CIERRE_TURNO"]:
            return
        if tab == 2 and tipo != "ALERTA_SEGURIDAD":
            return
        if tab == 3 and tipo != "INTERVENCION":
            return

        pc_clean = src
        match = re.search(r'PC-(\d+)', src)
        if match: pc_clean = f"PC-{match.group(1)}"

        partes = payload.split("-", 1)
        obs = partes[1].strip() if len(partes) > 1 else payload

        usr = "SISTEMA"
        if "cajero" in src.lower() or "caja" in src.lower(): usr = "CAJERO"
        if "jefe" in src.lower() or "admin" in src.lower(): usr = "JEFE"

        item = CyberFeedItem(pc_clean, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tipo, usr, obs, self.is_dark_theme)
        self.feed_layout.insertWidget(0, item)

        while self.feed_layout.count() > 100:
            w = self.feed_layout.takeAt(self.feed_layout.count()-1)
            if w.widget(): w.widget().deleteLater()

    def set_master_reference(self, admin_window):
        self.admin_master = admin_window

    def set_caja_filter(self, caja_id):
        if caja_id == "todas":
            self.caja_filter = 0
        else:
            try:
                num_match = re.search(r'\d+', str(caja_id))
                self.caja_filter = int(num_match.group()) if num_match else 0
            except:
                self.caja_filter = 0
        self.filtrar_auditoria()

    def filtrar_auditoria(self):
        tab = getattr(self, 'active_tab_index', 0)
        q = "SELECT id, fecha, tipo, usuario, observaciones, monto, caja_id FROM movimientos_caja WHERE 1=1"
        p = []
        if tab == 0: q += " AND (tipo='VENTA' OR tipo LIKE '[TICKET]%')"
        elif tab == 1: q += " AND tipo IN ('APERTURA', 'CIERRE_Z', 'CIERRE_AUTO')"
        elif tab == 2: q += " AND tipo='ALERTA_SEGURIDAD'"
        elif tab == 3: q += " AND tipo='INTERVENCION'"

        f_val = self.cmb_fecha.currentText()
        from datetime import datetime, timedelta
        hoy = datetime.now()

        if f_val == "Hoy":
            q += " AND fecha >= ? AND fecha <= ?"
            p.extend([hoy.strftime("%Y-%m-%d 00:00:00"), hoy.strftime("%Y-%m-%d 23:59:59")])
        elif f_val == "Ayer":
            ayer = hoy - timedelta(days=1)
            q += " AND fecha >= ? AND fecha <= ?"
            p.extend([ayer.strftime("%Y-%m-%d 00:00:00"), ayer.strftime("%Y-%m-%d 23:59:59")])
        elif f_val == "Esta Semana":
            inicio_sem = hoy - timedelta(days=hoy.weekday())
            q += " AND fecha >= ? AND fecha <= ?"
            p.extend([inicio_sem.strftime("%Y-%m-%d 00:00:00"), hoy.strftime("%Y-%m-%d 23:59:59")])
        elif f_val == "Este Mes":
            q += " AND fecha >= ? AND fecha <= ?"
            p.extend([hoy.strftime("%Y-%m-01 00:00:00"), hoy.strftime("%Y-%m-31 23:59:59")])

        try:
            caja_id = int(self.caja_filter)
        except (TypeError, ValueError):
            num = re.search(r"\d+", str(self.caja_filter or ""))
            caja_id = int(num.group()) if num else 0
        if caja_id > 0:
            q += " AND caja_id=?"
            p.append(caja_id)

        q_count = "SELECT COUNT(*) " + q[q.find("FROM movimientos_caja"):]
        try:
            from src.cerebro_global.nexus_cerebro import CerebroNexus
            self.total_logs_count = CerebroNexus.ejecutar_escalar(q_count, tuple(p)) or 0
        except:
            self.total_logs_count = 0

        q += " ORDER BY id DESC"

        self.active_query = q
        self.active_params = p
        self.offset = 0
        while self.feed_layout.count():
            item = self.feed_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._cargar_siguiente_pagina()

    def _cargar_siguiente_pagina(self):
        if self.feed_layout.count() >= self.total_logs_count: return
        q_paginated = f"{self.active_query} LIMIT 50 OFFSET {self.offset}"
        try:
            from src.cerebro_global.nexus_cerebro import CerebroNexus
            page_logs = CerebroNexus.ejecutar_query(q_paginated, tuple(self.active_params)) or []
        except:
            return
        if not page_logs: return

        for r in page_logs:
            tipo = str(r['tipo']).upper()
            obs = str(r['observaciones'] or '')
            usr = str(r['usuario'] or '').upper()
            try: c_id = int(r['caja_id']) if r['caja_id'] is not None else 1
            except: c_id = 1
            pc_name = f"CAJA-{c_id}"

            self.feed_layout.addWidget(CyberFeedItem(pc_name, r['fecha'], tipo, usr, obs, self.is_dark_theme))

        self.offset += 50

    def _al_hacer_scroll(self, value):
        bar = self.scroll_eventos.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() - 15:
            self._cargar_siguiente_pagina()

    def _exportar_auditoria_excel(self):
        try:
            from src.cerebro_global.nexus_cerebro import CerebroNexus
            all_logs = CerebroNexus.ejecutar_query(self.active_query, tuple(self.active_params)) or []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error DB: {e}")
            return
        if not all_logs: return

        path, _ = QFileDialog.getSaveFileName(self, "Exportar", f"seguridad_{datetime.now().strftime('%Y%m%d')}.xlsx", "Excel (*.xlsx)")
        if not path: return
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["ID", "Fecha", "Tipo", "Usuario", "Observaciones", "Monto"])
            for r in all_logs:
                ws.append([r['id'], str(r['fecha']), r['tipo'], r['usuario'], r['observaciones'], r['monto']])
            wb.save(path)
            QMessageBox.information(self, "OK", f"Exportado {len(all_logs)} registros.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
