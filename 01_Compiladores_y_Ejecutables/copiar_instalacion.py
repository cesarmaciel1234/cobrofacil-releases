import os
import shutil
import time
import sys

src = r"c:\Users\cesar\OneDrive\Desktop\tpv pro 2026\dist\CobroFacil_POS"
dst = r"C:\Users\cesar\CobroFacil_POS_Install"

print("Iniciando copia de archivos...")

# Intentar matar cualquier proceso de CobroFacil_POS o subprocesos o python (evitando matarnos a nosotros mismos)
try:
    import psutil
    my_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid = proc.info['pid']
            name = proc.info['name'].lower()
            if pid != my_pid and ('cobrofacil' in name or 'mysqld' in name or 'python' in name):
                psutil.Process(pid).terminate()
                print(f"Proceso finalizado: {proc.info['name']} (PID {pid})")
        except:
            pass
except Exception as e:
    print(f"Error al buscar procesos activos: {e}")

time.sleep(2)

# Intentar borrar la carpeta de destino _internal si existe para hacer una copia limpia
internal_dst = os.path.join(dst, "_internal")
if os.path.exists(internal_dst):
    print("Eliminando carpeta _internal antigua para evitar mezclar versiones...")
    for attempt in range(5):
        try:
            shutil.rmtree(internal_dst)
            print("Carpeta _internal eliminada correctamente.")
            break
        except Exception as e:
            print(f"No se pudo eliminar _internal en el intento {attempt+1}: {e}")
            time.sleep(1)

# Copiar todo
for root, dirs, files in os.walk(src):
    rel_path = os.path.relpath(root, src)
    target_dir = os.path.join(dst, rel_path) if rel_path != "." else dst
    
    os.makedirs(target_dir, exist_ok=True)
    
    for file in files:
        src_file = os.path.join(root, file)
        dst_file = os.path.join(target_dir, file)
        
        copied = False
        for attempt in range(5):
            try:
                shutil.copy2(src_file, dst_file)
                copied = True
                break
            except PermissionError:
                print(f"Archivo bloqueado, reintentando: {dst_file}")
                time.sleep(0.5)
            except Exception as e:
                print(f"Error copiando {src_file}: {e}")
                break
        if not copied:
            print(f"❌ ¡ERROR CRÍTICO! No se pudo copiar {src_file} a {dst_file}")
            sys.exit(1)

print("Copia completada exitosamente!")
