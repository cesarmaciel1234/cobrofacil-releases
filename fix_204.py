with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'r', encoding='utf8') as f:
    text = f.read()

text = text.replace('        self.txt_monto_abono.installEventFilter(self)\n            self.instruccion.show()', '            self.txt_monto_abono.installEventFilter(self)\n            self.instruccion.show()')

with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'w', encoding='utf8') as f:
    f.write(text)