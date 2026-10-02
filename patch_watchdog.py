import sys

with open('src/central_red_global/servidor/arranque/bandeja.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                from src.services.mariadb_controller import mariadb_controller

                mariadb_controller.start_server()'''

replacement = '''                from src.services.mariadb_controller import mariadb_controller

                mariadb_controller.start_server()
                from src.base_de_datos.database import db
                if getattr(db, "db_engine_type", "sqlite") == "sqlite":
                    db.reconectar_mariadb("127.0.0.1")
                    db._create_tables()
                    db._migrate_db()'''

if target in content:
    content = content.replace(target, replacement)
    with open('src/central_red_global/servidor/arranque/bandeja.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed watchdog!")
else:
    print("Target not found.")
