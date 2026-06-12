import codecs
import re

with codecs.open('src/admin/admin3_reportes.py', 'r', encoding='utf-8') as f:
    text = f.read()

# --- VISTA FINANCIERO ---
vf = text.replace('class Admin3Reportes(QWidget):', 'class VistaFinanciero(QWidget):')

# Replace setup_ui
vf = re.sub(r'    def setup_ui\(self\):.*?(?=\n    def _update_tab_buttons)',
'''    def setup_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(10, 10, 10, 10)
        
        self.tab_ventas = QWidget()
        lay = QVBoxLayout(self.tab_ventas)
        lay.setContentsMargins(0,0,0,0)
        self.setup_ventas_ui_lay(lay)
        main_lay.addWidget(self.tab_ventas)
''', vf, flags=re.DOTALL)

# Rename setup_ventas_ui and make it take layout
vf = vf.replace('def setup_ventas_ui(self):', 'def setup_ventas_ui_lay(self, lay):')
vf = vf.replace('self.tab_ventas = QWidget()', '')
vf = vf.replace('lay = QVBoxLayout(self.tab_ventas)', '')
vf = vf.replace('self.stack_views.addWidget(self.tab_ventas)', '')

# Mute other setups
vf = re.sub(r'def setup_audit_ui\(self\):.*?(?=\n    def _limpiar_filtros_audit)', 'def setup_audit_ui(self):\n        pass\n', vf, flags=re.DOTALL)
vf = re.sub(r'def setup_historial_ui\(self\):.*?(?=\n    def _cargar_historial_tickets)', 'def setup_historial_ui(self):\n        pass\n', vf, flags=re.DOTALL)

with codecs.open('src/jefe/reportes/vista_financiero.py', 'w', encoding='utf-8') as f:
    f.write(vf)


# --- VISTA AUDITORIA ---
va = text.replace('class Admin3Reportes(QWidget):', 'class VistaAuditoria(QWidget):')

# Replace setup_ui
va = re.sub(r'    def setup_ui\(self\):.*?(?=\n    def _update_tab_buttons)',
'''    def setup_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(10, 10, 10, 10)
        
        self.tab_auditoria = QWidget()
        lay = QVBoxLayout(self.tab_auditoria)
        lay.setContentsMargins(0,0,0,0)
        self.setup_audit_ui_lay(lay)
        main_lay.addWidget(self.tab_auditoria)
''', va, flags=re.DOTALL)

# Rename setup_audit_ui and make it take layout
va = va.replace('def setup_audit_ui(self):', 'def setup_audit_ui_lay(self, lay):')
va = va.replace('self.tab_auditoria = QWidget()', '')
va = va.replace('lay = QVBoxLayout(self.tab_auditoria)', '')
va = va.replace('self.stack_views.addWidget(self.tab_auditoria)', '')

# Mute other setups
va = re.sub(r'def setup_ventas_ui\(self\):.*?(?=\n    def _update_tab_buttons)', 'def setup_ventas_ui(self):\n        pass\n', va, flags=re.DOTALL)
va = re.sub(r'def setup_historial_ui\(self\):.*?(?=\n    def _cargar_historial_tickets)', 'def setup_historial_ui(self):\n        pass\n', va, flags=re.DOTALL)
va = re.sub(r'def cargar_datos\(self, periodo="Mes Actual"\):.*?(?=\n    def _show_ventas_tab)', 'def cargar_datos(self, periodo="Mes Actual"):\n        pass\n', va, flags=re.DOTALL)

with codecs.open('src/jefe/reportes/vista_auditoria.py', 'w', encoding='utf-8') as f:
    f.write(va)

print("Safely generated modules.")
