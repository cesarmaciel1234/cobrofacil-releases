import os
import json
import math
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from src.contabilidad.shared_globals import PAL, btn_primary, build_table
from .motor_carne import MotorCarne, ColumnasCarne
from src.utils.parser import parse_float_regional
from src.jefe.promedios.motor_global_promedios import MotorPromedios
from src.base_de_datos.database import DatabaseManager

class UICarne(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tipo_promedio = "Carne"
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
            "kilos": self._prom_kilos.text(),
            "merma": self._prom_merma.text(),
            "precio": self._prom_precio.text(),
            "costo_total": self._prom_costo_total.text(),
            "filas": filas
        }

    def set_state(self, estado):
        self._prom_tabla.blockSignals(True)
        self._prom_kilos.setText(estado.get("kilos", ""))
        self._prom_merma.setText(estado.get("merma", ""))
        self._prom_precio.blockSignals(True)
        self._prom_costo_total.blockSignals(True)
        self._prom_precio.setText(estado.get("precio", ""))
        self._prom_costo_total.setText(estado.get("costo_total", ""))
        self._prom_precio.blockSignals(False)
        self._prom_costo_total.blockSignals(False)
        
        filas = estado.get("filas", [])
        self._prom_tabla.setRowCount(0)
        for i, row_data in enumerate(filas):
            self._prom_tabla.insertRow(i)
            for col in range(13):
                val = str(row_data[col]) if col < len(row_data) else "0.00"
                it = QTableWidgetItem(val)
                if col in [ColumnasCarne.COSTO, ColumnasCarne.VALOR_COSTO, ColumnasCarne.VENTA_NORMAL, ColumnasCarne.VENTA_MAYOREO, ColumnasCarne.GANANCIA_N, ColumnasCarne.GANANCIA_M]:
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if col == ColumnasCarne.COSTO: it.setForeground(QColor(PAL['text3']))
                self._prom_tabla.setItem(i, col, it)
        self._add_empty_row()
        self._prom_tabla.blockSignals(False)
        self._sync_calc()

    def redondear(self):
        if not hasattr(self, '_costo_real_kg') or self._costo_real_kg == 0: return
        self._prom_tabla.blockSignals(True)
        for r in range(self._prom_tabla.rowCount()):
            try:
                precio_actual = float(self._prom_tabla.item(r, 3).text().replace(',', ''))
                if precio_actual > 0:
                    redondeado = math.ceil(precio_actual / 500) * 500
                    self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{redondeado:,.2f}"))
            except ValueError: pass
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
                            "kilos": str(r.get('kilos', '')),
                            "precio": str(r.get('precio', '')),
                            "filas": r.get('filas', [])
                        }
                        # El input proveedor y fecha
                        self._input_proveedor.setText(r.get('proveedor', ''))
                        self.set_state(estado)
                    except ValueError: pass
                    break

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        
        
        self.sub_tabs_lay = QHBoxLayout()
        self.sub_tabs_lay.setContentsMargins(0, 0, 0, 10)
        self.btn_media_res = QPushButton("🥩 Media Res")
        self.btn_mocho = QPushButton("🥩 Mocho")
        self.btn_pecho = QPushButton("🥩 Pecho")
        for b in [self.btn_media_res, self.btn_mocho, self.btn_pecho]:
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self.sub_tabs_lay.addWidget(b)
        self.sub_tabs_lay.addStretch()
        
        self.btn_media_res.clicked.connect(lambda: self._switch_sub_tab("Media Res"))
        self.btn_mocho.clicked.connect(lambda: self._switch_sub_tab("Mocho"))
        self.btn_pecho.clicked.connect(lambda: self._switch_sub_tab("Pecho"))
        lay.addLayout(self.sub_tabs_lay)
        

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

        r2_lay = QHBoxLayout()
        lbl_kilos = QLabel("Kilos:")
        self._prom_kilos = QLineEdit()
        self._prom_kilos.setFixedWidth(100)
        
        self._btn_repartir = btn_primary("Repartir")
        self._btn_repartir.clicked.connect(self._repartir_kilos)
        
        lbl_merma = QLabel("Merma:")
        self._prom_merma = QLineEdit()
        self._prom_merma.setFixedWidth(100)
        self._prom_merma.setReadOnly(True)
        
        lbl_precio = QLabel("Precio/kg:")
        self._prom_precio = QLineEdit()
        self._prom_precio.setFixedWidth(100)
        
        lbl_costo_tot = QLabel("Costo Total ($):")
        self._prom_costo_total = QLineEdit()
        self._prom_costo_total.setFixedWidth(120)
        
        self.btn_calc_base = btn_primary("⚙ Calcular Costo Base")
        
        for lbl in [lbl_kilos, lbl_merma, lbl_precio, lbl_costo_tot]:
            lbl.setStyleSheet("color: #0F172A; font-weight: bold;")
            
        r2_lay.addWidget(lbl_kilos)
        r2_lay.addWidget(self._prom_kilos)
        r2_lay.addWidget(self._btn_repartir)
        r2_lay.addWidget(lbl_merma)
        r2_lay.addWidget(self._prom_merma)
        r2_lay.addWidget(lbl_precio)
        r2_lay.addWidget(self._prom_precio)
        r2_lay.addWidget(lbl_costo_tot)
        r2_lay.addWidget(self._prom_costo_total)
        r2_lay.addStretch()
        r2_lay.addWidget(self.btn_calc_base)
        lay.addLayout(r2_lay)



        # 13 COLUMNS
        self._prom_tabla = build_table([
            "Corte", "Kilos", "Costo $/kg", "Precio Venta", "% Ganancia", 
            "P. Mayoreo", "Desde kg", "% Mayoreo", "V. Costo", "V. Total", "V. Mayoreo", "Ganancia", "G. Mayoreo"
        ])
        self._prom_tabla.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed | QAbstractItemView.EditTrigger.AnyKeyPressed)
        self._prom_tabla.itemChanged.connect(self._on_tabla_changed)
        lay.addWidget(self._prom_tabla)

        # Single Line Footer
        self._lbl_totales = QLabel()
        self._lbl_totales.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_totales.setStyleSheet(f"font-size: 15px; font-weight: 800; margin-top: 10px;")
        lay.addWidget(self._lbl_totales)

        self._prom_kilos.textChanged.connect(self._sync_calc)
        self._prom_precio.textChanged.connect(self._sync_costo_total)
        self._prom_costo_total.textChanged.connect(self._sync_precio)
        
        self._switch_sub_tab("Media Res")

    
    def _switch_sub_tab(self, sub_tab):
        self._sub_tipo = sub_tab
        active = f"QPushButton {{ background: {PAL['primary']}; color: white; border-radius: 8px; padding: 6px 12px; font-weight: bold; }}"
        inactive = "QPushButton { background: #E2E8F0; color: #0F172A; border: 1px solid #94A3B8; border-radius: 8px; padding: 6px 12px; font-weight: bold; }"
        self.btn_media_res.setStyleSheet(active if sub_tab == "Media Res" else inactive)
        self.btn_mocho.setStyleSheet(active if sub_tab == "Mocho" else inactive)
        self.btn_pecho.setStyleSheet(active if sub_tab == "Pecho" else inactive)
        self._load_defaults()
    

    def _sync_costo_total(self):
        if self._prom_costo_total.signalsBlocked(): return
        try:
            k = parse_float_regional(self._prom_kilos.text())
            p = parse_float_regional(self._prom_precio.text())
            if k > 0:
                self._prom_costo_total.blockSignals(True)
                self._prom_costo_total.setText(f"{k*p:.2f}")
                self._prom_costo_total.blockSignals(False)
        except ValueError: pass
        self._sync_calc()

    def _sync_precio(self):
        if self._prom_precio.signalsBlocked(): return
        try:
            k = parse_float_regional(self._prom_kilos.text())
            ct = parse_float_regional(self._prom_costo_total.text())
            if k > 0:
                self._prom_precio.blockSignals(True)
                self._prom_precio.setText(f"{ct/k:.2f}")
                self._prom_precio.blockSignals(False)
        except ValueError: pass
        self._sync_calc()

    def _load_defaults(self):
        self._prom_tabla.blockSignals(True)
        self._prom_tabla.setRowCount(0)
        cortes = MotorCarne.get_cortes(self._sub_tipo)
        for i, (corte, kilos) in enumerate(cortes):
            self._prom_tabla.insertRow(i)
            self._prom_tabla.setItem(i, ColumnasCarne.CORTE, QTableWidgetItem(corte))
            self._prom_tabla.setItem(i, ColumnasCarne.KILOS, QTableWidgetItem(str(kilos)))
            for col in range(ColumnasCarne.COSTO, ColumnasCarne.GANANCIA_M + 1):
                it = QTableWidgetItem("0.00" if col != ColumnasCarne.VACIO_6 else "")
                if col in [ColumnasCarne.COSTO, ColumnasCarne.VALOR_COSTO, ColumnasCarne.VENTA_NORMAL, ColumnasCarne.VENTA_MAYOREO, ColumnasCarne.GANANCIA_N, ColumnasCarne.GANANCIA_M]:
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if col == ColumnasCarne.COSTO: it.setForeground(QColor(PAL['text3']))
                self._prom_tabla.setItem(i, col, it)
        
        self._add_empty_row()
        self._prom_tabla.blockSignals(False)
        self._sync_calc()

    def _add_empty_row(self):
        i = self._prom_tabla.rowCount()
        self._prom_tabla.insertRow(i)
        self._prom_tabla.setItem(i, ColumnasCarne.CORTE, QTableWidgetItem(""))
        self._prom_tabla.setItem(i, ColumnasCarne.KILOS, QTableWidgetItem(""))
        for col in range(ColumnasCarne.COSTO, ColumnasCarne.GANANCIA_M + 1):
            it = QTableWidgetItem("0.00" if col != ColumnasCarne.VACIO_6 else "")
            if col in [ColumnasCarne.COSTO, ColumnasCarne.VALOR_COSTO, ColumnasCarne.VENTA_NORMAL, ColumnasCarne.VENTA_MAYOREO, ColumnasCarne.GANANCIA_N, ColumnasCarne.GANANCIA_M]:
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == ColumnasCarne.COSTO: it.setForeground(QColor(PAL['text3']))
            self._prom_tabla.setItem(i, col, it)

    def _repartir_kilos(self):
        try:
            kt = parse_float_regional(self._prom_kilos.text())
            if kt <= 0: return
            cortes = MotorCarne.get_cortes(self._sub_tipo)
            if not cortes: return
            sd = sum(k for c, k in cortes)
            if sd <= 0: return
            
            self._prom_tabla.blockSignals(True)
            for r in range(min(len(cortes), self._prom_tabla.rowCount())):
                k_nuevo = (cortes[r][1] / sd) * kt
                self._prom_tabla.setItem(r, ColumnasCarne.KILOS, QTableWidgetItem(f"{k_nuevo:.2f}"))
            self._prom_tabla.blockSignals(False)
            self._sync_calc()
        except ValueError: pass

    def _sync_calc(self):
        kt = parse_float_regional(self._prom_kilos.text())
        pt = parse_float_regional(self._prom_precio.text())
        sk = 0.0
        for r in range(self._prom_tabla.rowCount()):
            try: sk += parse_float_regional(self._prom_tabla.item(r, ColumnasCarne.KILOS).text())
            except ValueError: pass
        
        merma = kt - sk
        k_utiles = kt - merma
        c_real = (kt * pt) / k_utiles if k_utiles > 0 else 0.0
        
        self._prom_merma.setText(f"{merma:.2f}")
        self._costo_real_kg = c_real
        self._kilos_utiles = k_utiles
        
        self._on_tabla_changed(None, from_calc=True)

    def _on_tabla_changed(self, item, from_calc=False):
        if getattr(self, '_is_updating', False): return
        self._prom_tabla.blockSignals(True)
        self._is_updating = True
        try:
            if not hasattr(self, '_costo_real_kg'): self._costo_real_kg = 0.0

            c_ed = item.column() if item else -1
            r_ed = item.row() if item else -1

            if item and c_ed in [ColumnasCarne.KILOS, ColumnasCarne.PV_KG, ColumnasCarne.MARGEN_V, ColumnasCarne.PM_KG, ColumnasCarne.VACIO_6, ColumnasCarne.MARGEN_M]:
                t = item.text()
                ct = ''.join(c for c in t if c.isdigit() or c in '.,-')
                if ct != t: item.setText(ct)

            if item and c_ed == ColumnasCarne.CORTE and r_ed == self._prom_tabla.rowCount() - 1 and item.text().strip():
                self._add_empty_row()
            if item and c_ed == ColumnasCarne.KILOS:
                self._is_updating = False
                self._prom_tabla.blockSignals(False)
                self._sync_calc()
                return

            # Extraer filas de la tabla
            filas = []
            for r in range(self._prom_tabla.rowCount()):
                fila = []
                for c in range(13):
                    it = self._prom_tabla.item(r, c)
                    fila.append(it.text() if it else "")
                filas.append(fila)

            # Obtener valor editado si aplica
            valor_editado = 0.0
            if item and c_ed != -1:
                try:
                    valor_editado = parse_float_regional(item.text())
                except ValueError:
                    pass

            # Llamar al motor para recalcular
            resultado = MotorCarne.recalcular_tabla(
                filas, self._costo_real_kg,
                col_editada=c_ed, fila_editada=r_ed,
                valor_editado=valor_editado, from_calc=from_calc
            )

            # Actualizar tabla con resultados
            for r, calc in enumerate(resultado["filas"]):
                self._prom_tabla.setItem(r, ColumnasCarne.COSTO, QTableWidgetItem(f"{self._costo_real_kg:,.2f}"))
                self._prom_tabla.setItem(r, ColumnasCarne.PV_KG, QTableWidgetItem(f"{calc['pv']:,.2f}"))
                self._prom_tabla.setItem(r, ColumnasCarne.MARGEN_V, QTableWidgetItem(f"{calc['pg']:.2f}"))
                self._prom_tabla.setItem(r, ColumnasCarne.PM_KG, QTableWidgetItem(f"{calc['pm']:,.2f}"))
                self._prom_tabla.setItem(r, ColumnasCarne.MARGEN_M, QTableWidgetItem(f"{calc['pmg']:.2f}"))
                self._prom_tabla.setItem(r, ColumnasCarne.VALOR_COSTO, QTableWidgetItem(f"{calc['v_costo']:,.2f}"))
                self._prom_tabla.setItem(r, ColumnasCarne.VENTA_NORMAL, QTableWidgetItem(f"{calc['vn']:,.2f}"))
                self._prom_tabla.setItem(r, ColumnasCarne.VENTA_MAYOREO, QTableWidgetItem(f"{calc['vo']:,.2f}"))
                self._prom_tabla.setItem(r, ColumnasCarne.GANANCIA_N, QTableWidgetItem(f"{calc['gn']:,.2f}"))
                self._prom_tabla.setItem(r, ColumnasCarne.GANANCIA_M, QTableWidgetItem(f"{calc['go']:,.2f}"))

            # Actualizar totales
            ku = getattr(self, '_kilos_utiles', 0.0)
            cr = getattr(self, '_costo_real_kg', 0.0)
            t = resultado["totales"]
            self._lbl_totales.setText(
                f'<span style="color: #E11D48;">Kilos útiles: {ku:.2f} kg | Costo real kg: ${cr:,.2f}</span>'
                f'&nbsp;&nbsp;&nbsp;&nbsp;||&nbsp;&nbsp;&nbsp;&nbsp;'
                f'<span style="color: #10B981;">Normal =&gt; Venta: ${t["vn"]:,.2f} | Ganancia: ${t["gn"]:,.2f}</span>'
                f'&nbsp;&nbsp;&nbsp;&nbsp;||&nbsp;&nbsp;&nbsp;&nbsp;'
                f'<span style="color: #3B82F6;">Mayoreo =&gt; Venta: ${t["vo"]:,.2f} | Ganancia: ${t["go"]:,.2f}</span>'
            )

        finally:
            self._prom_tabla.blockSignals(False)
            self._is_updating = False