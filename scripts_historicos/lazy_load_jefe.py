import codecs
import re

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add flags to __init__
init_replacement = """        self._audit_ui_loaded = False
        self._historial_ui_loaded = False
        
        self.setup_ui()"""
content = content.replace("        self.setup_ui()", init_replacement, 1)

# 2. Modify setup_ui to skip synchronous build
# Currently it has:
#         # Auditoria view
#         self.audit_view = QWidget()
#         self.setup_audit_ui()
#         self.stack_views.addWidget(self.audit_view)
#         # Historial view ...
# But wait, looking at the grep earlier, does setup_historial_ui exist inside setup_ui?
# Let's just regex replace self.setup_audit_ui() and self.setup_historial_ui() inside setup_ui
# Actually, I'll replace `self.setup_audit_ui()` with `pass # Lazy loaded` inside setup_ui.
content = re.sub(r'(self\.audit_view = QWidget\(\)\s*)self\.setup_audit_ui\(\)', r'\1# self.setup_audit_ui() # Lazy loaded', content)
content = re.sub(r'(self\.historial_view = QWidget\(\)\s*)self\.setup_historial_ui\(\)', r'\1# self.setup_historial_ui() # Lazy loaded', content)

# Also need to make sure self.historial_view is added if it was there. Let's see if we can just inject _lazy_load_tabs logic
content = content.replace("        self.cargar_datos()\n", """        self.cargar_datos()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, self._lazy_load_tabs)\n""")

# 3. Modify tab functions
new_tab_funcs = """    def _show_auditoria_tab(self):
        if getattr(self, '_audit_ui_loaded', False) == False:
            self.setup_audit_ui()
            self._audit_ui_loaded = True
        self.stack_views.setCurrentIndex(1)
        self._update_tab_buttons()

    def _show_historial_tab(self):
        if getattr(self, '_historial_ui_loaded', False) == False:
            self.setup_historial_ui()
            self._historial_ui_loaded = True
        self.stack_views.setCurrentIndex(2)
        self._update_tab_buttons()

    def _lazy_load_tabs(self):
        if getattr(self, '_audit_ui_loaded', False) == False:
            self.setup_audit_ui()
            self._audit_ui_loaded = True
        if getattr(self, '_historial_ui_loaded', False) == False:
            self.setup_historial_ui()
            self._historial_ui_loaded = True
"""

# Replace the existing _show_auditoria_tab and _show_historial_tab
content = re.sub(r'    def _show_auditoria_tab\(self\):.*?self\._update_tab_buttons\(\)', '', content, flags=re.DOTALL)
content = re.sub(r'    def _show_historial_tab\(self\):.*?self\._update_tab_buttons\(\)', '', content, flags=re.DOTALL)

# Insert the new ones before setup_audit_ui
content = content.replace("    def setup_audit_ui(self):", new_tab_funcs + "\n    def setup_audit_ui(self):")


with codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Lazy UI Loading injected successfully.")
