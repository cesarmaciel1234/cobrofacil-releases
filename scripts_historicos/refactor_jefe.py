import os

# 1. Update main_window.py
with open("src/main_window.py", "r", encoding="utf-8") as f:
    mw_code = f.read()

if "None,    # 20 — JefeReportes" not in mw_code:
    mw_code = mw_code.replace("None,    # 19 — Jefe0Dashboard           (lazy)", "None,    # 19 — Jefe0Dashboard           (lazy)\n            None,    # 20 — JefeReportes             (lazy)")
    mw_code = mw_code.replace("19: lambda: __import__('src.jefe.jefe0_dashboard',    fromlist=['Jefe0Dashboard']).Jefe0Dashboard(),", "19: lambda: __import__('src.jefe.jefe0_dashboard',    fromlist=['Jefe0Dashboard']).Jefe0Dashboard(),\n            20: lambda: __import__('src.jefe.jefe_reportes',    fromlist=['JefeReportes']).JefeReportes(),")

with open("src/main_window.py", "w", encoding="utf-8") as f:
    f.write(mw_code)

# 2. Update jefe0_dashboard.py
with open("src/jefe/jefe0_dashboard.py", "r", encoding="utf-8") as f:
    jd_code = f.read()

jd_code = jd_code.replace('("reportes",     "Reportes\\ny Ventas",       "📊", "#10B981", "#D1FAE5", "#065F46", 4,  None)', '("reportes",     "Reportes\\ny Ventas",       "📊", "#10B981", "#D1FAE5", "#065F46", 20,  None)')

with open("src/jefe/jefe0_dashboard.py", "w", encoding="utf-8") as f:
    f.write(jd_code)

# 3. Refactor jefe_reportes.py
with open("src/jefe/jefe_reportes.py", "r", encoding="utf-8") as f:
    jr_code = f.read()

# Replace class name
jr_code = jr_code.replace("class Admin3Reportes(QWidget):", "class JefeReportes(QWidget):")
jr_code = jr_code.replace("Admin3Reportes", "JefeReportes")

# We will inject DataLoaderThread and modify cargar_datos
# It's safer to use python regex or AST but we can just replace the function body of cargar_datos if we're careful.
# Since we know `def cargar_datos(self, periodo=None):` exists.

thread_class = """
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
            # 1. KPIs
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
            
            # 2. Chart Data
            import datetime
            s_dt_c = datetime.datetime.strptime(self.start_str, "%Y-%m-%d %H:%M:%S")
            e_dt_c = datetime.datetime.strptime(self.end_str, "%Y-%m-%d %H:%M:%S")
            
            chart_data = {}
            if self.period_type == "month":
                meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                for i, m in enumerate(meses_nombres):
                    chart_data[f"{i+1:02d}"] = {'ventas': 0.0, 'ganancia': 0.0, 'label': m}
                res_tot = db_manager.execute_query(
                    "SELECT substr(fecha, 6, 2) as key_val, SUM(total) as tot FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA') GROUP BY key_val", (self.start_str, self.end_str)
                )
                res_cost = db_manager.execute_query(
                    "SELECT substr(v.fecha, 6, 2) as key_val, SUM(dv.cantidad * COALESCE(p.costo, 0)) as costo FROM ventas v JOIN detalles_ventas dv ON v.id = dv.id_venta LEFT JOIN productos p ON dv.id_producto = p.id WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') GROUP BY key_val", (self.start_str, self.end_str)
                )
            else:
                dias_nombres = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                if self.period_type == "week":
                    for i in range(7):
                        curr_d = s_dt_c + datetime.timedelta(days=i)
                        chart_data[curr_d.strftime("%Y-%m-%d")] = {'ventas': 0.0, 'ganancia': 0.0, 'label': dias_nombres[i]}
                else:
                    days_diff = (e_dt_c - s_dt_c).days + 1
                    for i in range(days_diff):
                        curr_d = s_dt_c + datetime.timedelta(days=i)
                        chart_data[curr_d.strftime("%Y-%m-%d")] = {'ventas': 0.0, 'ganancia': 0.0, 'label': curr_d.strftime("%d")}
                        
                res_tot = db_manager.execute_query(
                    "SELECT substr(fecha, 1, 10) as key_val, SUM(total) as tot FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA') GROUP BY key_val", (self.start_str, self.end_str)
                )
                res_cost = db_manager.execute_query(
                    "SELECT substr(v.fecha, 1, 10) as key_val, SUM(dv.cantidad * COALESCE(p.costo, 0)) as costo FROM ventas v JOIN detalles_ventas dv ON v.id = dv.id_venta LEFT JOIN productos p ON dv.id_producto = p.id WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') GROUP BY key_val", (self.start_str, self.end_str)
                )

            if res_tot:
                for r in res_tot:
                    k = str(r['key_val'])
                    if k in chart_data:
                        chart_data[k]['ventas'] = float(r['tot'] or 0.0)
                        chart_data[k]['ganancia'] = float(r['tot'] or 0.0)
            if res_cost:
                for r in res_cost:
                    k = str(r['key_val'])
                    if k in chart_data:
                        c = float(r['costo'] or 0.0)
                        chart_data[k]['ganancia'] = chart_data[k]['ventas'] - c

            display_chart_data = {v['label']: {'ventas': v['ventas'], 'ganancia': v['ganancia']} for k, v in chart_data.items()}

            res_diario = []
            for k, v in chart_data.items():
                if self.period_type == "month" or self.period_type == "week":
                    res_diario.append({'dia': v['label'], 'tot': v['ventas'], 'label': v['label']})
                else:
                    res_diario.append({'dia': f"Día {v['label']}", 'tot': v['ventas'], 'label': v['label']})
                    
            # Depto data
            res_depto = db_manager.execute_query(
                "SELECT COALESCE(p.departamento, 'S/D') as depto, SUM(dv.subtotal) as tot, SUM(dv.cantidad * COALESCE(p.costo, 0)) as costo FROM detalles_ventas dv JOIN ventas v ON dv.id_venta = v.id LEFT JOIN productos p ON dv.id_producto = p.id WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') GROUP BY depto ORDER BY tot DESC", (self.start_str, self.end_str)
            )
            
            # Pago data
            res_pago = db_manager.execute_query(
                "SELECT substr(fecha, 1, 10) as dia, COALESCE(metodo_pago, 'Efectivo') as m_pago, SUM(total) as tot FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA') GROUP BY dia, m_pago", (self.start_str, self.end_str)
            )
            
            # Cajeros y Productos
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

import re
jr_code = jr_code.replace("class JefeReportes(QWidget):", thread_class + "\nclass JefeReportes(QWidget):")

# Rewrite cargar_datos
cargar_datos_new = """    def cargar_datos(self, periodo=None):
        if periodo:
            self.current_period = periodo
        else:
            periodo = getattr(self, "current_period", "Semana Actual")
            
        import datetime
        hoy = datetime.datetime.now()
        
        if periodo == "Semana Actual":
            start_date = hoy - datetime.timedelta(days=hoy.weekday())
            start_str = start_date.strftime("%Y-%m-%d 00:00:00")
            end_str = hoy.strftime("%Y-%m-%d 23:59:59")
        elif periodo == "Mes Actual":
            import calendar
            start_str = hoy.replace(day=1).strftime("%Y-%m-%d 00:00:00")
            last_day = calendar.monthrange(hoy.year, hoy.month)[1]
            end_str = hoy.replace(day=last_day).strftime("%Y-%m-%d 23:59:59")
        elif periodo == "Mes Anterior":
            first_day_this_month = hoy.replace(day=1)
            last_day_prev = first_day_this_month - datetime.timedelta(days=1)
            start_str = last_day_prev.replace(day=1).strftime("%Y-%m-%d 00:00:00")
            end_str = last_day_prev.strftime("%Y-%m-%d 23:59:59")
        elif periodo == "Año actual":
            start_str = hoy.replace(month=1, day=1).strftime("%Y-%m-%d 00:00:00")
            end_str = hoy.strftime("%Y-%m-%d 23:59:59")
        else:
            start_str, end_str = hoy.strftime("%Y-%m-%d 00:00:00"), hoy.strftime("%Y-%m-%d 23:59:59")
            
        for text, btn in self.period_buttons.items():
            btn.setStyleSheet("QPushButton { font-size: 13px; font-weight: bold; border: none; background: transparent; text-decoration: underline; }")
            if text == periodo:
                btn.setStyleSheet("QPushButton { font-size: 13px; font-weight: bold; border: none; background: transparent; text-decoration: underline; color: #10B981; }")
        
        lbl_title = self.findChild(QLabel, "lbl_main_title_financial")
        if lbl_title: lbl_title.setText(f"Resumen de Ventas ({periodo}) - Cargando...")
        
        period_type = "day"
        if "Año" in periodo: period_type = "month"
        elif "Semana" in periodo: period_type = "week"
        else: period_type = "month_days"
        
        self.loader_thread = DataLoaderThread(periodo, start_str, end_str, period_type)
        self.loader_thread.data_loaded.connect(self._on_data_loaded)
        self.loader_thread.start()

    def _on_data_loaded(self, data):
        if not data:
            return
            
        v_bruta = data.get("v_bruta", 0)
        ganancia = data.get("ganancia", 0)
        t_cant = data.get("t_cant", 0)
        t_promedio = v_bruta / t_cant if t_cant > 0 else 0
        margen = (ganancia / v_bruta * 100) if v_bruta > 0 else 0.0
        
        lbl_title = self.findChild(QLabel, "lbl_main_title_financial")
        if lbl_title: lbl_title.setText(f"Resumen de Ventas ({self.current_period})")

        for i in reversed(range(self.kpi_layout.count())): 
            w = self.kpi_layout.itemAt(i).widget()
            if w: w.deleteLater()
        
        def create_kpi(title, value, color="#0F172A"):
            w = QFrame()
            w.setStyleSheet(f"background: white; border-radius: 12px; border: 1px solid #E2E8F0;")
            l = QVBoxLayout(w)
            l.setContentsMargins(20,20,20,20)
            t = QLabel(title.upper())
            t.setStyleSheet(" font-size: 12px; font-weight: 800; border: none;")
            v = QLabel(value)
            v.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 900; border: none;")
            t.setAlignment(Qt.AlignCenter); v.setAlignment(Qt.AlignCenter)
            l.addWidget(t); l.addWidget(v)
            return w
            
        self.kpi_layout.addWidget(create_kpi("Ventas Totales", f"${v_bruta:,.2f}"), 0, 0)
        self.kpi_layout.addWidget(create_kpi("Ganancia Neta", f"${ganancia:,.2f}"), 0, 2)
        self.kpi_layout.addWidget(create_kpi("Número de Ventas", f"{t_cant}"), 1, 0)
        self.kpi_layout.addWidget(create_kpi("Ticket Promedio", f"${t_promedio:,.2f}"), 2, 0)
        self.kpi_layout.addWidget(create_kpi("Margen de utilidad promedio", f"{margen:,.0f}%", "#10B981"), 1, 2, 2, 1)

        self.stock_chart.update_data(data.get("display_chart_data", {}), None)
        
        table_style = "QTableWidget { background-color: white; border: none; } QTableWidget::item { padding: 10px; border-bottom: 1px solid #F1F5F9; font-size: 13px;  } QHeaderView::section { font-weight: bold; border: none; padding: 10px; text-transform: uppercase; font-size: 11px; }"
        
        self.tabla_vtas_tiempo.setRowCount(0)
        self.tabla_vtas_tiempo.setStyleSheet(table_style)
        for i, r in enumerate(data.get("res_diario", [])):
            self.tabla_vtas_tiempo.insertRow(i)
            self.tabla_vtas_tiempo.setItem(i, 0, QTableWidgetItem(r['dia']))
            it = QTableWidgetItem(f"${r['tot']:,.2f}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_vtas_tiempo.setItem(i, 1, it)

        donut_data = {}
        self.tabla_vtas_depto.setRowCount(0)
        self.tabla_gan_depto.setRowCount(0)
        self.tabla_vtas_depto.setStyleSheet(table_style)
        self.tabla_gan_depto.setStyleSheet(table_style)
        
        colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4", "#64748B"]
        for i, r in enumerate(data.get("res_depto", [])):
            nom = str(r['depto']).upper()
            v = float(r['tot'] or 0)
            c = float(r['costo'] or 0)
            donut_data[nom] = v
            self.tabla_vtas_depto.insertRow(i)
            self.tabla_gan_depto.insertRow(i)
            
            it_nom = QTableWidgetItem(f"● {nom}")
            it_nom.setForeground(QBrush(QColor(colors[i % len(colors)])))
            self.tabla_vtas_depto.setItem(i, 0, it_nom)
            it_v = QTableWidgetItem(f"${v:,.2f}")
            it_v.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_vtas_depto.setItem(i, 1, it_v)
            
            self.tabla_gan_depto.setItem(i, 0, QTableWidgetItem(f"● {nom}"))
            it_g = QTableWidgetItem(f"${(v-c):,.2f}")
            it_g.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_gan_depto.setItem(i, 1, it_g)
            
        self.depto_donut.data = donut_data
        self.depto_donut.update()

        chart_pago = {}
        for r in data.get("res_pago", []):
            d, m, t = str(r['dia']), str(r['m_pago']), float(r['tot'])
            if d not in chart_pago: chart_pago[d] = {}
            chart_pago[d][m] = chart_pago[d].get(m, 0) + t
        self.pago_chart.update_data(chart_pago)
        
        self.tabla_cajeros.setRowCount(0)
        for i, r in enumerate(data.get("res_cajeros", [])):
            self.tabla_cajeros.insertRow(i)
            self.tabla_cajeros.setItem(i, 0, QTableWidgetItem(f"👤 {str(r['cajero']).capitalize()}"))
            self.tabla_cajeros.setItem(i, 1, QTableWidgetItem(f"{r['cant']} tickets"))
            it = QTableWidgetItem(f"${r['tot']:,.2f}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_cajeros.setItem(i, 2, it)

        self.tabla_estrellas.setRowCount(0)
        for i, r in enumerate(data.get("res_productos", [])):
            self.tabla_estrellas.insertRow(i)
            self.tabla_estrellas.setItem(i, 0, QTableWidgetItem(f"⭐ {str(r['nombre']).title()[:17]}"))
            self.tabla_estrellas.setItem(i, 1, QTableWidgetItem(f"{r['cant']:,.2f} u/kg"))
            it = QTableWidgetItem(f"${r['tot']:,.2f}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_estrellas.setItem(i, 2, it)
"""

# Replace the old cargar_datos block
import re
# Find where def cargar_datos starts and where def _buscar_auditoria starts
pattern = re.compile(r"def cargar_datos\(self, periodo=None\):.*?def setup_audit_ui", re.DOTALL)
jr_code = pattern.sub(cargar_datos_new + "\n\n    def setup_audit_ui", jr_code)

with open("src/jefe/jefe_reportes.py", "w", encoding="utf-8") as f:
    f.write(jr_code)

print("Refactor complete")
