import sys

with open('src/base_de_datos/autoblindaje_db.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        if engine_type == "sqlite" or latest_backup.lower().endswith(".db"):
            db_file = os.path.join(base_dir, "punpro.db")'''

replacement = '''        if engine_type == "sqlite":
            if not latest_backup.lower().endswith(".db"):
                logger.error("No se puede restaurar un respaldo de MariaDB sobre SQLite.")
                return False
            db_file = os.path.join(base_dir, "punpro.db")'''

if target in content:
    content = content.replace(target, replacement)
    with open('src/base_de_datos/autoblindaje_db.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Target not found.")
