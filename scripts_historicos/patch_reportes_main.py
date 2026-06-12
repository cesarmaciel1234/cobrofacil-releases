import codecs
import re

with codecs.open('src/jefe/reportes/reportes_main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the setup_historial_ui function body
# We want to replace it entirely and just inject the VistaHistorial
match = re.search(r'(    def setup_historial_ui\(self\):.*?)(?=\n    def )', text, flags=re.DOTALL)
if match:
    new_setup = """    def setup_historial_ui(self):
        from src.jefe.reportes.vista_historial import VistaHistorial
        self.tab_historial = VistaHistorial(self)
        self.stack_views.addWidget(self.tab_historial)
"""
    text = text.replace(match.group(1), new_setup)

# Remove the old _cargar_historial_tickets and _cargar_historial_pagina
match2 = re.search(r'(    def _cargar_historial_tickets\(self\):.*?)(?=\n    def _update_tab_buttons)', text, flags=re.DOTALL)
if match2:
    text = text.replace(match2.group(1), "")

# Let's also check if there is an _on_hist_scroll that needs removal
match3 = re.search(r'(    def _on_hist_scroll\(self.*?:.*?)(?=\n    def )', text, flags=re.DOTALL)
if match3:
    text = text.replace(match3.group(1), "")

with codecs.open('src/jefe/reportes/reportes_main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patched reportes_main.py")
