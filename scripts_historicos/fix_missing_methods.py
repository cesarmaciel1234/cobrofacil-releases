import codecs

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

missing_methods = """
    def _show_ventas_tab(self):
        self.stack_views.setCurrentIndex(0)
        self._update_tab_buttons()

    def _show_auditoria_tab(self):
        self.stack_views.setCurrentIndex(1)
        self._update_tab_buttons()

    def _show_historial_tab(self):
        self.stack_views.setCurrentIndex(2)
        self._update_tab_buttons()

    def setup_audit_ui(self):
"""

content = content.replace("    def setup_audit_ui(self):", missing_methods)

with codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Restored missing methods")
