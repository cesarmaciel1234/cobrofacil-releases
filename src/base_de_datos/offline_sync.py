import json
import os
import threading
import time
from src.utils.paths import get_base_path
import logging

logger = logging.getLogger("PunPro")

class OfflineSync:
    def __init__(self):
        self.base_path = get_base_path()
        self.queue_file = os.path.join(self.base_path, "offline_queue.json")
        self._ensure_queue_file()
        
        self.sync_worker = threading.Thread(target=self._sync_loop, daemon=True)
        # self.sync_worker.start() # Deshabilitado temporalmente para pruebas de crash (0x8001010d) a los 15s

    def _ensure_queue_file(self):
        if not os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(f"No se pudo crear offline_queue: {e}")

    def guardar_venta_offline(self, venta_data, items):
        """Guarda la venta en el JSON local cuando la LAN falla."""
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)
            
            queue.append({
                "venta_data": venta_data,
                "items": items,
                "timestamp": time.time()
            })
            
            with open(self.queue_file, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=4)
            logger.info("Venta guardada en BUFFER OFFLINE.")
        except Exception as e:
            logger.error(f"Error escribiendo en buffer offline: {e}")

    def _sync_loop(self):
        """Intenta sincronizar cada 15 segundos si hay red."""
        from src.base_de_datos.database import db_manager
        
        while True:
            time.sleep(15)
            
            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    queue = json.load(f)
            except:
                queue = []
                
            if not queue:
                continue
                
            logger.info(f"Intentando sincronizar {len(queue)} ventas offline...")
            
            exitosas = []
            for i, record in enumerate(queue):
                venta = record["venta_data"]
                items = record["items"]
                
                # Intentar sincronizar usando la abstracción de base de datos
                success = db_manager.sync_venta_to_master(venta, items)
                if success:
                    exitosas.append(i)
                else:
                    logger.warning("Fallo en sincronización. Se reintentará en el próximo ciclo.")
                    break # Si falla una, detenemos y reintentamos luego para mantener orden
            
            if exitosas:
                queue = [q for idx, q in enumerate(queue) if idx not in exitosas]
                try:
                    with open(self.queue_file, "w", encoding="utf-8") as f:
                        json.dump(queue, f, indent=4)
                    logger.info(f"{len(exitosas)} ventas sincronizadas exitosamente.")
                except Exception as e:
                    logger.error(f"Error actualizando cola post-sync: {e}")

offline_sync_manager = OfflineSync()
