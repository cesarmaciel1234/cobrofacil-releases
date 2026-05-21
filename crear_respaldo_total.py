import os
import shutil
import zipfile
import datetime
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def crear_respaldo_total():
    print("="*60)
    print("🛡️ INICIANDO RESPALDO DE SEGURIDAD ABSOLUTO - PUNPRO 2026")
    print("="*60)

    # 1. Limpieza de archivos temporales
    print("\n[1/5] Ejecutando Limpieza de Archivos Temporales...")
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
                print(f"  ✅ Borrado: {f}")
            except Exception as e:
                print(f"  ❌ Error al borrar {f}: {e}")

    for d in dirs_to_delete:
        if os.path.exists(d):
            try:
                import stat
                for root, dirs, files in os.walk(d, topdown=False):
                    for file in files:
                        try: os.chmod(os.path.join(root, file), stat.S_IWRITE)
                        except: pass
                    for dir in dirs:
                        try: os.chmod(os.path.join(root, dir), stat.S_IWRITE)
                        except: pass
                shutil.rmtree(d)
                print(f"  ✅ Carpeta borrada: {d}")
            except Exception as e:
                print(f"  ❌ Error al borrar carpeta {d}: {e}")

    # 2. Crear punto de restauración con marca de tiempo
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join("backups", f"Respaldo_{timestamp}")
    critical_dir = os.path.join(backup_dir, "datos_criticos")
    
    print(f"\n[2/5] Creando punto de restauración en {backup_dir}...")
    try:
        os.makedirs(critical_dir, exist_ok=True)
        if os.path.exists("punpro.db"):
            shutil.copy2("punpro.db", os.path.join(critical_dir, "punpro.db"))
            print("  ✅ Base de datos (punpro.db) respaldada.")
        if os.path.exists("config.json"):
            shutil.copy2("config.json", os.path.join(critical_dir, "config.json"))
            print("  ✅ Configuración (config.json) respaldada.")
    except Exception as e:
        print(f"  ❌ Error al crear punto de restauración: {e}")

    # 3. Crear ZIP completo del proyecto (PROYECTO_COMPLETO_RESPALDO.zip)
    print("\n[3/5] Creando ZIP de Respaldo Completo (PROYECTO_COMPLETO_RESPALDO.zip)...")
    zip_filename = "PROYECTO_COMPLETO_RESPALDO.zip"
    
    exclude_dirs = {".venv", ".git", "backups", "build", "dist", "CATORTA_USB_PUNPRO"}
    exclude_files = {zip_filename}

    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk("."):
                # Filtrar carpetas excluidas
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
                
                for file in files:
                    if file in exclude_files or file.endswith('.zip') or file.endswith('.pyc'):
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, ".")
                    zipf.write(file_path, arcname)
        print(f"  ✅ ZIP de respaldo maestro creado con éxito: {zip_filename}")
    except Exception as e:
        print(f"  ❌ Error al empaquetar ZIP: {e}")

    # 4. Ensamblar la Super Carpeta "CATORTA_USB_PUNPRO"
    print("\n[4/5] Ensamblando la súper carpeta 'CATORTA_USB_PUNPRO' para Pendrive...")
    catorta = "CATORTA_USB_PUNPRO"
    if os.path.exists(catorta):
        import stat
        for root, dirs, files in os.walk(catorta, topdown=False):
            for file in files:
                try: os.chmod(os.path.join(root, file), stat.S_IWRITE)
                except: pass
            for dir in dirs:
                try: os.chmod(os.path.join(root, dir), stat.S_IWRITE)
                except: pass
        try:
            shutil.rmtree(catorta)
        except Exception as e:
            print(f"  ⚠️ Advertencia al limpiar Catorta anterior: {e}")
        
    os.makedirs(os.path.join(catorta, "1_Sistemas_Portables_Descomprimidos"), exist_ok=True)
    os.makedirs(os.path.join(catorta, "2_Archivos_Comprimidos_ZIP"), exist_ok=True)
    os.makedirs(os.path.join(catorta, "3_Manuales_y_Documentacion"), exist_ok=True)
    os.makedirs(os.path.join(catorta, "4_Instaladores_InnoSetup"), exist_ok=True)

    # Copiar ZIPs de respaldo
    if os.path.exists(zip_filename):
        shutil.copy2(zip_filename, os.path.join(catorta, "2_Archivos_Comprimidos_ZIP", zip_filename))
        print("  ✅ ZIP de respaldo copiado a la Catorta.")

    # Copiar Base Documental
    docs_source = "docs"
    docs_dest = os.path.join(catorta, "3_Manuales_y_Documentacion")
    if os.path.exists(docs_source):
        for item in os.listdir(docs_source):
            s = os.path.join(docs_source, item)
            d = os.path.join(docs_dest, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        print("  ✅ Manuales y documentación técnica copiados.")

    # Copiar esquemas Inno Setup
    for f in os.listdir("."):
        if f.endswith(".iss") or f.endswith(".spec"):
            shutil.copy2(f, os.path.join(catorta, "4_Instaladores_InnoSetup", f))
    print("  ✅ Archivos de instalación Inno Setup y Spec copiados.")

    # Escribir la Guía del Pendrive
    guia_content = """===============================================================================
🌟 PUNPRO TPV 2026 - INDICE DE LA CATORTA USB MAESTRA
===============================================================================

Has copiado esta carpeta a tu pendrive. Tienes en tus manos el batallón
de despliegue informático definitivo para operar en cualquier mostrador.

ESTRUCTURA DE CONTENIDOS:

📁 1_Sistemas_Portables_Descomprimidos\\
   Entra aquí si necesitas abrir la caja de inmediato en una PC ajena.
   Elige la carpeta según el Windows, doble clic a "INICIAR_SISTEMA.bat" y factura.

📁 2_Archivos_Comprimidos_ZIP\\
   Contiene los bloques sellados. Úsalos si un antivirus rebelde te bloquea
   copiar archivos sueltos, o si necesitas enviar el sistema por WhatsApp/Correo.

📁 3_Manuales_y_Documentacion\\
   Toda la literatura técnica. Contiene los atajos de teclado para capacitar al
   cajero y las reglas de inmutabilidad para futuros programadores.

📁 4_Instaladores_InnoSetup\\
   Scripts fuente listos para compilar en Inno Setup si el cliente exige
   una instalación clásica (Setup.exe) con permisos nativos de base de datos.

===============================================================================
SOFTWARE PROPIEDAD DE PUNPRO SYSTEMS - LICENCIA DE DESPLIEGUE ELITE 2026
===============================================================================
"""
    with open(os.path.join(catorta, "GUIA_RAPIDA_DEL_PENDRIVE.txt"), "w", encoding="utf-8") as f:
        f.write(guia_content)
    print("  ✅ Guía de Pendrive generada.")

    print("\n[5/5] Sincronización Finalizada.")
    print("="*60)
    print("✅ RESPALDO Y EMPAQUETADO COMPLETADOS CON EXITO")
    print("="*60)
    print("Ve a la raíz de tu proyecto. Encontraras la súper carpeta llamada:")
    print("     📁 CATORTA_USB_PUNPRO/")
    print("¡Listo para copiar a tu Pendrive USB!")
    print("="*60)

if __name__ == "__main__":
    crear_respaldo_total()
