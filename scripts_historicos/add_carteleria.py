import codecs
import re

text = codecs.open('src/inicio_y_perfiles/perfil_pantalla.py', 'r', encoding='utf-8').read()

# 1. Update CARD_STYLE
card_style_new = '''CARD_STYLE = {
    "cajero": ("#0284C7", "#E0F2FE", "VENTA DIRECTA",  "#0369A1"),  # azul frío
    "admin":  ("#059669", "#DCFCE7", "FULL ACCESS",    "#047857"),  # verde templado
    "jefe":   ("#D97706", "#FEF3C7", "ACCESO GERENCIAL","#B45309"), # ámbar cálido
    "carteleria": ("#8B5CF6", "#EDE9FE", "MODO VISOR", "#6D28D9"), # púrpura vibrante
}'''
text = re.sub(r'CARD_STYLE = \{.*?\}', card_style_new, text, flags=re.DOTALL)

# 2. Update _ROLES
text = text.replace('_ROLES  = ["cajero", "admin", "jefe"]', '_ROLES  = ["cajero", "admin", "jefe", "carteleria"]')

# 3. Update window width
text = text.replace('self.setFixedSize(840, 490)', 'self.setFixedSize(1100, 490)')

# 4. Add the button
btn_code = '''self.btn_jefe = ProfileCard(
            "jefe", "👑", "JEFE / DUEÑO",
            "Control total · Reportes · Cierres")
        self.btn_jefe.clicked.connect(lambda: self._elegir("jefe"))

        self.btn_carteleria = ProfileCard(
            "carteleria", "📺", "CARTELERÍA",
            "Pantalla Pública · Publicidad")
        self.btn_carteleria.clicked.connect(lambda: self._elegir("carteleria"))'''
text = text.replace('''self.btn_jefe = ProfileCard(
            "jefe", "👑", "JEFE / DUEÑO",
            "Control total · Reportes · Cierres")
        self.btn_jefe.clicked.connect(lambda: self._elegir("jefe"))''', btn_code)

text = text.replace('cards_lay.addWidget(self.btn_jefe)', 'cards_lay.addWidget(self.btn_jefe)\n        cards_lay.addWidget(self.btn_carteleria)')

# 5. Update update_selection_ui
update_ui = '''self.btn_jefe.set_active(self.selected_index == 2)
        self.btn_carteleria.set_active(self.selected_index == 3)'''
text = text.replace('self.btn_jefe.set_active(self.selected_index == 2)', update_ui)

# 6. Update modulo
text = text.replace('self.selected_index = (self.selected_index + delta) % 3', 'self.selected_index = (self.selected_index + delta) % 4')

codecs.open('src/inicio_y_perfiles/perfil_pantalla.py', 'w', encoding='utf-8').write(text)
print('perfil_pantalla updated successfully!')
