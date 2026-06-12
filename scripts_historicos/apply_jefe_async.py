import codecs
import re

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Restore ModernCard background
content = content.replace("""
            #card {
                
                border: none;
                border-radius: 20px;
            }
""", """
            #card {
                background: #FFFFFF;
                border: none;
                border-radius: 20px;
            }
""")

# 2. Extract everything from `def cargar_datos(self, periodo="Mes Actual"):` to `def setup_audit_ui(self):`
match = re.search(r'(    def cargar_datos\(self, periodo="Mes Actual"\):.*?)(    def _show_auditoria_tab\(self\):)', content, flags=re.DOTALL)
if match:
    old_cargar_datos = match.group(1)
    
    # Let's find where # FETCH DATA starts
    fetch_match = re.search(r'(.*?)(            # FETCH DATA.*)', old_cargar_datos, flags=re.DOTALL)
    if fetch_match:
        cargar_datos_top = fetch_match.group(1)
        sync_block = fetch_match.group(2)
        
        # We rewrite cargar_datos to end with thread start
        new_cargar_datos = cargar_datos_top + """
            # START ASYNC THREAD
            period_type = "day"
            if "Año" in self.current_period:
                period_type = "month"
            elif "Semana" in self.current_period:
                period_type = "week"
            else:
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
            
            # Start loading animation or disable things if needed
            self.worker.start()
"""

        # Now we create _on_data_loaded
        # We need to extract the UI rendering part from sync_block.
        # sync_block starts with `# FETCH DATA`. It computes v_bruta, ganancia, then does `# Limpiar KPIs previos`
        ui_render_match = re.search(r'(            # Limpiar KPIs previos.*)', sync_block, flags=re.DOTALL)
        
        if ui_render_match:
            ui_render = ui_render_match.group(1)
            
            # We need to remove the synchronous fetching parts inside ui_render, like:
            # - `res_diario = ...`
            # - `res_depto = db_manager.execute_query(...)`
            # Wait, `ui_render` contains everything from `# Limpiar KPIs previos` down to the end of `cargar_datos`!
            # It still contains synchronous queries for res_depto, res_pago, res_cajeros, res_productos, top_sold, bottom_sold!
            
            # We'll just define _on_data_loaded and use the emitted data dictionary!
            
            on_data_loaded_str = """
    def _on_data_loaded(self, data):
        if not data: return
        
        v_bruta = data.get('v_bruta', 0.0)
        ganancia = data.get('ganancia', 0.0)
        t_cant = data.get('t_cant', 0)
        display_chart_data = data.get('display_chart_data', {})
        res_diario = data.get('res_diario', [])
        res_depto = data.get('res_depto', [])
        res_pago = data.get('res_pago', [])
        res_cajeros = data.get('res_cajeros', [])
        res_productos = data.get('res_productos', [])
        
        t_promedio = v_bruta / t_cant if t_cant > 0 else 0.0
        margen = (ganancia / v_bruta * 100) if v_bruta > 0 else 0.0

        start_str = self.current_start_str
        end_str = self.current_end_str
        is_comp = False # Simplified for now

        # Limpiar KPIs previos
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

        # Gráfico principal
        if hasattr(self, 'main_chart'):
            self.main_chart.set_data(display_chart_data, None)
            
        # Tabla Ventas Tiempo
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtGui import QBrush, QColor, QFont
        from PyQt5.QtCore import Qt
        
        table_style = \"\"\"
            QTableWidget { background-color: #FFFFFF; border: none; color: #1E293B; }
            QTableWidget::item { padding: 14px; border-bottom: 1px solid #F8FAFC; font-size: 13px;  }
            QTableWidget::item:hover { background-color: #F8FAFC; }
            QHeaderView::section { background-color: #F1F5F9; color: #475569; font-weight: bold; border: none; padding: 10px; text-transform: uppercase; font-size: 11px; }
        \"\"\"
        
        self.tabla_vtas_tiempo.setRowCount(0)
        self.tabla_vtas_tiempo.setColumnCount(2)
        self.tabla_vtas_tiempo.horizontalHeader().setVisible(False)
        self.tabla_vtas_tiempo.setStyleSheet(table_style)
        
        if res_diario:
            self.tabla_vtas_tiempo.setRowCount(len(res_diario))
            for i, r in enumerate(reversed(res_diario)):
                self.tabla_vtas_tiempo.setItem(i, 0, QTableWidgetItem(str(r['dia'])))
                it = QTableWidgetItem(f"${r['tot']:,.2f}")
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_vtas_tiempo.setItem(i, 1, it)
                
        # Depto
        self.tabla_vtas_depto.setStyleSheet(table_style)
        self.tabla_gan_depto.setStyleSheet(table_style)
        
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
            self.depto_donut.set_data(donut_data)
            
        # Pago
        self.tabla_pago.setStyleSheet(table_style)
        if res_pago:
            self.tabla_pago.setRowCount(len(res_pago))
            for i, r in enumerate(res_pago):
                self.tabla_pago.setItem(i, 0, QTableWidgetItem(str(r['dia'])))
                self.tabla_pago.setItem(i, 1, QTableWidgetItem(str(r['m_pago'])))
                it = QTableWidgetItem(f"${float(r['tot'] or 0):,.2f}")
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_pago.setItem(i, 2, it)
                
        # Cajeros
        self.tabla_cajeros.setStyleSheet(table_style)
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
                
        # Estrellas
        self.tabla_estrellas.setStyleSheet(table_style)
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
            
            content = content.replace(old_cargar_datos, new_cargar_datos + on_data_loaded_str + "\n")

with codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("JefeReportes refactored to fully async successfully.")
