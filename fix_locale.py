import os

file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix text setting and getting
old_set = '''self.txt_monto_abono.setText(f"{monto_sugerido:.2f}")'''
new_set = '''self.txt_monto_abono.setText(f"{monto_sugerido:.2f}".replace('.', ','))'''
text = text.replace(old_set, new_set)

old_get = '''texto = self.txt_monto_abono.text().replace(',', '.')'''
new_get = '''texto = self.txt_monto_abono.text().replace('.', '').replace(',', '.')'''
text = text.replace(old_get, new_get)

# Let's also enforce English locale on the validator to avoid thousands issues, or just remove the validator
old_val = '''self.txt_monto_abono.setValidator(QDoubleValidator(0.0, 9999999.0, 2))'''
new_val = '''# self.txt_monto_abono.setValidator(QDoubleValidator(0.0, 9999999.0, 2))'''
text = text.replace(old_val, new_val)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
