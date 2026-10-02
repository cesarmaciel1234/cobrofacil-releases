# -*- coding: utf-8 -*-
import re

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Clean duplication
index = content.find('from PyQt6.QtWidgets import *', 100)
if index > 0:
    content = content[index:]

# 2. Fix the columns
content = content.replace(
    'self._prom_tabla = build_table(["Corte", "Kilos", "Costo $/kg", "% Ganancia", "Precio/kg Venta", "P. mayoreo", "Cant. may.", "Venta Total", "Ganancia Neta"])',
    'self._prom_tabla = build_table(["Corte", "Kilos", "Costo $/kg", "% Ganancia", "Precio Venta", "P. Mayoreo", "C. May.", "V. Total", "Ganancia", "V. Tot. May.", "Gan. May."])'
)

# 3. Add Repartir button
def repl_layout(m):
    return '''        lbl_kilos = QLabel("Kilos:")
        lbl_merma = QLabel("Merma:")
        lbl_precio = QLabel("Precio/kg:")
        self._lbl_costo_tot = QLabel("Costo Total:")
        for lbl in [lbl_kilos, lbl_merma, lbl_precio, self._lbl_costo_tot]:
            lbl.setStyleSheet("QLabel { color: #0F172A; font-weight: bold; }")

        self._btn_repartir_kilos = btn_primary("Repartir")
        self._btn_repartir_kilos.setToolTip("Autocompletar Kilos en tabla proporcionalmente al total ingresado")
        self._btn_repartir_kilos.clicked.connect(self._repartir_kilos)

        m_lay.addWidget(lbl_kilos)
        m_lay.addWidget(self._prom_kilos)
        m_lay.addWidget(self._btn_repartir_kilos)
        m_lay.addWidget(lbl_merma)'''

content = re.sub(
    r'        lbl_kilos = QLabel\("Kilos:"\).*?m_lay\.addWidget\(lbl_merma\)',
    repl_layout,
    content,
    flags=re.DOTALL
)

# 4. Add _repartir_kilos logic
def repl_func(m):
    return '''    def _repartir_kilos(self):
        try:
            kilos_totales = float(self._prom_kilos.text().replace(',', '.') or 0)
            if kilos_totales <= 0: return

            from src.jefe.promedios.promedio_motor.res import PromedioRes, PromedioMocho, PromedioPecho
            from src.jefe.promedios.promedio_motor.cerdo import PromedioCerdo
            from src.jefe.promedios.promedio_motor.pollo import PromedioPollo

            cortes = []
            if self._tipo_promedio == "Carne_MediaRes": cortes = PromedioRes.get_cortes()
            elif self._tipo_promedio == "Carne_Mocho": cortes = PromedioMocho.get_cortes()
            elif self._tipo_promedio == "Carne_Pecho": cortes = PromedioPecho.get_cortes()
            elif self._tipo_promedio == "Cerdo": cortes = PromedioCerdo.get_cortes()
            elif self._tipo_promedio == "Pollo": cortes = PromedioPollo.get_cortes()
            
            if not cortes: return
            
            suma_default = sum(k for c, k, p in cortes)
            if suma_default <= 0: return

            self._prom_tabla.blockSignals(True)
            for r in range(min(len(cortes), self._prom_tabla.rowCount())):
                _corte, k_def, _pct = cortes[r]
                k_nuevo = (k_def / suma_default) * kilos_totales
                self._prom_tabla.setItem(r, 1, QTableWidgetItem(f"{k_nuevo:.2f}"))
            self._prom_tabla.blockSignals(False)
            self._calc_media_res(quiet=True, from_calc=True)
        except Exception: pass

    def _sync_costo_total_from_precio(self):'''

content = re.sub(
    r'    def _sync_costo_total_from_precio\(self\):',
    repl_func,
    content
)

# 5. Fix _on_prom_tabla_changed math
def repl_logic(m):
    return '''                oferta_str = self._prom_tabla.item(r, 5).text().replace(',','').strip()
                cant_may_str = self._prom_tabla.item(r, 6).text().replace(',','').strip()
                precio_oferta_kg = 0.0
                tiene_oferta = False

                if oferta_str and cant_may_str:
                    try:
                        p_mayoreo = float(oferta_str)
                        c_may = float(cant_may_str)
                        if p_mayoreo > 0 and c_may > 0:
                            precio_oferta_kg = p_mayoreo / c_may
                            tiene_oferta = True
                    except: pass

                it_venta = self._prom_tabla.item(r, 4)
                if tiene_oferta:
                    it_venta.setFont(font_strike)
                    it_venta.setForeground(QColor("#94A3B8"))
                else:
                    it_venta.setFont(font_normal)
                    it_venta.setForeground(QColor(PAL['text']))

                costo_tot = kilos * self._costo_real_kg

                # Normal Scenario
                venta_n = kilos * precio_venta_base
                gan_n = venta_n - costo_tot
                t_venta_normal += venta_n
                t_ganancia_normal += gan_n

                # Offer Scenario
                venta_o = kilos * (precio_oferta_kg if tiene_oferta else precio_venta_base)
                gan_o = venta_o - costo_tot
                t_venta_oferta += venta_o
                t_ganancia_oferta += gan_o

                self._prom_tabla.setItem(r, 2, QTableWidgetItem(f"{self._costo_real_kg:,.2f}"))

                # Update row UI to show normal
                vi = QTableWidgetItem(f"{venta_n:,.2f}")
                vi.setForeground(QColor(PAL['success'] if gan_n >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 7, vi)

                gi = QTableWidgetItem(f"{gan_n:,.2f}")
                gi.setForeground(QColor(PAL['success'] if gan_n >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 8, gi)

                # Update row UI to show mayoreo
                vi_m = QTableWidgetItem(f"{venta_o:,.2f}")
                vi_m.setForeground(QColor(PAL['success'] if gan_o >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 9, vi_m)

                gi_m = QTableWidgetItem(f"{gan_o:,.2f}")
                gi_m.setForeground(QColor(PAL['success'] if gan_o >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 10, gi_m)

                suma_kilos_cortes += kilos'''

content = re.sub(
    r'                oferta_str = self\._prom_tabla\.item\(r, 5\)\.text\(\)\.replace.*?suma_kilos_cortes \+= kilos',
    repl_logic,
    content,
    flags=re.DOTALL
)

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'w', encoding='utf-8') as f:
    f.write(content)
