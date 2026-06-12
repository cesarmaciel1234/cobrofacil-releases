import codecs

with codecs.open('src/jefe/contabilidad/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update init_ui
old_init_ui = """        self.init_ai_tab()            # 11
        self.init_reports_tab()       # 12
        # self.init_stock_tab()         # Eliminado por solicitud de enfoque contable/financiero
        
        if self.role == "admin":
            self.init_admin_tab()           # Índice 14
            self.init_admin_payments_tab()  # Índice 15
            self.init_audit_pro_tab()       # Índice 16 (Nivel 4)
            self.stack.setCurrentIndex(13)"""

new_init_ui = """        self.init_ai_tab()            # 11
        self.init_reports_tab()       # 12
        self.init_promedios_tab()     # 13
        # self.init_stock_tab()         # Eliminado por solicitud de enfoque contable/financiero
        
        if self.role == "admin":
            self.init_admin_tab()           # Índice 14
            self.init_admin_payments_tab()  # Índice 15
            self.init_audit_pro_tab()       # Índice 16 (Nivel 4)
            self.stack.setCurrentIndex(14)"""

# 2. Update init_sidebar_items for admin
old_admin_sidebar = """            # El administrador tiene un menú simplificado con acceso al panel global (índice 13)
            self.add_nav_item("Panel Global", 13)
            self.add_nav_item("Ejecutar Pagos", 14)
            # Control Stock eliminado
            self.add_nav_item("Auditoría Pro", 15)"""

new_admin_sidebar = """            # El administrador tiene un menú simplificado con acceso al panel global (índice 14)
            self.add_nav_item("Panel Global", 14)
            self.add_nav_item("Ejecutar Pagos", 15)
            # Control Stock eliminado
            self.add_nav_item("Auditoría Pro", 16)"""

# 3. Update init_sidebar_items for user
old_user_sidebar = """            self.add_section_label("EXPORTACIÓN")
            self.add_nav_item("Reportes PDF", 12)"""

new_user_sidebar = """            self.add_section_label("EXPORTACIÓN")
            self.add_nav_item("Reportes PDF", 12)
            
            # Espaciador
            spacer = QListWidgetItem("")
            spacer.setFlags(Qt.NoItemFlags)
            self.nav_list.addItem(spacer)
            
            self.add_nav_item("Promedios", 13)"""

# 4. Add the init_promedios_tab method definition
method_code = """
    def init_promedios_tab(self):
        self.tab_promedios = QWidget()
        layout = QVBoxLayout(self.tab_promedios)
        lbl = QLabel("<h1>Módulo de Promedios (En Construcción)</h1>")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        self.stack.addWidget(self.tab_promedios)
"""

if old_init_ui in content:
    content = content.replace(old_init_ui, new_init_ui)
else:
    print("Failed to replace init_ui")

if old_admin_sidebar in content:
    content = content.replace(old_admin_sidebar, new_admin_sidebar)
else:
    print("Failed to replace admin sidebar")

if old_user_sidebar in content:
    content = content.replace(old_user_sidebar, new_user_sidebar)
else:
    print("Failed to replace user sidebar")

# Add init_promedios_tab after init_reports_tab
marker = "def init_reports_tab(self):"
marker_idx = content.find(marker)
if marker_idx != -1:
    end_of_method = content.find("def ", marker_idx + len(marker))
    content = content[:end_of_method] + method_code + content[end_of_method:]
else:
    print("Failed to inject method")

with codecs.open('src/jefe/contabilidad/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done applying modifications")
