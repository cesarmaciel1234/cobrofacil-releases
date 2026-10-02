import re

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'r', encoding='utf-8') as f:
    content = f.read()

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

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'w', encoding='utf-8') as f:
    f.write(content)
