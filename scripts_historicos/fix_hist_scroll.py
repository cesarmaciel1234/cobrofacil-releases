import codecs
import re

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = """    def _cargar_historial_tickets(self):
        if getattr(self, '_is_loading_historial', False): return
        if not getattr(self, '_historial_ui_loaded', False): return
        
        # Iniciar desde offset 0
        self.hist_offset = 0
        self.hist_limit = 50
        self.tabla_historial_crudo.setRowCount(0)
        
        # Conectar el scroll si no esta conectado
        scroll_bar = self.tabla_historial_crudo.verticalScrollBar()
        try:
            scroll_bar.valueChanged.disconnect(self._on_hist_scroll)
        except: pass
        scroll_bar.valueChanged.connect(self._on_hist_scroll)
        
        self._cargar_historial_pagina()

    def _on_hist_scroll(self, value):
        bar = self.tabla_historial_crudo.verticalScrollBar()
        if value >= bar.maximum() - 5:
            self._cargar_historial_pagina()

    def _cargar_historial_pagina(self):
        if getattr(self, '_is_loading_historial', False): return
        self._is_loading_historial = True
        try:
            from src.utils.db import db_manager
            query = f\"\"\"
                SELECT v.id, v.fecha, v.usuario, p.departamento, dv.nombre_producto,
                       dv.cantidad, p.unidad AS unidad_medida, dv.precio_unitario, dv.subtotal,
                       v.metodo_pago, v.estado
                FROM ventas v
                JOIN detalles_ventas dv ON dv.id_venta = v.id
                LEFT JOIN productos p ON dv.id_producto = p.id
                ORDER BY v.id DESC LIMIT {self.hist_limit} OFFSET {self.hist_offset}
            \"\"\"
            rows = db_manager.execute_query(query) or []
            
            filtro = self.txt_hist_buscar.text().strip().lower()
            if filtro:
                rows = [r for r in rows if filtro in str(r.get('id','')) or 
                                          filtro in str(r.get('nombre_producto','')).lower() or
                                          filtro in str(r.get('usuario','')).lower() or
                                          filtro in str(r.get('departamento','')).lower()]
                                          
            if not rows:
                return

            from PyQt5.QtGui import QColor, QFont
            from PyQt5.QtCore import Qt
            from PyQt5.QtWidgets import QTableWidgetItem
            
            font_mono = QFont("Consolas", 10, QFont.Bold)
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
                it_depto.setForeground(col_text)
                
                it_prod = QTableWidgetItem(str(r.get('nombre_producto', '')).upper())
                it_prod.setForeground(col_prod)
                it_prod.setFont(QFont("Segoe UI", 9, QFont.Bold))
                
                it_cant = QTableWidgetItem(f"{r.get('cantidad', 0):.2f}")
                it_cant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                it_cant.setFont(font_mono)
                it_cant.setForeground(col_text)
                
                it_um = QTableWidgetItem(str(r.get('unidad_medida', 'UN')))
                it_um.setTextAlignment(Qt.AlignCenter)
                it_um.setForeground(col_gray)
                
                it_punit = QTableWidgetItem(f"{r.get('precio_unitario', 0):.2f}")
                it_punit.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                it_punit.setFont(font_mono)
                it_punit.setForeground(col_gray)
                
                it_subt = QTableWidgetItem(f"{sign} {abs(subtotal_val):.2f}")
                it_subt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                it_subt.setFont(font_mono)
                it_subt.setForeground(trade_color)
                
                it_pago = QTableWidgetItem(str(r.get('metodo_pago', '')).upper())
                it_pago.setForeground(col_gray)
                it_pago.setTextAlignment(Qt.AlignCenter)
                
                it_estado = QTableWidgetItem(estado_val)
                it_estado.setTextAlignment(Qt.AlignCenter)
                it_estado.setFont(QFont("Segoe UI", 9, QFont.Bold))
                it_estado.setForeground(trade_color)
                
                bg = QColor("#ffffff") if i % 2 == 0 else QColor("#F8FAFC")
                for it in [it_id, it_fecha, it_cajero, it_depto, it_prod, it_cant, it_um, it_punit, it_subt, it_pago, it_estado]:
                    it.setBackground(bg)
                    it.setFont(QFont("Segoe UI", 9))
                
                self.tabla_historial_crudo.setItem(i, 0, it_id)
                self.tabla_historial_crudo.setItem(i, 1, it_fecha)
                self.tabla_historial_crudo.setItem(i, 2, it_cajero)
                self.tabla_historial_crudo.setItem(i, 3, it_depto)
                self.tabla_historial_crudo.setItem(i, 4, it_prod)
                self.tabla_historial_crudo.setItem(i, 5, it_cant)
                self.tabla_historial_crudo.setItem(i, 6, it_um)
                self.tabla_historial_crudo.setItem(i, 7, it_punit)
                self.tabla_historial_crudo.setItem(i, 8, it_subt)
                self.tabla_historial_crudo.setItem(i, 9, it_pago)
                self.tabla_historial_crudo.setItem(i, 10, it_estado)
                
            self.hist_offset += self.hist_limit
        finally:
            self._is_loading_historial = False"""

match = re.search(r'(    def _cargar_historial_tickets\(self\):.*?)(?=\Z)', text, flags=re.DOTALL)
if match:
    text = text.replace(match.group(1), replacement)
    codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8').write(text)
    print('Fixed historial infinite scroll logic')
else:
    print('Regex failed')
