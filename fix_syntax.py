file_path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("\\'stack\\'", "'stack'")
text = text.replace("\\'_fiado_flujo_activo\\'", "'_fiado_flujo_activo'")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed syntax error')
