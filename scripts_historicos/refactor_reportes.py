import codecs
import re

with codecs.open('src/jefe/reportes/reportes_main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Create vista_financiero.py
# We keep all chart classes (ModernCard, ModernChart, SalesChart, etc.)
# We rename JefeReportes to VistaFinanciero.
# We replace setup_ui and setup_ventas_ui so it just builds the financial dashboard.
vf_text = text.replace('class JefeReportes(QWidget):', 'class VistaFinanciero(QWidget):')

# Remove setup_ui and replace it with setup_ventas_ui logic mapped to self
setup_ui_match = re.search(r'(    def setup_ui\(self\):.*?)(?=\n    def _update_tab_buttons)', vf_text, flags=re.DOTALL)
if setup_ui_match:
    vf_text = vf_text.replace(setup_ui_match.group(1), "    def setup_ui(self):\n        lay = QVBoxLayout(self)\n        lay.setContentsMargins(10,10,10,10)\n        self.setup_ventas_ui(lay)\n")

# Modify setup_ventas_ui to accept a layout and build on it
vf_text = vf_text.replace('def setup_ventas_ui(self):', 'def setup_ventas_ui(self, main_lay):')
vf_text = vf_text.replace('self.tab_ventas = QWidget()', '')
vf_text = vf_text.replace('lay = QVBoxLayout(self.tab_ventas)', 'lay = QVBoxLayout()')
vf_text = vf_text.replace('self.stack_views.addWidget(self.tab_ventas)', 'main_lay.addLayout(lay)')

# Remove tabs and stack_views logic
vf_text = re.sub(r'def _update_tab_buttons\(self\):.*?(?=\n    def cargar_datos)', '', vf_text, flags=re.DOTALL)
vf_text = re.sub(r'def _show_ventas_tab\(self\):.*?(?=\n    def setup_audit_ui)', '', vf_text, flags=re.DOTALL)
vf_text = re.sub(r'def setup_audit_ui\(self\):.*?(?=\n    def _limpiar_filtros_audit)', '', vf_text, flags=re.DOTALL)
vf_text = re.sub(r'def _limpiar_filtros_audit\(self\):.*?(?=\n    def _buscar_auditoria)', '', vf_text, flags=re.DOTALL)
vf_text = re.sub(r'def _buscar_auditoria\(self\):.*?(?=\n    def _load_more_audit_rows)', '', vf_text, flags=re.DOTALL)
vf_text = re.sub(r'def _load_more_audit_rows\(self\):.*?(?=\n    def _on_audit_scroll)', '', vf_text, flags=re.DOTALL)
vf_text = re.sub(r'def _on_audit_scroll\(self, value\):.*?(?=\n    def _calcular_comparativa)', '', vf_text, flags=re.DOTALL)
vf_text = re.sub(r'def setup_historial_ui\(self\):.*', '', vf_text, flags=re.DOTALL)

with codecs.open('src/jefe/reportes/vista_financiero.py', 'w', encoding='utf-8') as f:
    f.write(vf_text)

# 2. Create vista_auditoria.py
# Same idea but keep only audit logic
va_text = text.replace('class JefeReportes(QWidget):', 'class VistaAuditoria(QWidget):')

if setup_ui_match:
    va_text = va_text.replace(setup_ui_match.group(1), "    def setup_ui(self):\n        lay = QVBoxLayout(self)\n        lay.setContentsMargins(10,10,10,10)\n        self.setup_audit_ui(lay)\n")

va_text = va_text.replace('def setup_audit_ui(self):', 'def setup_audit_ui(self, main_lay):')
va_text = va_text.replace('self.tab_auditoria = QWidget()', '')
va_text = va_text.replace('lay = QVBoxLayout(self.tab_auditoria)', 'lay = QVBoxLayout()')
va_text = va_text.replace('self.stack_views.addWidget(self.tab_auditoria)', 'main_lay.addLayout(lay)')

# Strip unneeded methods from vista_auditoria
va_text = re.sub(r'def setup_ventas_ui\(self\):.*?(?=\n    def _update_tab_buttons)', '', va_text, flags=re.DOTALL)
va_text = re.sub(r'def _update_tab_buttons\(self\):.*?(?=\n    def cargar_datos)', '', va_text, flags=re.DOTALL)
va_text = re.sub(r'def _show_ventas_tab\(self\):.*?(?=\n    def setup_audit_ui)', '', va_text, flags=re.DOTALL)
va_text = re.sub(r'def setup_historial_ui\(self\):.*', '', va_text, flags=re.DOTALL)
va_text = re.sub(r'def cargar_datos\(self, periodo="Mes Actual"\):.*?(?=\n    def _show_ventas_tab)', '    def cargar_datos(self, periodo="Mes Actual"):\n        pass\n', va_text, flags=re.DOTALL)
va_text = re.sub(r'def _calcular_comparativa\(self\):.*?(?=\n    def _actualizar_audit_kpis)', '    def _calcular_comparativa(self):\n        pass\n', va_text, flags=re.DOTALL)

with codecs.open('src/jefe/reportes/vista_auditoria.py', 'w', encoding='utf-8') as f:
    f.write(va_text)

# 3. Clean reportes_main.py
# Keep ONLY the skeleton
rm_text = text

# Replace the bodies of setup_ventas_ui and setup_audit_ui
rm_text = re.sub(r'def setup_ventas_ui\(self\):.*?(?=\n    def _update_tab_buttons)', 
'''def setup_ventas_ui(self):
        from src.jefe.reportes.vista_financiero import VistaFinanciero
        self.tab_ventas = VistaFinanciero()
        self.stack_views.addWidget(self.tab_ventas)
''', rm_text, flags=re.DOTALL)

rm_text = re.sub(r'def setup_audit_ui\(self\):.*?(?=\n    def _limpiar_filtros_audit)', 
'''def setup_audit_ui(self):
        from src.jefe.reportes.vista_auditoria import VistaAuditoria
        self.tab_auditoria = VistaAuditoria()
        self.stack_views.addWidget(self.tab_auditoria)
''', rm_text, flags=re.DOTALL)

# Delete all the extra functions we just extracted
rm_text = re.sub(r'def _limpiar_filtros_audit\(self\):.*?(?=\n    def setup_historial_ui)', '', rm_text, flags=re.DOTALL)
rm_text = re.sub(r'def cargar_datos\(self, periodo="Mes Actual"\):.*?(?=\n    def _show_ventas_tab)', 
'''def cargar_datos(self, periodo="Mes Actual"):
        # Delegate load to active tab if needed, but for now they load themselves on init
        pass
''', rm_text, flags=re.DOTALL)

rm_text = rm_text.replace('self.cargar_datos("Semana Actual")', '')
rm_text = rm_text.replace('self.sync_timer.timeout.connect(self.sincronizacion_silenciosa)', 'pass')
rm_text = re.sub(r'def sincronizacion_silenciosa\(self\):.*?(?=\n    def _crear_tabla_estilizada)', '', rm_text, flags=re.DOTALL)
rm_text = re.sub(r'def _crear_tabla_estilizada\(self, titulo, col_count=2\):.*?(?=\n    def setup_ui)', '', rm_text, flags=re.DOTALL)

with codecs.open('src/jefe/reportes/reportes_main.py', 'w', encoding='utf-8') as f:
    f.write(rm_text)

print("Split completed successfully!")
