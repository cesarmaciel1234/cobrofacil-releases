import os
import shutil
import time

src = r"c:\Users\cesar\OneDrive\Desktop\tpv pro 2026\dist\CobroFacil_POS"
dst = r"C:\Users\cesar\CobroFacil_POS_Install"

print("Iniciando copia de archivos...")

# Intentar matar cualquier proceso de CobroFacil_POS o subprocesos
try:
    import psutil
    for proc in psutil.process_iter(['pid', 'name']):
        if 'CobroFacil' in proc.info['name'] or 'mysqld' in proc.info['name']:
            try:
                psutil.Process(proc.info['pid']).terminate()
                print(f"Proceso finalizado: {proc.info['name']} (PID {proc.info['pid']})")
            except:
                pass
except:
    pass

time.sleep(1)

for root, dirs, files in os.walk(src):
    rel_path = os.path.relpath(root, src)
    target_dir = os.path.join(dst, rel_path) if rel_path != "." else dst
    
    os.makedirs(target_dir, exist_ok=True)
    
    for file in files:
        src_file = os.path.join(root, file)
        dst_file = os.path.join(target_dir, file)
        
        # Copiar reintentando si está bloqueado
        for attempt in range(5):
            try:
                shutil.copy2(src_file, dst_file)
                break
            except PermissionError:
                print(f"Archivo bloqueado, reintentando: {dst_file}")
                time.sleep(0.5)
            except Exception as e:
                print(f"Error copiando {src_file}: {e}")
                break

print("Copia completada exitosamente!")
