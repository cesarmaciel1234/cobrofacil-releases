import time
from src.services.mariadb_controller import mariadb_controller

print("Iniciando MariaDB...")
mariadb_controller.start_server()

print("Esperando 5s para estabilizar MariaDB...")
time.sleep(5)

print("Importando database (iniciara db_manager)...")
from src.base_de_datos.database import db_manager

print("Reconectando...")
db_manager.reconectar_mariadb("127.0.0.1")
print("Creando tablas...")
db_manager._create_tables()
print("Migrando...")
db_manager._migrate_db()

print("Matando MariaDB para liberar...")
mariadb_controller.stop_server()
print("LISTO!")
