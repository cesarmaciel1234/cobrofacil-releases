import os
import shutil
import subprocess
import time
import zipfile

# Obtener la ruta absoluta de la carpeta del propio script (hace el programa 100% portable)
base_install = os.path.dirname(os.path.abspath(__file__))
mysql_exe = os.path.join(base_install, "mariadb_server", "bin", "mysql.exe")
mysqld_exe = os.path.join(base_install, "mariadb_server", "bin", "mysqld.exe")
data_dir = os.path.join(base_install, "mariadb_server", "data")
punpro_db_dir = os.path.join(data_dir, "punpro_db")
backup_dir = os.path.join(base_install, "backups", "db")

print("=========================================================")
print("  ASISTENTE DE RESTAURACIÓN DE RESPALDOS - COBRO FÁCIL")
print("=========================================================")

# Listar respaldos disponibles
try:
    files = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith("backup_") and (f.endswith(".sql") or f.endswith(".zip"))],
        key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
        reverse=True
    )
except Exception as e:
    print(f"Error leyendo carpeta de respaldos: {e}")
    input("Presiona Enter para salir...")
    exit(1)

if not files:
    print("No se encontraron respaldos .sql o .zip en la carpeta backups/db/")
    input("Presiona Enter para salir...")
    exit(1)

print("\nRespaldos disponibles:")
for idx, f in enumerate(files):
    sz = os.path.getsize(os.path.join(backup_dir, f)) / (1024 * 1024)
    print(f" [{idx + 1}] {f} ({sz:.2f} MB)")

print("\n[R] Restaurar el respaldo más reciente (Recomendado)")
print("[S] Salir sin hacer cambios")

choice = input("\nSelecciona una opción: ").strip().lower()

if choice == "s":
    print("Operación cancelada.")
    exit(0)

selected_file = files[0] # Por defecto, el más reciente
if choice != "r" and choice.isdigit():
    val = int(choice) - 1
    if 0 <= val < len(files):
        selected_file = files[val]
    else:
        print("Opción inválida.")
        exit(1)

backup_path = os.path.join(backup_dir, selected_file)
print(f"\nProcesando {selected_file}...")

# 1. Asegurar detención de servidores MariaDB locales para liberar candados de archivos
print("Deteniendo servidor MariaDB temporalmente...")
subprocess.run("taskkill /F /IM mysqld.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)

try:
    if selected_file.endswith(".zip"):
        print("Restaurando archivos físicos de base de datos (.ZIP)...")
        # Eliminar carpeta punpro_db actual
        if os.path.exists(punpro_db_dir):
            shutil.rmtree(punpro_db_dir)
        os.makedirs(punpro_db_dir, exist_ok=True)
        
        # Descomprimir contenido directamente en punpro_db
        with zipfile.ZipFile(backup_path, 'r') as z:
            z.extractall(punpro_db_dir)
            
        print("\n✅ Archivos físicos restaurados con éxito.")
    else:
        print("Restaurando a partir de volcado SQL...")
        # Iniciar temporalmente el motor para importar el SQL
        subprocess.Popen(
            [mysqld_exe, f'--datadir={data_dir}', '--port=3306', '--bind-address=0.0.0.0', '--skip-networking=OFF', '--skip-name-resolve'],
            creationflags=0x08000000
        )
        time.sleep(3)
        
        with open(backup_path, "r", encoding="utf-8", errors="replace") as f_in:
            sql_content = f_in.read()
            
        # Recrear BD
        subprocess.run(
            [mysql_exe, "-u", "root", "-p1234", "-e", "CREATE DATABASE IF NOT EXISTS punpro_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Importar SQL
        subprocess.run(
            [mysql_exe, "-u", "root", "-p1234", "punpro_db"],
            input=sql_content,
            text=True,
            check=True
        )
        print("\n✅ Respaldos importados correctamente del archivo SQL.")
        
except Exception as e:
    print(f"\n❌ Error durante la restauración: {e}")

# Levantar MariaDB nuevamente para dejar el sistema listo
print("\nRe-iniciando base de datos...")
subprocess.Popen(
    [mysqld_exe, f'--datadir={data_dir}', '--port=3306', '--bind-address=0.0.0.0', '--skip-networking=OFF', '--skip-name-resolve'],
    creationflags=0x08000000
)
time.sleep(2)

print("\n¡Operación finalizada!")
input("Presiona Enter para cerrar...")
