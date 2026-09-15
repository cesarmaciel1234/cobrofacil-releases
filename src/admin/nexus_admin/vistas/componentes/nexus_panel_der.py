import os
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QComboBox, 
                             QWidget, QScrollArea, QMessageBox, QFileDialog, QLineEdit)
from PyQt6.QtCore import Qt
from datetime import datetime

class CyberFeedItem(QFrame):
    def __init__(self, pc, fecha, tipo, usuario, obs, is_dark=False):
        super().__init__()
        
        icon = "🔹"
        color = "#38BDF8"
        if "SEGURIDAD" in tipo.upper() or "ALERTA" in tipo.upper() or "CRITICO" in obs.upper():
            icon = "🚨"
            color = "#EF4444"
        elif "INTERVENCION" in tipo.upper() or "INTERVENCIÓN" in tipo.upper():
            icon = "🔑"
            color = "#F59E0B"
        elif "APERTURA" in tipo.upper():
            icon = "💰"
            color = "#8B5CF6"
        elif "CIERRE" in tipo.upper():
            icon = "🏁"
            color = "#10B981"
        elif "VENTA" in tipo.upper():
            icon = "💵"
            color = "#10B981"
            
        bg_color = "#1E293B" if is_dark else "#FFFFFF"
        hover_color = "#283548" if is_dark else "#F8FAFC"
        border_color = "#0F172A" if is_dark else "#E2E8F0"
        hover_border = "#334155" if is_dark else "#CBD5E1"
        text_desc = "#94A3B8" if is_dark else "#64748B"
        pill_bg = "#0F172A" if is_dark else "#F1F5F9"
        pill_text = "#94A3B8" if is_dark else "#475569"
            
        self.setStyleSheet(f"""
            CyberFeedItem {{
                background-color: {bg_color}; 
                border: 1px solid {border_color};
                border-left: 4px solid {color};
                border-radius: 6px; 
                margin-bottom: 4px;
            }}
            CyberFeedItem:hover {{
                background-color: {hover_color};
                border: 1px solid {hover_border};
                border-left: 6px solid {color};
            }}
        """)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)
        
        t_lay = QHBoxLayout()
        t_lay.setContentsMargins(0,0,0,0)
        
        lbl_title = QLabel(f"<b><span style='color: {color}; font-size: 13px;'>{icon} [{pc}] {tipo}</span></b>")
        lbl_title.setTextFormat(Qt.TextFormat.RichText)
        
        try: time_str = str(fecha)[5:16]
        except: time_str = str(fecha)
            
        lbl_time = QLabel(f"<span style='background-color: {pill_bg}; color: {pill_text}; font-size: 10px; padding: 2px 6px; border-radius: 4px;'>&nbsp;{time_str}&nbsp;</span>")
        lbl_time.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        t_lay.addWidget(lbl_title)
        t_lay.addStretch()
        t_lay.addWidget(lbl_time)
        
        lbl_desc = QLabel(f"<span style='color: {text_desc}; font-size: 11px; font-style: italic;'><b>Usuario:</b> {usuario} &nbsp;//&nbsp; <b>Detalle:</b> {obs}</span>")
        lbl_desc.setWordWrap(True)
        lbl_desc.setTextFormat(Qt.TextFormat.RichText)
        lbl_desc.setContentsMargins(22, 0, 0, 0)
        
        lay.addLayout(t_lay)
        lay.addWidget(lbl_desc)

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
        
        self.btn_tab_cobros = QPushButton("💵 COBROS")
        self.btn_tab_cajones = QPushButton("💰 CAJONES")
        self.btn_tab_alertas = QPushButton("🚨 ALERTAS")
        self.btn_tab_acciones = QPushButton("👤 ACCIONES")
        
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
        
        self.btn_exportar = QPushButton("📥 EXPORTAR")
        self.btn_exportar.setCursor(Qt.PointingHandCursor)
        self.btn_exportar.setStyleSheet("QPushButton { background: #10B981; color: white; font-weight: bold; border-radius: 6px; padding: 6px 12px; font-size: 11px; } QPushButton:hover { background: #059669; }")
        self.btn_exportar.clicked.connect(self._exportar_auditoria_excel)
        header_layout.addWidget(self.btn_exportar)
        
        main_layout.addLayout(header_layout)
        
        # --- BODY CONTENEDOR PRINCIPAL ---
        self.body_container = QWidget()
        body_layout = QVBoxLayout(self.body_container)
        body_layout.setContentsMargins(10, 10, 10, 10)
        
        self.cmb_tipo_evento = QComboBox()
        self.cmb_tipo_evento.addItems(["Todos los Eventos", "Brechas de Seguridad", "Intervenciones Supervisor", "Turnos y Aperturas", "Cancelaciones de Tickets", "Ingresos y Retiros de Efectivo", "Ventas y Cobros"])
        self.cmb_tipo_evento.hide() 
        
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

        self.caja_filter = 0
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
            self.cmb_fecha.setStyleSheet("QComboBox { background: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 6px 10px; font-size: 11px; color: #F8FAFC; } QComboBox:focus { border-color: #38BDF8; background: #0F172A; }")
        else:
            self.body_container.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; border-top-left-radius: 0px; border: 1px solid #E2E8F0;")
            self.cmb_fecha.setStyleSheet("QComboBox { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 10px; font-size: 11px; color: #0F172A; font-weight: 500; } QComboBox:focus { border-color: #38BDF8; }")
            
        if hasattr(self, 'active_tab_index'):
            self.cambiar_pestana(self.active_tab_index)
        else:
            self.cambiar_pestana(0)
            
        # Update existing feed items
        for i in range(self.feed_layout.count()):
            item = self.feed_layout.itemAt(i)
            if item and item.widget():
                pass

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
        if index == 0: self.cmb_tipo_evento.setCurrentIndex(6)
        elif index == 1: self.cmb_tipo_evento.setCurrentIndex(3)
        elif index == 2: self.cmb_tipo_evento.setCurrentIndex(1)
        elif index == 3: self.cmb_tipo_evento.setCurrentIndex(2)
            
        self.filtrar_auditoria()

    def agregar_log(self, src, payload, fg_color):
        tipo = "EVENTO"
        if "[VENTA]" in payload: tipo = "VENTA"
        elif "ALERTA" in payload or "CRITICAL" in payload: tipo = "ALERTA_SEGURIDAD"
        elif "INTERVENCION" in payload or "INTERVENCIÓN" in payload: tipo = "INTERVENCION"
        elif "APERTURA" in payload: tipo = "APERTURA"
            
        idx = self.cmb_tipo_evento.currentIndex()
        if idx != 0: 
            if idx == 6 and tipo != "VENTA": return 
            if idx == 3 and tipo != "APERTURA": return 
            if idx == 1 and tipo != "ALERTA_SEGURIDAD": return 
            if idx == 2 and tipo != "INTERVENCION": return 
            
        import re
        
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
        if caja_id == "todas": self.caja_filter = 0
        else:
            try:
                import re
                num_match = re.search(r'\d+', str(caja_id))
                self.caja_filter = int(num_match.group()) if num_match else 0
            except: self.caja_filter = 0
        self.filtrar_auditoria()

    def filtrar_auditoria(self):
        idx_tipo = self.cmb_tipo_evento.currentIndex()
        q = "SELECT id, fecha, tipo, usuario, observaciones, monto, caja_id FROM movimientos_caja WHERE 1=1"
        p = []
        if idx_tipo == 1: q += " AND tipo='ALERTA_SEGURIDAD'"
        elif idx_tipo == 2: q += " AND tipo='INTERVENCION'"
        elif idx_tipo == 3: q += " AND tipo IN ('APERTURA', 'CIERRE_Z', 'CIERRE_AUTO')"
        elif idx_tipo == 4: q += " AND tipo='CANCELACION'"
        elif idx_tipo == 5: q += " AND tipo IN ('INGRESO', 'RETIRO')"
        elif idx_tipo == 6: q += " AND (tipo='VENTA' OR tipo LIKE '[TICKET]%')"
        else:
            q += " AND observaciones NOT LIKE '[TICKET]%' AND tipo NOT LIKE '[TICKET]%' AND tipo != 'VENTA'"
            
        f_val = self.cmb_fecha.currentText()
        if f_val == "Hoy": q += " AND DATE(fecha) = CURDATE()"
        elif f_val == "Ayer": q += " AND DATE(fecha) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)"
        elif f_val == "Esta Semana": q += " AND YEARWEEK(fecha, 1) = YEARWEEK(CURDATE(), 1)"
        elif f_val == "Este Mes": q += " AND YEAR(fecha) = YEAR(CURDATE()) AND MONTH(fecha) = MONTH(CURDATE())"
                
        if self.caja_filter > 0:
            q += " AND caja_id=?"
            p.append(self.caja_filter)

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
