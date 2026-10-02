import re
file_path = 'src/contabilidad/jefe_contabilidad.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Remove month/year combo imports and logic
imports_pattern = r'QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDateEdit,'
text = text.replace(imports_pattern, 'QTableWidgetItem, QHeaderView, QLineEdit, QDateEdit,')

# Find the header construction
header_pattern = r'# Selector mes/ao(.*?)lay\.addWidget\(self\._year_sel\)'
def header_repl(match):
    return '''# Selector de Período (Botonera)
        from src.jefe.reportes.periodo import montar_botones_periodo, resolver_rango_periodo, pintar_activo
        
        self.period_buttons = montar_botones_periodo(
            lay, 
            self.cargar_datos_periodo,
            "background: transparent; color: #64748B; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 12px; font-weight: 500;",
            "background: #1E293B; color: #FFFFFF; border: none; border-radius: 6px; padding: 6px 12px; font-weight: 600;"
        )
        self.current_period = "Mes Actual"'''

# Careful with the encoding matching of ao. I will just replace the explicit lines:
lines = text.split('\n')
new_lines = []
skip = False
for line in lines:
    if '# Selector mes/a' in line or '# Selector mes/año' in line:
        skip = True
        new_lines.append('''        # Selector de Período (Botonera)
        from src.jefe.reportes.periodo import montar_botones_periodo, resolver_rango_periodo, pintar_activo
        self.current_period = "Mes Actual"
        self._desde, self._hasta = None, None
        
        self.period_buttons = montar_botones_periodo(
            lay, 
            self.cargar_datos_periodo,
            "background: transparent; color: #64748B; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 12px; font-weight: 500;",
            "background: #1E293B; color: #FFFFFF; border: none; border-radius: 6px; padding: 6px 12px; font-weight: 600;"
        )
''')
        continue
    if skip and 'lay.addWidget(self._year_sel)' in line:
        skip = False
        continue
    if skip:
        continue
    
    # Also skip connecting events
    if 'self._month_sel.currentIndexChanged.connect' in line or 'self._year_sel.currentIndexChanged.connect' in line:
        continue
        
    if 'def _mes(self):' in line:
        skip = True
        continue
    if skip and 'def _a' in line and '(self):' in line:
        pass
    if skip and 'return int(self._year_sel.currentText())' in line:
        skip = False
        continue
        
    new_lines.append(line)

text = '\n'.join(new_lines)

text += '''

    def cargar_datos_periodo(self, periodo="Mes Actual"):
        from src.jefe.reportes.periodo import resolver_rango_periodo, pintar_activo
        self.current_period = periodo
        rango = resolver_rango_periodo(periodo, self)
        if not rango: return
        
        self._desde, self._hasta, etiqueta = rango
        
        # Actualizar UI botonera
        pintar_activo(
            self.period_buttons, 
            periodo, 
            "background: #1E293B; color: #FFFFFF; border: none; border-radius: 6px; padding: 6px 12px; font-weight: 600;",
            "background: transparent; color: #64748B; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 12px; font-weight: 500;",
            etiqueta
        )
        
        self._reload_current_tab()

    @property
    def _mes(self): return None
    @property
    def _año(self): return None
'''

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

# We also need to update vista_resumen to use self.parent()._desde and self.parent()._hasta
with open('src/contabilidad/vista_resumen.py', 'r', encoding='utf-8') as f:
    res = f.read()
    
res = res.replace('self._db.get_stats(self._mes, self._ao)', 'self._db.get_stats(self.parent()._desde, self.parent()._hasta)')
res = res.replace('self._db.get_stats(self._mes, self._año)', 'self._db.get_stats(self.parent()._desde, self.parent()._hasta)')
res = res.replace('self._db.get_all_movements(self._mes, self._ao)', 'self._db.get_all_movements(self.parent()._desde, self.parent()._hasta)')
res = res.replace('self._db.get_all_movements(self._mes, self._año)', 'self._db.get_all_movements(self.parent()._desde, self.parent()._hasta)')

with open('src/contabilidad/vista_resumen.py', 'w', encoding='utf-8') as f:
    f.write(res)
    
print("Patch jefe_contabilidad applied")
