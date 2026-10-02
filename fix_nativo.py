with open('src/cajero/paso6_cobro/fiado_en_cobro/nativo.py', 'r', encoding='utf8') as f:
    text = f.read()

text = text.replace(
    'lbl_deuda = QLabel(f\'Deuda Previa:\\n\\\')',
    'lbl_deuda = QLabel(f\'Deuda Previa:\\n\\')'
)
text = text.replace(
    'lbl_venta = QLabel(f\'Venta Actual:\\n\\\')',
    'lbl_venta = QLabel(f\'Venta Actual:\\n\\')'
)

with open('src/cajero/paso6_cobro/fiado_en_cobro/nativo.py', 'w', encoding='utf8') as f:
    f.write(text)