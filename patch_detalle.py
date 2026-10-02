with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'r', encoding='utf8') as f:
    text = f.read()

text = text.replace('self.detalle.setText(f""Deuda Previa: \nVenta Actual: "")', 'self.detalle.setText(f""Deuda Previa: \nVenta Actual: "")')

with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'w', encoding='utf8') as f:
    f.write(text)