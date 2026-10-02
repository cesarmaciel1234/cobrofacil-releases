import os

files = [
    'src/jefe/promedios/carne/ui_carne.py',
    'src/jefe/promedios/cerdo/ui_cerdo.py',
    'src/jefe/promedios/pollo/ui_pollo.py'
]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    old_block = '''                    if self._costo_real_kg > 0:
                        if c_ed == 3 and r == r_ed:
                            pg = ((pv / self._costo_real_kg) - 1) * 100
                            self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{pg:.2f}"))
                        elif (c_ed == 4 and r == r_ed) or from_calc:
                            pv = self._costo_real_kg * (1 + pg / 100)
                            self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pv:,.2f}"))
                        
                        if c_ed == 5 and r == r_ed:
                            pmg = ((pm / self._costo_real_kg) - 1) * 100
                            self._prom_tabla.setItem(r, 7, QTableWidgetItem(f"{pmg:.2f}"))
                        elif (c_ed == 7 and r == r_ed) or from_calc:
                            pm = self._costo_real_kg * (1 + pmg / 100)
                            self._prom_tabla.setItem(r, 5, QTableWidgetItem(f"{pm:,.2f}"))
                    else:
                        if from_calc:
                            pv = 0.0; pm = 0.0
                            self._prom_tabla.setItem(r, 3, QTableWidgetItem("0.00"))
                            self._prom_tabla.setItem(r, 5, QTableWidgetItem("0.00"))'''

    new_block = '''                    if self._costo_real_kg > 0:
                        if c_ed == 4 and r == r_ed:
                            pv = self._costo_real_kg * (1 + pg / 100)
                            self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pv:,.2f}"))
                        else:
                            pg = ((pv / self._costo_real_kg) - 1) * 100 if pv > 0 else 0.0
                            self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{pg:.2f}"))
                        
                        if c_ed == 7 and r == r_ed:
                            pm = self._costo_real_kg * (1 + pmg / 100)
                            self._prom_tabla.setItem(r, 5, QTableWidgetItem(f"{pm:,.2f}"))
                        else:
                            pmg = ((pm / self._costo_real_kg) - 1) * 100 if pm > 0 else 0.0
                            self._prom_tabla.setItem(r, 7, QTableWidgetItem(f"{pmg:.2f}"))
                    else:
                        if from_calc:
                            # Do not clear pv or pm if they manually loaded them.
                            # Just set the percentages to 0 since we can't calculate margin.
                            pg = 0.0
                            pmg = 0.0
                            self._prom_tabla.setItem(r, 4, QTableWidgetItem("0.00"))
                            self._prom_tabla.setItem(r, 7, QTableWidgetItem("0.00"))'''

    content = content.replace(old_block, new_block)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

print('Updated UI logic')
