import codecs
import re

with codecs.open('src/admin/admin3_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject DataLoaderThread before Admin3Reportes
thread_code = """
from PyQt5.QtCore import QThread, pyqtSignal

class DataLoaderThread(QThread):
    data_loaded = pyqtSignal(dict)

    def __init__(self, periodo, start_str, end_str, period_type):
        super().__init__()
        self.periodo = periodo
        self.start_str = start_str
        self.end_str = end_str
        self.period_type = period_type

    def run(self):
        try:
            from src.utils.db import db_manager
            import datetime
            
            # KPIs
            res_kpi = db_manager.execute_query(
                "SELECT SUM(total) as v_bruta, SUM(total - descuento + recargo) as v_neta, COUNT(id) as cant "
                "FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA')", 
                (self.start_str, self.end_str)
            )
            v_bruta = float(res_kpi[0]['v_bruta'] or 0.0) if res_kpi and res_kpi[0] else 0.0
            t_cant = int(res_kpi[0]['cant'] or 0) if res_kpi and res_kpi[0] else 0
            
            res_costo = db_manager.execute_query(
                "SELECT SUM(dv.cantidad * COALESCE(p.costo, 0)) as costo "
                "FROM detalles_ventas dv JOIN ventas v ON dv.id_venta = v.id "
                "LEFT JOIN productos p ON dv.id_producto = p.id "
                "WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA')",
                (self.start_str, self.end_str)
            )
            costo = float(res_costo[0]['costo'] or 0.0) if res_costo and res_costo[0] else 0.0
            ganancia = v_bruta - costo
            
            # Chart Data
            s_dt_c = datetime.datetime.strptime(self.start_str, "%Y-%m-%d %H:%M:%S")
            e_dt_c = datetime.datetime.strptime(self.end_str, "%Y-%m-%d %H:%M:%S")
            days_diff = (e_dt_c - s_dt_c).days + 1
            
            display_chart_data = {}
            if self.period_type == "day":
                query_chart = "SELECT substr(fecha, 12, 2) as hora, SUM(total) as tot FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA') GROUP BY hora"
                res = db_manager.execute_query(query_chart, (self.start_str, self.end_str))
                for r in (res or []): display_chart_data[f"{r['hora']}:00"] = float(r['tot'] or 0)
            elif self.period_type == "week" or days_diff <= 31:
                query_chart = "SELECT substr(fecha, 1, 10) as dia, SUM(total) as tot FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA') GROUP BY dia"
                res = db_manager.execute_query(query_chart, (self.start_str, self.end_str))
                for r in (res or []):
                    dt_obj = datetime.datetime.strptime(r['dia'], "%Y-%m-%d")
                    display_chart_data[dt_obj.strftime("%d/%m")] = float(r['tot'] or 0)
            else:
                query_chart = "SELECT substr(fecha, 1, 7) as mes, SUM(total) as tot FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA') GROUP BY mes"
                res = db_manager.execute_query(query_chart, (self.start_str, self.end_str))
                for r in (res or []):
                    try:
                        m_idx = int(r['mes'][-2:])
                        meses = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                        display_chart_data[meses[m_idx]] = float(r['tot'] or 0)
                    except: display_chart_data[r['mes']] = float(r['tot'] or 0)
            
            # Tablas Varias
            res_diario = db_manager.execute_query(
                "SELECT substr(fecha, 1, 10) as dia, SUM(total) as tot FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA') GROUP BY dia ORDER BY dia DESC", (self.start_str, self.end_str)
            )
            res_depto = db_manager.execute_query(
                "SELECT COALESCE(p.departamento, 'General') as depto, SUM(dv.subtotal) as tot, SUM(dv.cantidad * COALESCE(p.costo, 0)) as costo FROM detalles_ventas dv JOIN ventas v ON dv.id_venta = v.id LEFT JOIN productos p ON dv.id_producto = p.id WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') GROUP BY depto ORDER BY tot DESC", (self.start_str, self.end_str)
            )
            res_pago = db_manager.execute_query(
                "SELECT substr(fecha, 1, 10) as dia, COALESCE(metodo_pago, 'Efectivo') as m_pago, SUM(total) as tot FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA') GROUP BY dia, m_pago", (self.start_str, self.end_str)
            )
            res_cajeros = db_manager.execute_query(
                "SELECT COALESCE(v.usuario, 'Desconocido') as cajero, COUNT(v.id) as cant, SUM(v.total) as tot FROM ventas v WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') GROUP BY cajero ORDER BY tot DESC LIMIT 5", (self.start_str, self.end_str)
            )
            res_productos = db_manager.execute_query(
                "SELECT dv.nombre_producto as nombre, SUM(dv.cantidad) as cant, SUM(dv.subtotal) as tot FROM detalles_ventas dv JOIN ventas v ON dv.id_venta = v.id WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') GROUP BY dv.nombre_producto ORDER BY tot DESC LIMIT 5", (self.start_str, self.end_str)
            )

            self.data_loaded.emit({
                "v_bruta": v_bruta,
                "ganancia": ganancia,
                "t_cant": t_cant,
                "display_chart_data": display_chart_data,
                "res_diario": res_diario,
                "res_depto": res_depto,
                "res_pago": res_pago,
                "res_cajeros": res_cajeros,
                "res_productos": res_productos
            })
        except Exception as e:
            print("Error in DataLoaderThread:", e)
            self.data_loaded.emit({})

"""

content = re.sub(r'(class Admin3Reportes\(QWidget\):)', thread_code + r'\1', content, count=1)

# 2. Modify cargar_datos to start the thread
cargar_datos_match = re.search(r'(    def cargar_datos\(self, periodo="Mes Actual"\):.*?)(        # 1\. KPIs.*?)(\n    def )', content, flags=re.DOTALL)
if cargar_datos_match:
    prefix = cargar_datos_match.group(1)
    body_to_replace = cargar_datos_match.group(2)
    suffix = cargar_datos_match.group(3)
    
    new_body = """
        period_type = "month_days"
        import datetime
        try:
            s_dt_c = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            e_dt_c = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
            days_diff = (e_dt_c - s_dt_c).days + 1
            if days_diff > 60: period_type = "month"
        except: pass
        
        self.worker = DataLoaderThread(periodo, start_str, end_str, period_type)
        self.worker.data_loaded.connect(self._on_data_loaded)
        self.worker.start()
"""
    
    # Also add _on_data_loaded
    on_data_loaded = """
    def _on_data_loaded(self, data):
        if not data: return
        v_bruta = data.get('v_bruta', 0.0)
        ganancia = data.get('ganancia', 0.0)
        t_cant = data.get('t_cant', 0)
        t_promedio = v_bruta / t_cant if t_cant > 0 else 0.0
        margen = (ganancia / v_bruta * 100) if v_bruta > 0 else 0.0
        
        display_chart_data = data.get('display_chart_data', {})
        res_diario = data.get('res_diario', [])
        res_depto = data.get('res_depto', [])
        res_pago = data.get('res_pago', [])
        res_cajeros = data.get('res_cajeros', [])
        res_productos = data.get('res_productos', [])

        # Cleanup existing KPIs
        for i in reversed(range(self.kpi_layout.count())): 
            w = self.kpi_layout.itemAt(i).widget()
            if w: w.deleteLater()
            
        def create_kpi(title, value, color="#0F172A", align="left"):
            from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
            from PyQt5.QtCore import Qt
            w = QFrame()
            w.setStyleSheet("background: white; border-radius: 18px; border: 1px solid #E2E8F0;")
            l = QVBoxLayout(w)
            l.setContentsMargins(20,20,20,20)
            l.setSpacing(8)
            t = QLabel(title.upper())
            t.setStyleSheet(" font-size: 12px; font-weight: 800; color: #475569; letter-spacing: 1px; border: none;")
            v = QLabel(value)
            v.setStyleSheet(f"color: {color}; font-size: 34px; font-weight: 900; border: none;")
            t.setAlignment(Qt.AlignCenter)
            v.setAlignment(Qt.AlignCenter)
            l.addWidget(t)
            l.addWidget(v)
            return w
            
        self.kpi_layout.addWidget(create_kpi("Ventas Totales", f"${v_bruta:,.2f}"), 0, 0)
        self.kpi_layout.addWidget(create_kpi("Ganancia Neta", f"${ganancia:,.2f}"), 0, 2)
        self.kpi_layout.addWidget(create_kpi("Número de Ventas", f"{t_cant}"), 1, 0)
        self.kpi_layout.addWidget(create_kpi("Ticket Promedio", f"${t_promedio:,.2f}"), 2, 0)
        self.kpi_layout.addWidget(create_kpi("Margen de utilidad", f"{margen:,.0f}%", "#10B981"), 1, 2, 2, 1)

        if hasattr(self, 'main_chart'):
            self.main_chart.set_data(display_chart_data, None)
            
        # Tables
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtCore import Qt
        
        self.tabla_vtas_tiempo.setRowCount(0)
        if res_diario:
            self.tabla_vtas_tiempo.setRowCount(len(res_diario))
            for i, r in enumerate(reversed(res_diario)):
                self.tabla_vtas_tiempo.setItem(i, 0, QTableWidgetItem(str(r['dia'])))
                it = QTableWidgetItem(f"${r['tot']:,.2f}")
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_vtas_tiempo.setItem(i, 1, it)

        donut_data = {}
        if res_depto:
            self.tabla_vtas_depto.setRowCount(min(len(res_depto), 15))
            self.tabla_gan_depto.setRowCount(min(len(res_depto), 15))
            for i, r in enumerate(res_depto[:15]):
                d = str(r['depto']).upper()
                tot = float(r['tot'] or 0.0)
                cost = float(r['costo'] or 0.0)
                gan = tot - cost
                donut_data[d] = tot
                self.tabla_vtas_depto.setItem(i, 0, QTableWidgetItem(d))
                it = QTableWidgetItem(f"${tot:,.2f}")
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_vtas_depto.setItem(i, 1, it)
                
                self.tabla_gan_depto.setItem(i, 0, QTableWidgetItem(d))
                it2 = QTableWidgetItem(f"${gan:,.2f}")
                it2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_gan_depto.setItem(i, 1, it2)
                
        if hasattr(self, 'depto_donut'):
            if hasattr(self.depto_donut, 'update_data'):
                self.depto_donut.update_data(donut_data)
            else:
                self.depto_donut.set_data(donut_data)
                
        if res_pago:
            self.tabla_pago.setRowCount(len(res_pago))
            for i, r in enumerate(res_pago):
                self.tabla_pago.setItem(i, 0, QTableWidgetItem(str(r['dia'])))
                self.tabla_pago.setItem(i, 1, QTableWidgetItem(str(r['m_pago'])))
                it = QTableWidgetItem(f"${float(r['tot'] or 0):,.2f}")
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_pago.setItem(i, 2, it)
                
        if res_cajeros:
            self.tabla_cajeros.setRowCount(len(res_cajeros))
            for i, r in enumerate(res_cajeros):
                self.tabla_cajeros.setItem(i, 0, QTableWidgetItem(str(r['cajero']).upper()))
                it1 = QTableWidgetItem(str(r['cant']))
                it1.setTextAlignment(Qt.AlignCenter)
                self.tabla_cajeros.setItem(i, 1, it1)
                it2 = QTableWidgetItem(f"${float(r['tot'] or 0):,.2f}")
                it2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_cajeros.setItem(i, 2, it2)
                
        if res_productos:
            self.tabla_estrellas.setRowCount(len(res_productos))
            for i, r in enumerate(res_productos):
                self.tabla_estrellas.setItem(i, 0, QTableWidgetItem(str(r['nombre']).upper()))
                it1 = QTableWidgetItem(f"{float(r['cant'] or 0):.2f}")
                it1.setTextAlignment(Qt.AlignCenter)
                self.tabla_estrellas.setItem(i, 1, it1)
                it2 = QTableWidgetItem(f"${float(r['tot'] or 0):,.2f}")
                it2.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_estrellas.setItem(i, 2, it2)
"""
    
    content = content.replace(cargar_datos_match.group(0), prefix + new_body + on_data_loaded + suffix)

# 3. Add Infinite Scroll to _cargar_historial_tickets
hist_match = re.search(r'(    def _cargar_historial_tickets\(self\):.*?)(?=\n    def )', content, flags=re.DOTALL)
if hist_match:
    infinite_scroll_hist = """    def _cargar_historial_tickets(self):
        if getattr(self, '_is_loading_historial', False): return
        
        self.hist_offset = 0
        self.hist_limit = 50
        self.tabla_historial_crudo.setRowCount(0)
        
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
                                          
            if not rows: return
            
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
                it_fecha = QTableWidgetItem(str(r.get('fecha', '')))
                it_cajero = QTableWidgetItem(str(r.get('usuario', '')).upper())
                it_depto = QTableWidgetItem(str(r.get('departamento', '')).upper())
                it_prod = QTableWidgetItem(str(r.get('nombre_producto', '')).upper())
                it_cant = QTableWidgetItem(f"{r.get('cantidad', 0):.2f}")
                it_um = QTableWidgetItem(str(r.get('unidad_medida', 'UN')))
                it_punit = QTableWidgetItem(f"{r.get('precio_unitario', 0):.2f}")
                it_subt = QTableWidgetItem(f"{sign} {abs(subtotal_val):.2f}")
                it_pago = QTableWidgetItem(str(r.get('metodo_pago', '')).upper())
                it_estado = QTableWidgetItem(estado_val)
                
                it_id.setTextAlignment(Qt.AlignCenter)
                it_id.setForeground(col_gray)
                it_fecha.setTextAlignment(Qt.AlignCenter)
                it_fecha.setForeground(col_gray)
                it_cajero.setForeground(col_text)
                it_depto.setForeground(col_text)
                it_prod.setForeground(col_prod)
                it_prod.setFont(QFont("Segoe UI", 9, QFont.Bold))
                it_cant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                it_cant.setFont(font_mono)
                it_cant.setForeground(col_text)
                it_um.setTextAlignment(Qt.AlignCenter)
                it_um.setForeground(col_gray)
                it_punit.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                it_punit.setFont(font_mono)
                it_punit.setForeground(col_gray)
                it_subt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                it_subt.setFont(font_mono)
                it_subt.setForeground(trade_color)
                it_pago.setForeground(col_gray)
                it_pago.setTextAlignment(Qt.AlignCenter)
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
    content = content.replace(hist_match.group(1), infinite_scroll_hist)

with codecs.open('src/admin/admin3_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied perfectly!")
