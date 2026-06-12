import codecs
import re

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# --- HISTORIAL ---
# 1. Modify setup_historial_ui to connect the scroll bar
setup_hist_match = re.search(r'(    def setup_historial_ui\(self\):.*?)(        self\._historial_ui_loaded = True)', content, flags=re.DOTALL)
if setup_hist_match:
    setup_hist_block = setup_hist_match.group(1)
    if "self.historial_offset" not in setup_hist_block:
        # Inject initialization
        inject_hist = """
        self.historial_offset = 0
        self.historial_limit = 50
        self.tabla_historial_crudo.verticalScrollBar().valueChanged.connect(self._on_historial_scroll)
"""
        new_setup_hist = setup_hist_block + inject_hist
        content = content.replace(setup_hist_block, new_setup_hist)

# 2. Add _on_historial_scroll and _cargar_historial_pagina
scroll_hist_methods = """
    def _on_historial_scroll(self, value):
        if value == self.tabla_historial_crudo.verticalScrollBar().maximum():
            self._cargar_historial_pagina()

    def _cargar_historial_pagina(self):
        query = f\"\"\"
            SELECT v.id, v.fecha, v.usuario, p.departamento, dv.nombre_producto,
                   dv.cantidad, p.unidad AS unidad_medida, dv.precio_unitario, dv.subtotal,
                   v.metodo_pago, v.estado
            FROM ventas v
            JOIN detalles_ventas dv ON dv.id_venta = v.id
            LEFT JOIN productos p ON dv.id_producto = p.id
            ORDER BY v.id DESC LIMIT {self.historial_limit} OFFSET {self.historial_offset}
        \"\"\"
        from src.utils.db import db_manager
        rows = db_manager.execute_query(query) or []
        if not rows: return
        
        filtro = self.txt_hist_buscar.text().strip().lower()
        if filtro:
            rows = [r for r in rows if filtro in str(r.get('id','')) or 
                                      filtro in str(r.get('nombre_producto','')).lower() or
                                      filtro in str(r.get('usuario','')).lower() or
                                      filtro in str(r.get('departamento','')).lower()]
                                      
        from PyQt5.QtGui import QColor, QFont
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtCore import Qt
        
        col_green = QColor("#039855")
        col_red = QColor("#D92D20")
        col_text = QColor("#1E293B")
        col_gray = QColor("#64748B")
        col_prod = QColor("#4F46E5")
        
        for r in rows:
            i = self.tabla_historial_crudo.rowCount()
            self.tabla_historial_crudo.insertRow(i)
            
            estado_val = str(r.get('estado', '')).upper()
            subtotal_val = float(r.get('subtotal', 0))
            is_negative = estado_val in ['CANCELADA', 'ANULADA', 'REEMBOLSADA'] or subtotal_val < 0
            
            trade_color = col_red if is_negative else col_green
            sign = "-" if is_negative else "+"
            
            it_id = QTableWidgetItem(str(r.get('id', '')))
            it_id.setTextAlignment(Qt.AlignCenter)
            it_id.setForeground(col_gray)
            
            it_fecha = QTableWidgetItem(str(r.get('fecha', '')))
            it_fecha.setTextAlignment(Qt.AlignCenter)
            it_fecha.setForeground(col_gray)
            
            it_cajero = QTableWidgetItem(str(r.get('usuario', '')).upper())
            it_cajero.setForeground(col_text)
            
            it_depto = QTableWidgetItem(str(r.get('departamento', '')).upper())
            it_depto.setForeground(col_gray)
            
            it_prod = QTableWidgetItem(str(r.get('nombre_producto', '')).upper())
            it_prod.setForeground(col_prod)
            font_p = it_prod.font()
            font_p.setBold(True)
            it_prod.setFont(font_p)
            
            it_cant = QTableWidgetItem(f"{float(r.get('cantidad', 0)):.2f} {str(r.get('unidad_medida', ''))}")
            it_cant.setTextAlignment(Qt.AlignCenter)
            it_cant.setForeground(col_gray)
            
            it_monto = QTableWidgetItem(f"{sign}${abs(subtotal_val):,.2f}")
            it_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it_monto.setForeground(trade_color)
            font_m = it_monto.font()
            font_m.setBold(True)
            it_monto.setFont(font_m)
            
            it_estado = QTableWidgetItem(estado_val)
            it_estado.setTextAlignment(Qt.AlignCenter)
            it_estado.setForeground(col_text)
            
            self.tabla_historial_crudo.setItem(i, 0, it_id)
            self.tabla_historial_crudo.setItem(i, 1, it_fecha)
            self.tabla_historial_crudo.setItem(i, 2, it_cajero)
            self.tabla_historial_crudo.setItem(i, 3, it_depto)
            self.tabla_historial_crudo.setItem(i, 4, it_prod)
            self.tabla_historial_crudo.setItem(i, 5, it_cant)
            self.tabla_historial_crudo.setItem(i, 6, it_monto)
            self.tabla_historial_crudo.setItem(i, 7, it_estado)
            
        self.historial_offset += self.historial_limit
"""

# Replace old _cargar_historial_tickets completely
old_cargar_historial_match = re.search(r'(    def _cargar_historial_tickets\(self\):.*?)(    def)', content, flags=re.DOTALL)
if old_cargar_historial_match:
    old_cargar_historial = old_cargar_historial_match.group(1)
    new_cargar_historial = """    def _cargar_historial_tickets(self):
        self.historial_offset = 0
        self.tabla_historial_crudo.setRowCount(0)
        self._cargar_historial_pagina()

""" + scroll_hist_methods + "\n"
    content = content.replace(old_cargar_historial, new_cargar_historial)


# --- AUDITORIA ---
setup_audit_match = re.search(r'(    def setup_audit_ui\(self\):.*?)(        self\._audit_ui_loaded = True)', content, flags=re.DOTALL)
if setup_audit_match:
    setup_audit_block = setup_audit_match.group(1)
    if "self.audit_offset" not in setup_audit_block:
        inject_audit = """
        self.audit_offset = 0
        self.audit_limit = 50
        self.table_audit.verticalScrollBar().valueChanged.connect(self._on_audit_scroll)
"""
        new_setup_audit = setup_audit_block + inject_audit
        content = content.replace(setup_audit_block, new_setup_audit)

scroll_audit_methods = """
    def _on_audit_scroll(self, value):
        if value == self.table_audit.verticalScrollBar().maximum():
            self._cargar_audit_pagina()

    def _cargar_audit_pagina(self):
        mes_idx = self.cmb_audit_mes.currentIndex()
        import datetime
        now = datetime.datetime.now()
        
        where_clause = "estado IN ('COMPLETADA', 'CERRADA')"
        params = []
        
        if mes_idx > 0:
            where_clause += " AND MONTH(fecha) = ? AND YEAR(fecha) = ?"
            params.extend([mes_idx, now.year])
            
        cajero = self.cmb_audit_cajero.currentText()
        if cajero != "Todos los Cajeros":
            where_clause += " AND usuario = ?"
            params.append(cajero)
            
        depto = self.cmb_audit_depto.currentText()
        if depto != "Todos los Departamentos":
            where_clause += " AND p.departamento = ?"
            params.append(depto)
            
        filtro = self.txt_audit_buscar.text().strip()
        if filtro:
            where_clause += " AND (dv.nombre_producto LIKE ? OR v.id LIKE ?)"
            params.extend([f'%{filtro}%', f'%{filtro}%'])
            
        query = f\"\"\"
            SELECT v.id, v.fecha, v.usuario, p.departamento, dv.nombre_producto,
                   dv.cantidad, p.unidad, dv.precio_unitario, dv.subtotal,
                   v.metodo_pago, v.estado
            FROM ventas v
            JOIN detalles_ventas dv ON dv.id_venta = v.id
            LEFT JOIN productos p ON dv.id_producto = p.id
            WHERE {where_clause}
            ORDER BY v.fecha DESC LIMIT {self.audit_limit} OFFSET {self.audit_offset}
        \"\"\"
        
        from src.utils.db import db_manager
        rows = db_manager.execute_query(query, params) or []
        if not rows: return
        
        from PyQt5.QtGui import QColor
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtCore import Qt
        
        col_text = QColor("#1E293B")
        
        for r in rows:
            i = self.table_audit.rowCount()
            self.table_audit.insertRow(i)
            
            items = [
                str(r.get('id', '')),
                str(r.get('fecha', '')),
                str(r.get('usuario', '')),
                str(r.get('departamento', '')),
                str(r.get('nombre_producto', '')),
                f"{float(r.get('cantidad', 0)):.2f} {str(r.get('unidad', ''))}",
                f"${float(r.get('precio_unitario', 0)):,.2f}",
                f"${float(r.get('subtotal', 0)):,.2f}",
                str(r.get('metodo_pago', '')),
                str(r.get('estado', ''))
            ]
            
            for col_idx, val in enumerate(items):
                it = QTableWidgetItem(val)
                it.setForeground(col_text)
                if col_idx in [5, 6, 7]:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    it.setTextAlignment(Qt.AlignCenter)
                self.table_audit.setItem(i, col_idx, it)
                
        self.audit_offset += self.audit_limit
"""

old_buscar_audit_match = re.search(r'(    def _buscar_auditoria\(self\):.*?)(    def)', content, flags=re.DOTALL)
if old_buscar_audit_match:
    old_buscar_audit = old_buscar_audit_match.group(1)
    
    # Extract the KPI update logic which is at the end of _buscar_auditoria
    # Usually it's `tot_monto = ...` or `query_totales = ...`
    # We will keep _buscar_auditoria to clear the table, reset offset, call KPI logic, then _cargar_audit_pagina
    # But wait, it's easier to just append _cargar_audit_pagina to the end, and replace the rows loop
    
    # Replace the execution part in old_buscar_audit
    # The old execution is:
    # rows = db_manager.execute_query(...) or []
    # self.table_audit.setRowCount(0)
    # self.data = rows ...
    
    # We'll just write a new _buscar_auditoria that resets offset, calls KPIs, then calls _cargar_audit_pagina.
    
    new_buscar_audit = """    def _buscar_auditoria(self):
        self.audit_offset = 0
        self.table_audit.setRowCount(0)
        self.data = [] # Reset export data if needed
        
        mes_idx = self.cmb_audit_mes.currentIndex()
        import datetime
        now = datetime.datetime.now()
        where_clause = "estado IN ('COMPLETADA', 'CERRADA')"
        params = []
        if mes_idx > 0:
            where_clause += " AND MONTH(fecha) = ? AND YEAR(fecha) = ?"
            params.extend([mes_idx, now.year])
            
        from src.utils.db import db_manager
        q_kpi = f"SELECT SUM(dv.subtotal) as tot FROM ventas v JOIN detalles_ventas dv ON dv.id_venta = v.id LEFT JOIN productos p ON dv.id_producto = p.id WHERE {where_clause}"
        res_kpi = db_manager.execute_query(q_kpi, params)
        tot_monto = float(res_kpi[0]['tot'] or 0) if res_kpi and res_kpi[0] else 0.0
        
        for i in reversed(range(self.audit_kpi_layout.count())):
            w = self.audit_kpi_layout.itemAt(i).widget()
            if w: w.deleteLater()
            
        from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QGraphicsDropShadowEffect
        from PyQt5.QtGui import QColor
        from PyQt5.QtCore import Qt
        
        def build_kpi_card(titulo, valor, accent, bg="#FFFFFF", extra_text=None):
            f = QFrame()
            f.setObjectName("audit_kpi")
            f.setStyleSheet(f\"\"\"
                #audit_kpi {{
                    background: {bg};
                    border-radius: 18px;
                    border: none;
                }}
            \"\"\")
            sh = QGraphicsDropShadowEffect(f)
            sh.setBlurRadius(16)
            sh.setColor(QColor(0, 0, 0, 20))
            sh.setOffset(0, 4)
            f.setGraphicsEffect(sh)
            l = QVBoxLayout(f)
            l.setContentsMargins(18, 14, 18, 14)
            l.setSpacing(4)
            lbl_t = QLabel(titulo.upper())
            lbl_t.setStyleSheet("font-size: 10px; font-weight: 800;  border: none; background: none; color: #475569;")
            l.addWidget(lbl_t)
            lbl_v = QLabel(str(valor))
            lbl_v.setStyleSheet("font-size: 18px; font-weight: 900;  border: none; background: none; color: #1E293B;")
            l.addWidget(lbl_v)
            if extra_text:
                lbl_e = QLabel(extra_text)
                lbl_e.setStyleSheet("font-size: 11px; font-weight: bold;  border: none; background: none; color: #64748B;")
                l.addWidget(lbl_e)
            return f
            
        self.audit_kpi_layout.addWidget(build_kpi_card("Facturado Filtrado", f"${tot_monto:,.2f}", "green"))
        
        self._cargar_audit_pagina()

""" + scroll_audit_methods + "\n"

    content = content.replace(old_buscar_audit, new_buscar_audit)

with codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Infinite scroll implemented correctly.")
