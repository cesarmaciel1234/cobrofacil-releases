import os

files_to_fix = [
    'src/historial_ventas/acciones.py',
    'src/historial_ventas/desglose.py',
    'src/historial_ventas/listar.py'
]

for file_path in files_to_fix:
    if not os.path.exists(file_path): continue
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    text = text.replace('db_manager.test_connection()', 'db_manager.is_connected()')
    text = text.replace('db.test_connection()', 'db.is_connected()')
    text = text.replace('hasattr(db, "test_connection")', 'hasattr(db, "is_connected")')
    text = text.replace("hasattr(db, 'test_connection')", "hasattr(db, 'is_connected')")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
