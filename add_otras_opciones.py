import codecs
import re

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

pattern_btn = r'lay_btn = QHBoxLayout\(\)\s*lay_btn\.addStretch\(\)\s*lay_btn\.addWidget\(btn_cancelar\)\s*lay_btn\.addStretch\(\)'
replacement_btn = '''
        # Botón de Otras Opciones (Fiado, Clientes)
        self.btn_otras = QPushButton("🌟 Otras Opciones")
        self.btn_otras.setFixedHeight(60)
        self.btn_otras.setFixedWidth(250)
        self.btn_otras.setStyleSheet("QPushButton { background-color: #64748B; color: white; font-size: 20px; font-weight: bold; border-radius: 12px; } QPushButton:hover { background-color: #475569; }")
        
        # Crear Menú Desplegable
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        menu_otras = QMenu(self)
        menu_otras.setStyleSheet("""
            QMenu { background-color: #FFFFFF; border: 2px solid #E2E8F0; border-radius: 8px; font-size: 18px; font-weight: bold; color: #334155; padding: 5px; }
            QMenu::item { padding: 10px 30px; border-radius: 4px; }
            QMenu::item:selected { background-color: #F1F5F9; color: #0F172A; }
        """)
        
        act_fiado = QAction("👥 Fiado", self)
        act_fiado.triggered.connect(lambda: self.procesar_click_metodo("Fiado"))
        menu_otras.addAction(act_fiado)
        
        act_clientes = QAction("👤 Cuenta Corriente", self)
        act_clientes.triggered.connect(lambda: self.procesar_click_metodo("Clientes"))
        menu_otras.addAction(act_clientes)
        
        self.btn_otras.setMenu(menu_otras)
        
        lay_btn = QHBoxLayout()
        lay_btn.addStretch()
        lay_btn.addWidget(btn_cancelar)
        lay_btn.addSpacing(20)
        lay_btn.addWidget(self.btn_otras)
        lay_btn.addStretch()
'''
if re.search(pattern_btn, code):
    code = re.sub(pattern_btn, replacement_btn, code)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Otras Opciones button added!")
else:
    print("Pattern not found!")
