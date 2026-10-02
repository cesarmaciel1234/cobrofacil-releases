import re

with open('src/cajero/ingresar_efectivo/fiado/consulta.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_logic = '''        # Optimizacion de busqueda para fiado (no usamos COALESCE que rompe los indices)
        base += (" AND (c.nombre LIKE ? OR c.dni LIKE ? OR c.telefono LIKE ? OR c.direccion LIKE ?)")'''

text = re.sub(
    r'        base \+= \(\" AND \(c\.nombre LIKE \? OR COALESCE\(c\.dni, \'\'\) LIKE \?\"[\s\S]*?OR COALESCE\(c\.direccion, \'\'\) LIKE \?\)\"\)',
    new_logic,
    text
)

with open('src/cajero/ingresar_efectivo/fiado/consulta.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Optimized fiado/consulta.py')
