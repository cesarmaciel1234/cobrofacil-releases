import os
import sys
import stat
import shutil
import zipfile
import datetime

# Forzar UTF-8 en la salida para evitar UnicodeEncodeError en consola Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def rmtree_force(path):
    """Elimina un directorio forzando permisos de solo-lectura antes de borrar."""
    def on_error(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass  # ignorar si sigue sin poder borrar
    shutil.rmtree(path, onerror=on_error)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("INICIANDO RESPALDO COMPLETO - PUNPRO TPV 2026")
print("=" * 60)

# ---- PASO 1: Limpieza ----
print("\n[1/4] Limpiando archivos temporales...")
files_to_delete = [
    "test_hardware_drawer.py", "test_opos_caja.py", "test_stress.py",
    "opos_drawer_test.py", "test_database.py", "test_cajero_stress.py",
    "test_balanza_db.py", "check_db.py", "crash.log", "crash-cesar.log",
    "config-cesar.json", "tmp_migrate.py", "apply_systel_config.py",
    "fix_config_4digits.py", "reset_cajero.py"
]
dirs_to_delete = ["build", "__pycache__", ".pytest_cache", "dist"]

for f in files_to_delete:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"  [OK] Borrado: {f}")
        except Exception as e:
            print(f"  [ERROR] No se pudo borrar {f}: {e}")

for d in dirs_to_delete:
    if os.path.exists(d):
        try:
            rmtree_force(d)
            if not os.path.exists(d):
                print(f"  [OK] Carpeta borrada: {d}")
            else:
                print(f"  [SKIP] Carpeta en uso, se omite: {d}")
        except Exception as e:
            print(f"  [SKIP] No se pudo borrar {d}: {e}")

# ---- PASO 2: Punto de restauracion con timestamp ----
now = datetime.datetime.now()
ts = now.strftime("%Y%m%d_%H%M%S")
fecha_legible = now.strftime("%Y-%m-%d %H:%M")
backup_dir = os.path.join("backups", f"Respaldo_{ts}")
critical_dir = os.path.join(backup_dir, "datos_criticos")

print(f"\n[2/4] Creando punto de restauracion: {backup_dir}...")
os.makedirs(critical_dir, exist_ok=True)
for fname in ["punpro.db", "config.json"]:
    if os.path.exists(fname):
        shutil.copy2(fname, os.path.join(critical_dir, fname))
        print(f"  [OK] Copiado: {fname}")

# ---- PASO 3: ZIP maestro ----
zip_filename = "PROYECTO_COMPLETO_RESPALDO.zip"
print(f"\n[3/4] Generando {zip_filename}...")

exclude_dirs = {".venv", ".git", "backups", "build", "dist", "CATORTA_USB_PUNPRO", "scratch", "__pycache__"}
exclude_files = {zip_filename, "_hacer_respaldo.py"}

total_files = 0
with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for file in files:
            if file in exclude_files or file.endswith(".zip") or file.endswith(".pyc"):
                continue
            fp = os.path.join(root, file)
            arc = os.path.relpath(fp, ".")
            try:
                zipf.write(fp, arc)
                total_files += 1
            except Exception as e:
                print(f"  [WARN] No se pudo agregar {arc}: {e}")

size_mb = os.path.getsize(zip_filename) / 1024 / 1024
print(f"  [OK] ZIP creado: {total_files} archivos | {size_mb:.1f} MB")

# ---- PASO 4: CATORTA USB ----
print("\n[4/4] Ensamblando CATORTA_USB_PUNPRO...")
catorta = "CATORTA_USB_PUNPRO"
if os.path.exists(catorta):
    rmtree_force(catorta)

subdirs = [
    "1_Sistemas_Portables",
    "2_ZIPs_Respaldo",
    "3_Manuales_Documentacion",
    "4_Instaladores_InnoSetup",
]
for sd in subdirs:
    os.makedirs(os.path.join(catorta, sd), exist_ok=True)

# Copiar ZIP
shutil.copy2(zip_filename, os.path.join(catorta, "2_ZIPs_Respaldo", zip_filename))
print("  [OK] ZIP copiado a 2_ZIPs_Respaldo")

# Copiar docs
docs_dest = os.path.join(catorta, "3_Manuales_Documentacion")
if os.path.exists("docs"):
    for item in os.listdir("docs"):
        s = os.path.join("docs", item)
        d = os.path.join(docs_dest, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    print("  [OK] Carpeta docs/ copiada")

ia_plan = "ia planificacion"
if os.path.exists(ia_plan):
    shutil.copytree(ia_plan, os.path.join(docs_dest, "ia_planificacion"))
    print("  [OK] Carpeta 'ia planificacion' copiada")

# Copiar scripts Inno Setup y PyInstaller spec
iss_spec_dest = os.path.join(catorta, "4_Instaladores_InnoSetup")
for f in os.listdir("."):
    if f.endswith(".iss") or f.endswith(".spec"):
        shutil.copy2(f, os.path.join(iss_spec_dest, f))
        print(f"  [OK] Copiado instalador: {f}")

# Guia rapida
guia = (
    "PUNPRO TPV 2026 - CATORTA USB MAESTRA\n"
    "=" * 50 + "\n"
    f"Generado: {fecha_legible}\n\n"
    "ESTRUCTURA:\n\n"
    "  1_Sistemas_Portables\n"
    "    Sistema listo para ejecutar en cualquier PC.\n\n"
    "  2_ZIPs_Respaldo\n"
    "    Respaldo comprimido completo del proyecto.\n\n"
    "  3_Manuales_Documentacion\n"
    "    Toda la documentacion, manuales y planificacion.\n\n"
    "  4_Instaladores_InnoSetup\n"
    "    Scripts Inno Setup (.iss) y PyInstaller (.spec).\n\n"
    "=" * 50 + "\n"
    "PUNPRO SYSTEMS - LICENCIA DE DESPLIEGUE ELITE 2026\n"
)
with open(os.path.join(catorta, "GUIA_RAPIDA.txt"), "w", encoding="utf-8") as g:
    g.write(guia)
print("  [OK] GUIA_RAPIDA.txt generada")

print("\n" + "=" * 60)
print("RESPALDO COMPLETO FINALIZADO CON EXITO")
print("=" * 60)
print(f"  ZIP maestro  : {zip_filename} ({size_mb:.1f} MB)")
print(f"  Archivos     : {total_files}")
print(f"  Restauracion : {backup_dir}")
print(f"  Catorta USB  : {catorta}/")
print("=" * 60)
