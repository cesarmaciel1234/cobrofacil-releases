import codecs
import re

with codecs.open('src/admin/admin3_reportes.py', 'r', encoding='utf-8') as f:
    orig = f.read()

# --- VISTA FINANCIERO ---
vf = orig.replace('class Admin3Reportes(QWidget):', 'class VistaFinanciero(QWidget):')

# Remove the navbar logic from setup_ui
vf = re.sub(r'        # NAVBAR.*?main_layout\.addWidget\(header\)', '', vf, flags=re.DOTALL)

# Remove the stack_views and audit view injection at the end of setup_ui
vf = re.sub(r'        self\.stack_views = QStackedWidget\(\).*?self\.cargar_datos\(\)', '        main_layout.addWidget(scroll)\n        self.cargar_datos("Semana Actual")', vf, flags=re.DOTALL)

# Delete audit and history methods completely
vf = re.sub(r'    def setup_audit_ui\(self\):.*?(?=\n    def _limpiar_filtros_audit)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _limpiar_filtros_audit\(self\):.*?(?=\n    def _buscar_auditoria)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _buscar_auditoria\(self\):.*?(?=\n    def _load_more_audit_rows)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _load_more_audit_rows\(self\):.*?(?=\n    def _on_audit_scroll)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _on_audit_scroll\(self, value\):.*?(?=\n    def _calcular_comparativa)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def setup_historial_ui\(self\):.*?(?=\n    def _cargar_historial_tickets)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _cargar_historial_tickets\(self\):.*?(?=\n    def _cargar_historial_pagina)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _cargar_historial_pagina\(self\):.*?(?=\n    def _show_ventas_tab)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _show_ventas_tab\(self\):.*?(?=\n    def _show_auditoria_tab)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _show_auditoria_tab\(self\):.*?(?=\n    def _show_historial_tab)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _show_historial_tab\(self\):.*?(?=\n    def _update_tab_buttons)', '', vf, flags=re.DOTALL)
vf = re.sub(r'    def _update_tab_buttons\(self\):.*?(?=\n    def cargar_datos)', '', vf, flags=re.DOTALL)

with codecs.open('src/jefe/reportes/vista_financiero.py', 'w', encoding='utf-8') as f:
    f.write(vf)

# --- VISTA AUDITORIA ---
va = orig.replace('class Admin3Reportes(QWidget):', 'class VistaAuditoria(QWidget):')

# Replace setup_ui entirely to just load audit_ui
new_setup_ui = """    def setup_ui(self):
        self.setObjectName("VistaAuditoria")
        self.setStyleSheet("QWidget#VistaAuditoria { font-family: 'Segoe UI', sans-serif; background: transparent; }")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        self.audit_view = QWidget()
        main_layout.addWidget(self.audit_view)
        self.setup_audit_ui()
"""
va = re.sub(r'    def setup_ui\(self\):.*?(?=\n    def _update_tab_buttons)', new_setup_ui, va, flags=re.DOTALL)

# Clean up other methods
va = re.sub(r'    def _update_tab_buttons\(self\):.*?(?=\n    def cargar_datos)', '', va, flags=re.DOTALL)
va = re.sub(r'    def cargar_datos\(self, periodo="Mes Actual"\):.*?(?=\n    def _show_ventas_tab)', '', va, flags=re.DOTALL)
va = re.sub(r'    def _show_ventas_tab\(self\):.*?(?=\n    def setup_audit_ui)', '', va, flags=re.DOTALL)

with codecs.open('src/jefe/reportes/vista_auditoria.py', 'w', encoding='utf-8') as f:
    f.write(va)

print("Modules vista_financiero and vista_auditoria built correctly!")
