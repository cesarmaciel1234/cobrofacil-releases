import os
import glob
import zipfile
from datetime import datetime
from src.logger import logger
from src.utils.paths import get_base_path
from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

def comprimir_backups_del_dia(fecha_str=None):
    """
    Comprime todos los backups incrementales o periódicos del día en un solo archivo ZIP
    para ahorrar espacio y dejar el archivo 'diario' limpio.
    Se dispara típicamente al hacer el CIERRE_Z o en el mantenimiento nocturno.
    """
    if not fecha_str:
        fecha_str = datetime.now().strftime('%Y-%m-%d')
        
    for target_dir in AutoBlindajeDB.get_backup_directories():
        if not os.path.exists(target_dir):
            continue
            
        # Buscar backups de hoy
        patron_diario = f"*_{fecha_str}*.db"
        patron_diario_sql = f"*_{fecha_str}*.sql"
        
        archivos = glob.glob(os.path.join(target_dir, patron_diario)) + glob.glob(os.path.join(target_dir, patron_diario_sql))
        
        # Filtramos zips existentes para no re-comprimirlos o crashear
        archivos = [a for a in archivos if not a.endswith('.zip')]
        
        if not archivos:
            logger.info(f"💾 Compresión: No hay backups sueltos de {fecha_str} en {target_dir}")
            continue
            
        zip_path = os.path.join(target_dir, f"backup_consolidado_{fecha_str}.zip")
        
        logger.info(f"💾 Comprimiendo {len(archivos)} backups en {zip_path}...")
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for arc in archivos:
                    nombre_base = os.path.basename(arc)
                    zipf.write(arc, nombre_base)
            with zipfile.ZipFile(zip_path, "r") as chequeo:
                ilegible = chequeo.testzip() is not None
            if ilegible:
                logger.error(f"Zip del día ilegible, no se borra nada: {zip_path}")
                continue

            # El diario rolling no se borra: es la copia que se restaura.
            for arc in archivos:
                nombre = os.path.basename(arc).lower()
                if nombre.startswith("backup_diario_") and "_ventas" not in nombre:
                    continue
                try:
                    os.remove(arc)
                except Exception as e:
                    logger.warning(f"No se pudo borrar el backup suelto {arc}: {e}")
                    
            logger.info(f"✅ Compresión exitosa para {fecha_str} en {target_dir}")
        except Exception as e:
            logger.error(f"❌ Error al comprimir backups del día: {e}")
