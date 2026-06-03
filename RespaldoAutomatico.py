import os
import shutil
import zipfile
import datetime
import logging
import sys

# Configuración básica de log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - RESPALDO - %(levelname)s - %(message)s')

def realizar_respaldo():
    print("========================================")
    print("      SISTEMA DE RESPALDO SEGURO")
    print("========================================\n")
    
    # 1. Determinar rutas
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backups_dir = os.path.join(base_dir, "backups")
    
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)
        logging.info(f"Carpeta de respaldos creada en: {backups_dir}")
        
    # Archivos críticos a respaldar
    db_file = os.path.join(base_dir, "AQVGI.db")
    config_file = os.path.join(base_dir, "config.json")
    
    if not os.path.exists(db_file):
        logging.error(f"¡ATENCIÓN! No se encontró la base de datos principal: {db_file}")
        input("Presione ENTER para salir...")
        return
        
    # 2. Nombrar el archivo de respaldo con fecha y hora
    fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"Respaldo_TPV_{fecha_str}.zip"
    zip_path = os.path.join(backups_dir, zip_filename)
    
    logging.info(f"Iniciando compresión de archivos críticos...")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Respaldar BD
            zipf.write(db_file, arcname="AQVGI.db")
            logging.info(" - AQVGI.db empaquetado exitosamente.")
            
            # Respaldar config si existe
            if os.path.exists(config_file):
                zipf.write(config_file, arcname="config.json")
                logging.info(" - config.json empaquetado exitosamente.")
                
        print("\n[OK] RESPALDO COMPLETADO CON EXITO!")
        print(f"[*] Archivo guardado en: {zip_path}")
        print(f"Tamano: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB\n")
        
    except Exception as e:
        logging.error(f"Fallo critico al crear el respaldo: {e}")
        
    print("========================================")
    input("Presione ENTER para cerrar...")

if __name__ == "__main__":
    realizar_respaldo()
