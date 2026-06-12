import codecs
import re

with codecs.open('src/jefe/contabilidad/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update init_ui to add init_promedios_tab
content = re.sub(
    r'(self\.init_reports_tab\(\)\s*# 12\n\s*# self\.init_stock_tab\(\)\s*# Eliminado por solicitud de enfoque contable/financiero)',
    r'\1\n        self.init_promedios_tab()     # 13',
    content
)

# 2. Update stack index if role == admin
content = re.sub(
    r'(self\.stack\.setCurrentIndex\()13(\))',
    r'\g<1>14\g<2>',
    content
)

# 3. Add to admin menu (first occurrence of Reportes PDF block in init_sidebar_items)
content = re.sub(
    r'(self\.add_nav_item\("Reportes PDF", 12\))(.*?)(\s*else:)',
    r'\1\n            \n            # Espaciador\n            spacer = QListWidgetItem("")\n            spacer.setFlags(Qt.NoItemFlags)\n            self.nav_list.addItem(spacer)\n            \n            self.add_nav_item("Promedios", 13)\2\3',
    content,
    flags=re.DOTALL
)

# 4. Add to non-admin menu (second occurrence)
content = re.sub(
    r'(self\.add_nav_item\("Reportes PDF", 12\))(.*?)(\s*def add_nav_item)',
    r'\1\n            \n            # Espaciador\n            spacer = QListWidgetItem("")\n            spacer.setFlags(Qt.NoItemFlags)\n            self.nav_list.addItem(spacer)\n            \n            self.add_nav_item("Promedios", 13)\2\3',
    content,
    flags=re.DOTALL
)

# 5. Add method
method_code = """
    def init_promedios_tab(self):
        self.tab_promedios = QWidget()
        layout = QVBoxLayout(self.tab_promedios)
        lbl = QLabel("<h1>Módulo de Promedios (En Construcción)</h1>")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        self.stack.addWidget(self.tab_promedios)
"""

marker = "def init_reports_tab(self):"
marker_idx = content.find(marker)
if marker_idx != -1:
    end_of_method = content.find("def ", marker_idx + len(marker))
    content = content[:end_of_method] + method_code + content[end_of_method:]

with codecs.open('src/jefe/contabilidad/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
