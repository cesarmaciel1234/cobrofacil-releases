with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'r', encoding='utf8') as f:
    text = f.read()

# Remove checkmark
text = text.replace('self.icono.show()', '# self.icono.show()')

# Remove Límite and Compra Actual
import re
text = re.sub(r'self\.detalle\.setText\(f"\{nombre\}.*?"\)', 'self.detalle.setText(f"{nombre}")', text)

with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'w', encoding='utf8') as f:
    f.write(text)