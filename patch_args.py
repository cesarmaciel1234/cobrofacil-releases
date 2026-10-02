with open('src/cajero/paso6_cobro/fiado_en_cobro/nativo.py', 'r', encoding='utf8') as f:
    text = f.read()

text = text.replace(
    ", Qt.Key.Key_F1", ""
).replace(
    ", Qt.Key.Key_F2", ""
).replace(
    ", Qt.Key.Key_F3", ""
).replace(
    ", Qt.Key.Key_F4", ""
)

text = text.replace(
    "def _crear_boton(self, texto, bg, hover, key):",
    "def _crear_boton(self, texto, bg, hover):"
)

with open('src/cajero/paso6_cobro/fiado_en_cobro/nativo.py', 'w', encoding='utf8') as f:
    f.write(text)