import codecs

path = 'src/cerebro_global/nexus_cerebro.py'
with codecs.open(path, 'r', 'utf-8') as f:
    lines = f.readlines()

new_lines = []
query_count = 0
escalar_count = 0
for line in lines:
    if 'def ejecutar_query' in line:
        query_count += 1
        if query_count > 1:
            continue
    if 'def ejecutar_escalar' in line:
        escalar_count += 1
        if escalar_count > 1:
            continue
    if query_count > 1 and line.strip().startswith('from src.base_de_datos'):
        continue
    if query_count > 1 and line.strip().startswith('return db_manager.execute_query'):
        continue
    if query_count > 1 and line.strip().startswith('@staticmethod'):
        pass # Wait, staticmethod is before def. This is too messy.
