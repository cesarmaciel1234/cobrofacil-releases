# -*- coding: utf-8 -*-
import os
import sys
import shutil
import zipfile
import glob
import datetime

def print_header(title):
    print("\n" + "="*70)
    print(f"🛡️  {title}")
    print("="*70)

def restaurar_datos_criticos():
    print_header("RESTAURAR BASE DE DATOS Y CONFIGURACIÓN (REPORTE Z)")
    
    # 1. Buscar respaldos
    backups_pattern = os.path.join("backups", "Respaldo_*")
    backups = sorted(glob.glob(backups_pattern), reverse=True)
    
    if not backups:
        print("❌ ERROR: No se encontraron carpetas de respaldo en 'backups/'.")
        print("Primero debes ejecutar 'backup_total.bat' para crear un punto de restauración.")
        return False
        
    print("Puntos de restauración disponibles:")
    for idx, b_path in enumerate(backups):
        folder_name = os.path.basename(b_path)
        # Mostrar fecha formateada
        date_str = folder_name.replace("Respaldo_", "")
        print(f"  [{idx}] {folder_name} ({date_str})")
        
    try:
        sel = input("\n👉 Selecciona el número del respaldo a restaurar (o Enter para cancelar): ")
        if not sel.strip():
            print("❌ Operación cancelada.")
            return False
        sel_idx = int(sel)
        if sel_idx < 0 or sel_idx >= len(backups):
            print("❌ Opción inválida.")
            return False
    except ValueError:
        print("❌ Entrada no válida.")
        return False
        
    target_backup = backups[sel_idx]
    critical_dir = os.path.join(target_backup, "datos_criticos")
    
    db_src = os.path.join(critical_dir, "punpro.db")
    config_src = os.path.join(critical_dir, "config.json")
    
    if not os.path.exists(db_src) and not os.path.exists(config_src):
        print("❌ ERROR: No se encontraron datos críticos en este punto de restauración.")
        return False
        
    confirm = input(f"\n⚠️  ¿Seguro que deseas sobreescribir los datos actuales con los del respaldo {os.path.basename(target_backup)}? (S/N): ")
    if confirm.upper() != 'S':
        print("❌ Operación cancelada.")
        return False
        
    # Hacer respaldo temporal de seguridad antes de sobreescribir
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_bk_dir = os.path.join("backups", f"SEGURIDAD_PRE_RESTORE_{now}")
    os.makedirs(temp_bk_dir, exist_ok=True)
    
    print("\n📦 Guardando estado actual de seguridad...")
    if os.path.exists("punpro.db"):
        shutil.copy2("punpro.db", os.path.join(temp_bk_dir, "punpro.db"))
    if os.path.exists("config.json"):
        shutil.copy2("config.json", os.path.join(temp_bk_dir, "config.json"))
    print(f"✅ Estado actual salvado en: {temp_bk_dir}")
    
    # Restaurar
    print("\n⏩ Copiando archivos de restauración...")
    restored_db = False
    restored_config = False
    
    if os.path.exists(db_src):
        shutil.copy2(db_src, "punpro.db")
        print("   ✅ Base de datos (punpro.db) restaurada.")
        restored_db = True
        
    if os.path.exists(config_src):
        shutil.copy2(config_src, "config.json")
        print("   ✅ Configuración (config.json) restaurada.")
        restored_config = True
        
    if restored_db or restored_config:
        print("\n🎉 ¡DATOS RESTAURADOS CON ÉXITO!")
        return True
    else:
        print("❌ No se pudieron copiar los archivos.")
        return False

def restaurar_codigo_admin7():
    print_header("RECURSO DE ROLLBACK: RESTAURAR ARCHIVO DE CÓDIGO (admin7_cierre.py)")
    
    # Buscar archivos ZIP en el proyecto
    zip_files = []
    
    # 1. Zip del raíz
    if os.path.exists("PROYECTO_COMPLETO_RESPALDO.zip"):
        zip_files.append(("Maestro (Raíz)", "PROYECTO_COMPLETO_RESPALDO.zip"))
        
    # 2. Zip de la Catorta
    catorta_zip = os.path.join("CATORTA_USB_PUNPRO", "2_Archivos_Comprimidos_ZIP", "PROYECTO_COMPLETO_RESPALDO.zip")
    if os.path.exists(catorta_zip):
        zip_files.append(("Catorta USB", catorta_zip))
        
    # 3. Zips en la carpeta backups u otros lugares
    for z in glob.glob("backups/**/*.zip", recursive=True):
        zip_files.append((f"Backup ({os.path.basename(z)})", z))
        
    if not zip_files:
        print("❌ ERROR: No se encontraron archivos ZIP de respaldo en el proyecto.")
        return False
        
    print("Archivos ZIP de respaldo disponibles:")
    valid_zips = []
    for idx, (label, z_path) in enumerate(zip_files):
        try:
            with zipfile.ZipFile(z_path, 'r') as zf:
                namelist = zf.namelist()
                # Verificar si admin7_cierre.py está dentro del zip
                has_admin7 = any("admin7_cierre.py" in name for name in namelist)
                status_str = "🟢 Contiene admin7_cierre.py" if has_admin7 else "🔴 NO contiene el archivo"
                size_mb = os.path.getsize(z_path) / (1024 * 1024)
                print(f"  [{idx}] {label} - {z_path} ({size_mb:.2f} MB) [{status_str}]")
                if has_admin7:
                    valid_zips.append((idx, z_path))
        except Exception as e:
            print(f"  [{idx}] {label} - {z_path} (No se pudo leer: {e})")
            
    if not valid_zips:
        print("\n❌ ERROR: Ninguno de los ZIP contiene 'admin7_cierre.py'.")
        return False
        
    try:
        sel = input("\n👉 Selecciona el número del ZIP para extraer admin7_cierre.py (o Enter para cancelar): ")
        if not sel.strip():
            print("❌ Operación cancelada.")
            return False
        sel_idx = int(sel)
        z_path = next((path for idx, path in valid_zips if idx == sel_idx), None)
        if not z_path:
            print("❌ Selección inválida.")
            return False
    except ValueError:
        print("❌ Entrada no válida.")
        return False
        
    # Encontrar la ruta exacta de admin7_cierre.py dentro del ZIP
    exact_zip_path = None
    with zipfile.ZipFile(z_path, 'r') as zf:
        for name in zf.namelist():
            if "admin7_cierre.py" in name:
                exact_zip_path = name
                break
                
    if not exact_zip_path:
        print("❌ ERROR: No se encontró la ruta exacta del archivo dentro del ZIP.")
        return False
        
    confirm = input(f"\n⚠️  ¿Seguro que deseas sobreescribir src/admin/admin7_cierre.py con la versión extraída de {os.path.basename(z_path)}? (S/N): ")
    if confirm.upper() != 'S':
        print("❌ Operación cancelada.")
        return False
        
    # Respaldar el archivo actual de código antes de sobreescribir
    target_file = os.path.join("src", "admin", "admin7_cierre.py")
    if os.path.exists(target_file):
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        code_backup = f"{target_file}.bk_{now}"
        shutil.copy2(target_file, code_backup)
        print(f"📦 Archivo actual guardado como respaldo en: {code_backup}")
        
    # Extraer
    print("\n⏩ Extrayendo y reemplazando archivo de código...")
    try:
        with zipfile.ZipFile(z_path, 'r') as zf:
            # Leer el contenido del archivo dentro del zip
            content = zf.read(exact_zip_path)
            # Escribir en el destino
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            with open(target_file, 'wb') as f:
                f.write(content)
        print(f"🎉 ¡ARCHIVO {os.path.basename(target_file)} RESTAURADO CON ÉXITO DESDE EL ZIP!")
        return True
    except Exception as e:
        print(f"❌ Error al extraer el archivo: {e}")
        return False

def rutina_diagnostico():
    print_header("RUTINA DE DIAGNÓSTICO Y LIMPIEZA EXPRESS")
    
    # 1. Limpieza de temporales y caches
    print("🧹 Limpiando caché __pycache__ y temporales...")
    cleaned_count = 0
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                cleaned_count += 1
            except:
                pass
                
    # Borrar crash.log y archivos temporales residuales
    temp_files = ["crash.log", "crash-cesar.log", "test_stress.py"]
    for tf in temp_files:
        if os.path.exists(tf):
            try:
                os.remove(tf)
                print(f"   ✅ Archivo temporal eliminado: {tf}")
            except:
                pass
                
    print(f"   ✅ Carpetas de cache de Python depuradas: {cleaned_count}")
    
    # 2. Verificar integridad del catálogo de base de datos
    print("\n🗄️  Verificando base de datos 'punpro.db'...")
    if os.path.exists("punpro.db"):
        try:
            import sqlite3
            conn = sqlite3.connect("punpro.db")
            cursor = conn.cursor()
            # Chequear pragma integrity
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()[0]
            print(f"   ✅ Integridad física: {res.upper()}")
            
            # Contar tablas importantes
            cursor.execute("SELECT COUNT(*) FROM productos;")
            prod_count = cursor.fetchone()[0]
            print(f"   ✅ Productos catalogados: {prod_count}")
            
            cursor.execute("SELECT COUNT(*) FROM ventas;")
            ventas_count = cursor.fetchone()[0]
            print(f"   ✅ Ventas registradas: {ventas_count}")
            
            cursor.execute("SELECT COUNT(*) FROM movimientos_caja WHERE tipo='CIERRE_Z';")
            cierres_z = cursor.fetchone()[0]
            print(f"   ✅ Cierres Z históricos: {cierres_z}")
            
            conn.close()
        except Exception as e:
            print(f"   ❌ Error al inspeccionar la base de datos: {e}")
    else:
        print("   ❌ ADVERTENCIA: No se encontró punpro.db en el directorio raíz.")
        
    print("\n🏁 Diagnóstico y limpieza completados con éxito.")

def main():
    while True:
        print_header("SISTEMA DE RESTAURACIÓN MAESTRO - CAJAFACIL PRO")
        print("Selecciona una opción para proceder:")
        print("  [1] Restaurar Base de Datos y Configuración (desde backups/Respaldo_*)")
        print("  [2] Rollback de Código: Extraer admin7_cierre.py original (desde un ZIP)")
        print("  [3] Ejecutar Diagnóstico, Optimización y Limpieza de Caches")
        print("  [4] Salir")
        
        try:
            opt = input("\n👉 Opción: ")
            if opt == '1':
                restaurar_datos_criticos()
            elif opt == '2':
                restaurar_codigo_admin7()
            elif opt == '3':
                rutina_diagnostico()
            elif opt == '4':
                print("\n👋 ¡Hasta luego! Que tengas un excelente día de ventas.")
                break
            else:
                print("❌ Opción inválida. Inténtalo de nuevo.")
        except KeyboardInterrupt:
            print("\n👋 Saliendo de forma segura...")
            break
        except Exception as e:
            print(f"❌ Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    main()
