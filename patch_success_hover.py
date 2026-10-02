import sys
file_path = 'src/contabilidad/vista_resumen.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("PAL['success_hover']", "PAL['success']")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed success_hover')
