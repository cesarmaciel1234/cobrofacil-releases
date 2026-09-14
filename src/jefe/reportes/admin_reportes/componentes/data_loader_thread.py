from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager

import json
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QScrollArea, QGridLayout, QGraphicsDropShadowEffect, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QLineEdit, QFileDialog, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QSize, QThread, QUrl
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QLinearGradient, QPolygon, QPainterPath
import datetime

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

def get_depto_icon(depto_name):
    if not depto_name:
        return "📦"
    name = depto_name.strip().upper()
    if "CARNE" in name or "VACUNO" in name or "RES" in name or "CERDO" in name or "VACUN" in name or "ASADO" in name or "TERNER" in name:
        return "🥩"
    if "AVE" in name or "POLLO" in name or "GRANJA" in name or "POLLER" in name:
        return "🍗"
    if "ACHURA" in name or "CHINCHU" in name or "MENUDE" in name or "RIÑON" in name or "MOLLEJ" in name or "INTESTI" in name:
        return "🍢"
    if "PREPARADO" in name or "ELABORADO" in name or "HAMBUR" in name or "MILANE" in name or "ROTIS" in name:
        return "🍳"
    if "EMBUTIDO" in name or "FIAMBRE" in name or "SALCHI" in name or "CHORI" in name or "JAMON" in name or "SALA" in name or "CHARCU" in name:
        return "🌭"
    if "ALMACEN" in name or "ALMACÉN" in name or "ABARRO" in name or "DESPEN" in name:
        return "🥫"
    if "BEBIDA" in name or "REFRES" in name or "GASEO" in name or "CERVE" in name or "VINO" in name or "TRAGO" in name:
        return "🥤"
    if "VERDU" in name or "FRUTA" in name or "VEGETA" in name or "HORTE" in name:
        return "🥦"
    if "PANAD" in name or "PAN" in name or "FACTU" in name or "FACTUR" in name or "BIZCO" in name:
        return "🍞"
    if "LACTEO" in name or "LÁCTEO" in name or "QUESO" in name or "LECHE" in name or "MANTE" in name or "YOGU" in name:
        return "🧀"
    if "LIMPIE" in name or "HIGIEN" in name or "JABON" in name or "DETER" in name or "PERFU" in name:
        return "🧼"
    if "CONGEL" in name or "HELA" in name:
        return "❄️"
    if "KIOS" in name or "GOLO" in name or "CARAME" in name or "CHOCO" in name:
        return "🍬"
    return "📦"


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

