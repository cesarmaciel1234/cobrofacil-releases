import codecs
import re
import os

with codecs.open('src/jefe/contabilidad/jefe_contabilidad.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Define boundaries
boundaries = [
    ("vista_resumen", r"    def _build_tab_resumen\(self\):.*?(?=    def _build_tab_ingresos\(self\):)"),
    ("vista_ingresos", r"    def _build_tab_ingresos\(self\):.*?(?=    def _build_tab_gastos\(self\):)"),
    ("vista_gastos", r"    def _build_tab_gastos\(self\):.*?(?=    def _build_tab_proveedores\(self\):)"),
    ("vista_proveedores", r"    def _build_tab_proveedores\(self\):.*?(?=    def _build_tab_prestamos\(self\):)"),
    ("vista_prestamos", r"    def _build_tab_prestamos\(self\):.*?(?=    def _build_tab_cheques\(self\):)"),
    ("vista_cheques", r"    def _build_tab_cheques\(self\):.*?(?=    def _build_tab_tarjetas\(self\):)"),
    ("vista_tarjetas", r"    def _build_tab_tarjetas\(self\):.*?(?=    def _build_tab_inversiones\(self\):)"),
    ("vista_inversiones", r"    def _build_tab_inversiones\(self\):.*?(?=    def _build_tab_costos_fijos\(self\):)"),
    ("vista_costos_fijos", r"    def _build_tab_costos_fijos\(self\):.*?(?=    def _build_tab_historial\(self\):)"),
    ("vista_historial", r"    def _build_tab_historial\(self\):.*?(?=    def _build_tab_promedios\(self\):)"),
    ("vista_promedios", r"    def _build_tab_promedios\(self\):.*?(?=    def _build_tab_reportes\(self\):)"),
    ("vista_reportes", r"    def _build_tab_reportes\(self\):.*")
]

# The imports needed for every mixin (so linters/IDEs don't complain, though strictly not needed for mixins if they don't import, but many use QTableWidget etc)
# Actually, mixins don't strictly need imports if they rely on the parent class, but it's cleaner to include PyQt imports
header = """from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import datetime
from src.jefe.contabilidad.styles import PAL, modern_btn, apply_table_style, modern_input

"""

mixin_classes = []

for name, pattern in boundaries:
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(0)
        
        # Remove it from the main text
        text = text.replace(content, "")
        
        # Write to mixin file
        class_name = ''.join(word.capitalize() for word in name.split('_')) + 'Mixin'
        mixin_classes.append((name, class_name))
        
        with codecs.open(f'src/jefe/contabilidad/{name}.py', 'w', encoding='utf-8') as mf:
            mf.write(header)
            mf.write(f"class {class_name}:\n")
            mf.write(content)

# Now rewrite jefe_contabilidad.py with the mixin inheritances
# Import the mixins at the top
import_lines = ""
inheritance = ""
for name, class_name in mixin_classes:
    import_lines += f"from src.jefe.contabilidad.{name} import {class_name}\n"
    inheritance += f", {class_name}"

text = text.replace("class JefeContabilidad(QWidget):", import_lines + f"\nclass JefeContabilidad(QWidget{inheritance}):")

with codecs.open('src/jefe/contabilidad/jefe_contabilidad.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Modularization complete!")
