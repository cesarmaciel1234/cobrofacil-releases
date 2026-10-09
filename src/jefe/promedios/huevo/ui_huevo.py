"""
ui_huevo.py - Interfaz de usuario para cálculo de promedios de huevo
TPV Pro 2026 · Cobro Fácil POS

Estructura clon de pollo:
- Cajón = 12 maples
- 1 maple = 30 huevos
- Venta por maple: 30, 15, 10, 6 huevos
"""

import os
import json
import math
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from src.contabilidad.shared_globals import PAL, btn_primary, build_table
from .motor_huevo import MotorHuevo
from src.jefe.promedios.motor_global_promedios import MotorPromedios
from src.base_de_datos.database import DatabaseManager

class UIHuevo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tipo_promedio = "Huevo"
        self._build_ui()

    def get_state(self):
        filas = []
        for r in range(self._prom_tabla.rowCount()):
            row_data = []
            for c in range(self._prom_tabla.columnCount()):
                it = self._prom_tabla.item(r, c)
                row_data.append(it.text() if it else "")
            filas.append(row_data)
        return {
            "precio_cajon": self._input_precio_cajon.text(),
            "costo_maple": self._lbl_costo_maple.text(),
            "costo_huevo": self._lbl_costo_huevo.text(),
            "filas": filas
        }

    def set_state(self, estado):
        self._prom_tabla.blockSignals(True)
        self._input_precio_cajon.setText(estado.get("precio_cajon", ""))
        self._input_precio_cajon.blockSignals(True)
        self._input_precio_cajon.blockSignals(False)
        
        filas = estado.get("filas", [])
        self._prom_tabla.setRowCount(0)
        for i, row_data in enumerate(filas):
            self._prom_tabla.insertRow(i)
            for col in range(12):
                val = str(row_data[col]) if col < len(row_data) else "0.00"
                it = QTableWidgetItem(val)
                if col in [2, 8, 9, 10, 11]:
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if col == 2: it.setForeground(QColor(PAL['text3']))
                self._prom_tabla.setItem(i, col, it)
        self._add_empty_row()
        self._prom_tabla.blockSignals(False)
        self._sync_calc_huevo()

    def redondear(self):
        if not hasattr(self, '_costo_maple') or self._costo_maple == 0: return
        self._prom_tabla.blockSignals(True)
        for r in range(self._prom_tabla.rowCount()):
            try:
                precio_actual = float(self._prom_tabla.item(r, 3).text().replace(',', ''))
                if precio_actual > 0:
                    redondeado = math.ceil(precio_actual / 10) * 10
                    self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{redondeado:,.2f}"))
            except: pass
        self._prom_tabla.blockSignals(False)
        self._on_tabla_changed(None)

    def _action_guardar(self):
        prov = self._input_proveedor.text().strip()
        if not prov:
            QMessageBox.warning(self, "Datos Incompletos", "Ingrese el nombre del proveedor para guardar el historial.")
            return
        db = DatabaseManager()
        fecha_str = self._input_fecha.date().toString("dd/MM/yyyy")
        if MotorPromedios.guardar_historial(db, self._tipo_promedio, self.get_state(), prov, fecha_str):
            QMessageBox.information(self, "Guardado", "El historial ha sido guardado exitosamente.")
        else:
            QMessageBox.warning(self, "Error", "No se pudo guardar el historial.")

    def _action_cargar(self):
        db = DatabaseManager()
        registros = MotorPromedios.obtener_historial(db, self._tipo_promedio)
        if not registros:
            QMessageBox.information(self, "Historial", "No hay registros guardados para esta categoría.")
            return
            
        items = []
        for r in registros:
            items.append(f"{r['id']} - {r['fecha']} - {r['proveedor']}")
            
        dlg = QDialog(self)
        dlg.setWindowTitle("Cargar Historial")
        dlg.setStyleSheet(f"background: {PAL['bg']}; color: {PAL['text']}; font-size: 14px;")
        dlg.setMinimumWidth(350)
        
        l_v = QVBoxLayout(dlg)
        l_v.addWidget(QLabel("Seleccione el registro a cargar:"))
        
        combo = QComboBox()
        combo.addItems(items)
        combo.setStyleSheet(f"background: {PAL['surface']}; padding: 8px; border: 1px solid {PAL['border']}; border-radius: 4px;")
        l_v.addWidget(combo)
        
        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bbox.accepted.connect(dlg.accept)
        bbox.rejected.connect(dlg.reject)
        btn_ok = bbox.button(QDialogButtonBox.StandardButton.Ok)
        btn_ok.setText("Cargar")
        btn_ok.setStyleSheet(f"background: {PAL['primary']}; color: white; padding: 6px 16px; border-radius: 4px; font-weight: bold;")
        btn_cancel = bbox.button(QDialogButtonBox.StandardButton.Cancel)
        btn_cancel.setText("Cancelar")
        btn_cancel.setStyleSheet(f"background: {PAL['border']}; color: #0F172A; padding: 6px 16px; border-radius: 4px; font-weight: bold;")
        l_v.addSpacing(10)
        l_v.addWidget(bbox)
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = combo.currentText()
            id_sel = int(item.split(" - ")[0])
            for r in registros:
                if r['id'] == id_sel:
                    try:
                        estado = {
                            "precio_cajon": str(r.get('precio_cajon', '')),
                            "filas": r.get('filas', [])
                        }
                        self._input_proveedor.setText(r.get('proveedor', ''))
                        self.set_state(estado)
                    except: pass
                    break

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        
        # Header como pollo
        r1_lay = QHBoxLayout()
        lbl_prov = QLabel("Proveedor:")
        lbl_prov.setStyleSheet("font-weight: bold; color: #0F172A;")
        self._input_proveedor = QLineEdit()
        self._input_proveedor.setPlaceholderText("Proveedor")
        
        lbl_fecha = QLabel("Fecha:")
        lbl_fecha.setStyleSheet("font-weight: bold; color: #0F172A;")
        self._input_fecha = QDateEdit()
        self._input_fecha.setCalendarPopup(True)
        self._input_fecha.setDate(QDate.currentDate())
        
        self.btn_guardar = btn_primary("Guardar Historial")
        self.btn_guardar.setStyleSheet(self.btn_guardar.styleSheet().replace(PAL['primary'], "#0EA5E9"))
        self.btn_guardar.clicked.connect(self._action_guardar)
        self.btn_cargar = btn_primary("Cargar Historial")
        self.btn_cargar.setStyleSheet(self.btn_cargar.styleSheet().replace(PAL['primary'], "#3B82F6"))
        self.btn_cargar.clicked.connect(self._action_cargar)
        
        r1_lay.addWidget(lbl_prov)
        r1_lay.addWidget(self._input_proveedor)
        r1_lay.addStretch()
        r1_lay.addWidget(lbl_fecha)
        r1_lay.addWidget(self._input_fecha)
        r1_lay.addWidget(self.btn_guardar)
        r1_lay.addWidget(self.btn_cargar)
        lay.addLayout(r1_lay)

        # Datos como pollo (adaptados a huevo)
        r2_lay = QHBoxLayout()
        
        lbl_precio_cajon = QLabel("Precio Cajón:")
        lbl_precio_cajon.setStyleSheet("color: #0F172A; font-weight: bold;")
        self._input_precio_cajon = QLineEdit()
        self._input_precio_cajon.setFixedWidth(120)
        self._input_precio_cajon.textChanged.connect(self._sync_calc_huevo)
        
        self._lbl_costo_maple = QLabel("$0.00")
        self._lbl_costo_maple.setStyleSheet("font-weight: bold; font-size: 14px; color: #0F172A;")
        
        self._lbl_costo_huevo = QLabel("$0.00")
        self._lbl_costo_huevo.setStyleSheet("font-weight: bold; font-size: 14px; color: #0F172A;")
        
        r2_lay.addWidget(lbl_precio_cajon)
        r2_lay.addWidget(self._input_precio_cajon)
        r2_lay.addWidget(QLabel("Costo Maple:"))
        r2_lay.addWidget(self._lbl_costo_maple)
        r2_lay.addWidget(QLabel("Costo Huevo:"))
        r2_lay.addWidget(self._lbl_costo_huevo)
        r2_lay.addStretch()
        lay.addLayout(r2_lay)

        # Tabla con 12 columnas (igual a pollo)
        self._prom_tabla = build_table([
            "Maple Venta", "Huevos", "Costo Maple", "Precio Venta", "% Ganancia", 
            "P. Mayoreo", "Desde unid", "% Mayoreo", "V. Costo", "V. Total", "V. Mayoreo", "Ganancia", "G. Mayoreo"
        ])
        self._prom_tabla.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed | QAbstractItemView.EditTrigger.AnyKeyPressed)
        self._prom_tabla.itemChanged.connect(self._on_tabla_changed)
        lay.addWidget(self._prom_tabla)

        # Footer con totales (igual a pollo)
        self._lbl_totales = QLabel()
        self._lbl_totales.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_totales.setStyleSheet(f"font-size: 15px; font-weight: 800; margin-top: 10px;")
        lay.addWidget(self._lbl_totales)

        # Cargar datos por defecto
        self._load_defaults()
    
    def _sync_calc_huevo(self):
        """Calcula automáticamente los costos al cambiar el precio del cajón"""
        try:
            from .motor_huevo import MotorHuevo
            
            precio_cajon = float(self._input_precio_cajon.text().replace(',', '.') or 0)
            
            if precio_cajon > 0:
                # Estructura: 1 cajón = 12 maples, 1 maple = 30 huevos
                costo_maple, costo_huevo, total_huevos = MotorHuevo.calcular_costo_cajon(precio_cajon)
                
                self._lbl_costo_maple.setText(f"${costo_maple:.2f}")
                self._lbl_costo_huevo.setText(f"${costo_huevo:.2f}")
                
                # Guardar costo del maple para cálculos de tabla
                self._costo_maple = costo_maple
                
                # Recalcular tabla automáticamente
                self._on_tabla_changed(None, from_calc=True)
                
        except Exception as e:
            print(f"Error en sync_calc_huevo: {e}")
    
    def _load_defaults(self):
        """Carga las filas por defecto para huevo (maples de venta)"""
        self._prom_tabla.blockSignals(True)
        self._prom_tabla.setRowCount(0)
        
        # Maples de venta: 30, 15, 10, 6 huevos
        maples_venta = [
            ("Maple 30 huevos", 30),
            ("Maple 15 huevos", 15),
            ("Maple 10 huevos", 10),
            ("Maple 6 huevos", 6)
        ]
        
        for i, (nombre, huevos) in enumerate(maples_venta):
            self._prom_tabla.insertRow(i)
            self._prom_tabla.setItem(i, 0, QTableWidgetItem(nombre))
            self._prom_tabla.setItem(i, 1, QTableWidgetItem(str(huevos)))
            for col in range(2, 13):
                val = "0.00" if col != 6 else ""
                it = QTableWidgetItem(val)
                if col in [2, 8, 9, 10, 11, 12]:
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if col == 2: it.setForeground(QColor(PAL['text3']))
                self._prom_tabla.setItem(i, col, it)
        
        self._add_empty_row()
        self._prom_tabla.blockSignals(False)
        
        # Inicializar costos en 0
        self._costo_maple = 0.0
        self._costo_huevo = 0.0
        
        # Calcular con precio actual (si hay)
        self._sync_calc_huevo()

    def _add_empty_row(self):
        i = self._prom_tabla.rowCount()
        self._prom_tabla.insertRow(i)
        self._prom_tabla.setItem(i, 0, QTableWidgetItem(""))
        self._prom_tabla.setItem(i, 1, QTableWidgetItem(""))
        for col in range(2, 13):
            val = "0.00" if col != 6 else ""
            it = QTableWidgetItem(val)
            if col in [2, 8, 9, 10, 11, 12]:
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 2: it.setForeground(QColor(PAL['text3']))
            self._prom_tabla.setItem(i, col, it)

    def _on_tabla_changed(self, item, from_calc=False):
        """Calcula automáticamente precios, ganancias y mayoreo (como pollo)"""
        if getattr(self, '_is_updating', False): return
        self._prom_tabla.blockSignals(True)
        self._is_updating = True
        try:
            if not hasattr(self, '_costo_maple'):
                self._costo_maple = 0.0
            
            c_ed = item.column() if item else -1
            r_ed = item.row() if item else -1
            
            # Normalizar entrada
            if item and c_ed in [3, 4, 5, 7]:
                t = item.text().replace(',', '.')
                ct = ''.join(c for c in t if c.isdigit() or c in '.-')
                if ct != t: item.setText(ct)
            
            # Agregar fila vacía si se edita nombre de última fila
            if item and c_ed == 0 and r_ed == self._prom_tabla.rowCount() - 1 and item.text().strip():
                self._add_empty_row()
            
            t_vn = 0.0
            t_gn = 0.0
            t_vo = 0.0
            t_go = 0.0
            
            for r in range(self._prom_tabla.rowCount()):
                try:
                    item_huevos = self._prom_tabla.item(r, 1)
                    huevos = int(item_huevos.text() or 0) if item_huevos else 0
                    
                    # Costo proporcional del maple según cantidad de huevos
                    costo_proporcion = self._costo_maple * (huevos / 30) if self._costo_maple > 0 else 0.0
                    self._prom_tabla.setItem(r, 2, QTableWidgetItem(f"{costo_proporcion:,.2f}"))
                    
                    pv = float(self._prom_tabla.item(r, 3).text() or 0)
                    pg = float(self._prom_tabla.item(r, 4).text() or 0)
                    pm = float(self._prom_tabla.item(r, 5).text() or 0)
                    pmg = float(self._prom_tabla.item(r, 7).text() or 0)
                    
                    if costo_proporcion > 0:
                        # Recalcular % ganancia si se editó precio venta
                        if c_ed == 4 and r == r_ed:
                            pg = ((pv / costo_proporcion) - 1) * 100 if pv > 0 else 0.0
                            self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{pg:.2f}"))
                        # Recalcular precio venta si se editó % ganancia
                        elif c_ed == 4:
                            pv = costo_proporcion * (1 + pg / 100)
                            self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pv:,.2f}"))
                        
                        # Recalcular % mayoreo si se editó precio mayoreo
                        if c_ed == 7 and r == r_ed:
                            pmg = ((pm / costo_proporcion) - 1) * 100 if pm > 0 else 0.0
                            self._prom_tabla.setItem(r, 7, QTableWidgetItem(f"{pmg:.2f}"))
                        # Recalcular precio mayoreo si se editó % mayoreo
                        elif c_ed == 7:
                            pm = costo_proporcion * (1 + pmg / 100)
                            self._prom_tabla.setItem(r, 5, QTableWidgetItem(f"{pm:,.2f}"))
                    else:
                        if from_calc:
                            pg = 0.0
                            pmg = 0.0
                            self._prom_tabla.setItem(r, 4, QTableWidgetItem("0.00"))
                            self._prom_tabla.setItem(r, 7, QTableWidgetItem("0.00"))
                    
                    # Cálculos de totales
                    v_costo = costo_proporcion
                    if pv > 0:
                        vn = pv
                        gn = vn - v_costo
                    else:
                        vn = 0.0
                        gn = 0.0
                    t_vn += vn
                    t_gn += gn
                    
                    if pm > 0:
                        vo = pm
                        go = vo - v_costo
                    else:
                        vo = 0.0
                        go = 0.0
                    t_vo += vo
                    t_go += go
                    
                    self._prom_tabla.setItem(r, 8, QTableWidgetItem(f"{v_costo:,.2f}"))
                    self._prom_tabla.setItem(r, 9, QTableWidgetItem(f"{vn:,.2f}"))
                    self._prom_tabla.setItem(r, 10, QTableWidgetItem(f"{vo:.2f}"))
                    self._prom_tabla.setItem(r, 11, QTableWidgetItem(f"{gn:.2f}"))
                    self._prom_tabla.setItem(r, 12, QTableWidgetItem(f"{go:.2f}"))
                except: pass
            
            # Actualizar totales (como pollo)
            cm = getattr(self, '_costo_maple', 0.0)
            ch = getattr(self, '_costo_huevo', 0.0)
            self._lbl_totales.setText(
                f'<span style="color: #E11D48;">Costo Maple: ${cm:,.2f} | Costo Huevo: ${ch:,.2f}</span>'
                f'&nbsp;&nbsp;&nbsp;&nbsp;||&nbsp;&nbsp;&nbsp;&nbsp;'
                f'<span style="color: #10B981;">Normal =&gt; Venta: ${t_vn:,.2f} | Ganancia: ${t_gn:,.2f}</span>'
                f'&nbsp;&nbsp;&nbsp;&nbsp;||&nbsp;&nbsp;&nbsp;&nbsp;'
                f'<span style="color: #3B82F6;">Mayoreo =&gt; Venta: ${t_vo:,.2f} | Ganancia: ${t_go:,.2f}</span>'
            )
            
        finally:
            self._prom_tabla.blockSignals(False)
            self._is_updating = False
    
    def _sync_calc_huevo(self):
        """Calcula automáticamente los costos al cambiar el precio del cajón"""
        try:
            from .motor_huevo import MotorHuevo
            
            precio_cajon = float(self._input_precio_cajon.text().replace(',', '.') or 0)
            
            if precio_cajon > 0:
                # Estructura: 1 cajón = 12 maples, 1 maple = 30 huevos
                costo_maple, costo_huevo, total_huevos = MotorHuevo.calcular_costo_cajon(precio_cajon)
                
                self._lbl_costo_maple.setText(f"${costo_maple:.2f}")
                self._lbl_costo_huevo.setText(f"${costo_huevo:.2f}")
                
                # Guardar costo del maple para cálculos de tabla
                self._costo_maple = costo_maple
                
                # Recalcular tabla automáticamente
                self._on_tabla_changed(None, from_calc=True)
                
        except Exception as e:
            print(f"Error en sync_calc_huevo: {e}")
    
    def _load_defaults(self):
        """Carga las filas por defecto para huevo (maples de venta)"""
        self._prom_tabla.blockSignals(True)
        self._prom_tabla.setRowCount(0)
        
        # Maples de venta: 30, 15, 10, 6 huevos
        maples_venta = [
            ("Maple 30 huevos", 30),
            ("Maple 15 huevos", 15),
            ("Maple 10 huevos", 10),
            ("Maple 6 huevos", 6)
        ]
        
        for i, (nombre, huevos) in enumerate(maples_venta):
            self._prom_tabla.insertRow(i)
            self._prom_tabla.setItem(i, 0, QTableWidgetItem(nombre))
            self._prom_tabla.setItem(i, 1, QTableWidgetItem(str(huevos)))
            for col in range(2, 12):
                val = "0.00" if col in [3, 5, 9, 10, 11] else ""
                it = QTableWidgetItem(val)
                if col in [2, 8, 9, 10, 11]:
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._prom_tabla.setItem(i, col, it)
        
        self._prom_tabla.blockSignals(False)
        self._sync_calc_huevo()
    
    def _on_tabla_changed(self, item, from_calc=False):
        """Calcula automáticamente precios, ganancias y mayoreo (como pollo)"""
        if getattr(self, '_is_updating', False): return
        self._prom_tabla.blockSignals(True)
        self._is_updating = True
        try:
            if not hasattr(self, '_costo_maple'):
                self._costo_maple = 0.0
            
            c_ed = item.column() if item else -1
            r_ed = item.row() if item else -1
            
            # Normalizar entrada
            if item and c_ed in [3, 4, 5, 7]:
                t = item.text().replace(',', '.')
                ct = ''.join(c for c in t if c.isdigit() or c in '.-')
                if ct != t: item.setText(ct)
            
            t_vn = 0.0
            t_gn = 0.0
            t_vo = 0.0
            t_go = 0.0
            
            for r in range(self._prom_tabla.rowCount()):
                try:
                    item_huevos = self._prom_tabla.item(r, 1)
                    huevos = int(item_huevos.text() or 0) if item_huevos else 0
                    
                    # Costo proporcional del maple según cantidad de huevos
                    costo_proporcion = self._costo_maple * (huevos / 30) if self._costo_maple > 0 else 0.0
                    self._prom_tabla.setItem(r, 2, QTableWidgetItem(f"{costo_proporcion:.2f}"))
                    
                    pv = float(self._prom_tabla.item(r, 3).text() or 0)
                    pg = float(self._prom_tabla.item(r, 4).text() or 0)
                    pm = float(self._prom_tabla.item(r, 5).text() or 0)
                    pmg = float(self._prom_tabla.item(r, 7).text() or 0)
                    
                    if costo_proporcion > 0:
                        # Recalcular % ganancia si se editó precio venta
                        if c_ed == 4 and r == r_ed:
                            pg = ((pv / costo_proporcion) - 1) * 100 if pv > 0 else 0.0
                            self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{pg:.2f}"))
                        # Recalcular precio venta si se editó % ganancia
                        elif c_ed == 4:
                            pv = costo_proporcion * (1 + pg / 100)
                            self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pv:.2f}"))
                        
                        # Recalcular % mayoreo si se editó precio mayoreo
                        if c_ed == 7 and r == r_ed:
                            pmg = ((pm / costo_proporcion) - 1) * 100 if pm > 0 else 0.0
                            self._prom_tabla.setItem(r, 7, QTableWidgetItem(f"{pmg:.2f}"))
                        # Recalcular precio mayoreo si se editó % mayoreo
                        elif c_ed == 7:
                            pm = costo_proporcion * (1 + pmg / 100)
                            self._prom_tabla.setItem(r, 5, QTableWidgetItem(f"{pm:.2f}"))
                    else:
                        if from_calc:
                            pg = 0.0
                            pmg = 0.0
                            self._prom_tabla.setItem(r, 4, QTableWidgetItem("0.00"))
                            self._prom_tabla.setItem(r, 7, QTableWidgetItem("0.00"))
                    
                    # Cálculos de totales
                    v_costo = costo_proporcion
                    if pv > 0:
                        vn = pv
                        gn = vn - v_costo
                    else:
                        vn = 0.0
                        gn = 0.0
                    t_vn += vn
                    t_gn += gn
                    
                    if pm > 0:
                        vo = pm
                        go = vo - v_costo
                    else:
                        vo = 0.0
                        go = 0.0
                    t_vo += vo
                    t_go += go
                    
                    self._prom_tabla.setItem(r, 8, QTableWidgetItem(f"{v_costo:.2f}"))
                    self._prom_tabla.setItem(r, 9, QTableWidgetItem(f"{vn:.2f}"))
                    self._prom_tabla.setItem(r, 10, QTableWidgetItem(f"{vo:.2f}"))
                    self._prom_tabla.setItem(r, 11, QTableWidgetItem(f"{gn:.2f}"))
                    self._prom_tabla.setItem(r, 12, QTableWidgetItem(f"{go:.2f}"))
                except: pass
            
            # Actualizar totales
            self._lbl_totales.setText(
                f'<span style="color: #10B981;">Normal =&gt; Venta: ${t_vn:,.2f} | Ganancia: ${t_gn:,.2f}</span>'
                f'&nbsp;&nbsp;&nbsp;&nbsp;||&nbsp;&nbsp;&nbsp;&nbsp;'
                f'<span style="color: #3B82F6;">Mayoreo =&gt; Venta: ${t_vo:,.2f} | Ganancia: ${t_go:,.2f}</span>'
            )
            
        finally:
            self._prom_tabla.blockSignals(False)
            self._is_updating = False
    
    def _cargar_filas_defecto(self):
        """Carga las filas por defecto para huevo (maples de venta)"""
        # Maples de venta: 30, 15, 10, 6 huevos
        maples_venta = [
            ("Maple 30 huevos", 30),
            ("Maple 15 huevos", 15),
            ("Maple 10 huevos", 10),
            ("Maple 6 huevos", 6)
        ]
        
        self._prom_tabla.setRowCount(len(maples_venta))
        
        for i, (nombre, huevos) in enumerate(maples_venta):
            self._prom_tabla.setItem(i, 0, QTableWidgetItem(nombre))
            self._prom_tabla.setItem(i, 1, QTableWidgetItem(str(huevos)))
            self._prom_tabla.setItem(i, 2, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 3, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 4, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 5, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 6, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 7, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 8, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 9, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 10, QTableWidgetItem("0"))
            self._prom_tabla.setItem(i, 11, QTableWidgetItem("0"))
    
    def _calcular_costos(self):
        """Calcula el costo por maple, huevo y docena (ahora es automático al cambiar precio cajón)"""
        # Ya es automático, solo actualiza cálculos
        self._sync_calc_huevo()
    
    def _obtener_precio_inventario(self):
        """Obtiene los precios actuales de inventario para huevo"""
        try:
            from .motor_huevo import MotorHuevo
            from src.base_de_datos.database import DatabaseManager
            
            db = DatabaseManager()
            
            # Nombres de productos de huevo en inventario
            tipos_huevo = [
                "Huevo XL",
                "Huevo L",
                "Huevo M",
                "Huevo S",
                "Huevo J",
                "Blanco"
            ]
            
            precios = MotorHuevo.obtener_precios_inventario(db, tipos_huevo)
            
            # Mostrar precios en un dialogo
            msg = "Precios actuales en inventario:\n\n"
            for tipo, precio in precios.items():
                msg += f"{tipo}: ${precio:.2f}\n"
            
            QMessageBox.information(self, "Precios de Inventario", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error obteniendo precios: {e}")
    
    def _repartir_precios(self):
        """Reparte los precios basándose en el % de ganancia"""
        # Ya es automático al editar % ganancia
        pass
    
    def _guardar_historial(self):
        """Guarda el estado actual en el historial"""
        try:
            from src.jefe.promedios.motor_global_promedios import MotorPromedios
            from src.base_de_datos.database import DatabaseManager
            
            db = DatabaseManager()
            estado = self.get_state()
            
            exito = MotorPromedios.guardar_historial(
                db, self._tipo_promedio, estado,
                self._input_proveedor.text(),
                self._input_fecha.date().toString("yyyy-MM-dd")
            )
            
            if exito:
                QMessageBox.information(self, "Guardado", "Historial guardado exitosamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo guardar el historial.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando historial: {e}")
    
    def get_state(self):
        """Retorna el estado actual para sincronización"""
        filas = []
        for i in range(self._prom_tabla.rowCount()):
            fila = []
            for j in range(self._prom_tabla.columnCount()):
                item = self._prom_tabla.item(i, j)
                fila.append(item.text() if item else "0")
            filas.append(fila)
        
        return {
            "precio_cajon": self._input_precio_cajon.text(),
            "costo_maple": self._lbl_costo_maple.text(),
            "costo_huevo": self._lbl_costo_huevo.text(),
            "filas": filas
        }
    
    def redondear(self):
        """Redondea precios a múltiplos de 10"""
        for i in range(self._prom_tabla.rowCount()):
            item_precio = self._prom_tabla.item(i, 3)
            if item_precio:
                precio = float(item_precio.text().replace(',', '.') or 0)
                precio_redondeado = round(precio / 10) * 10
                self._prom_tabla.setItem(i, 3, QTableWidgetItem(f"{precio_redondeado:.2f}"))
