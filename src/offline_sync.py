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
        self.sync_worker.start()

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
        from src.database import db_manager
        import sqlite3
        
        while True:
            time.sleep(15)
            
            # Chequear si estamos en red (si es local, también sincroniza)
            # Primero ver si hay pendientes
            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    queue = json.load(f)
            except:
                queue = []
                
            if not queue:
                continue
                
            logger.info(f"Intentando sincronizar {len(queue)} ventas offline...")
            
            # Intentar conexión
            if db_manager.db_path.startswith("\\\\") or db_manager.db_path.startswith("//"):
                host = db_manager.db_path[2:].replace("/", "\\").split("\\")[0]
                import socket
                try:
                    socket.create_connection((host, 445), timeout=1.5).close()
                except Exception:
                    logger.warning("Red LAN inaccesible. Sincronización pospuesta.")
                    continue
            
            # Intentamos vaciar
            exitosas = []
            for i, record in enumerate(queue):
                # Guardado directo (cuidado con recursión si falla en el save, 
                # así que usamos la inserción raw o llamamos al manager pero 
                # marcando que estamos sincando)
                venta = record["venta_data"]
                items = record["items"]
                try:
                    conn = sqlite3.connect(db_manager.db_path, timeout=10.0)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, usuario, metodo_pago, caja_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        venta.get("total", 0),
                        venta.get("pago_con", 0),
                        venta.get("cambio", 0),
                        venta.get("pago_efectivo", 0),
                        venta.get("pago_otro", 0),
                        venta.get("usuario", "admin"),
                        venta.get("metodo_pago", "Efectivo"),
                        venta.get("caja_id", 1)
                    ))
                    id_venta = cursor.lastrowid
                    
                    for item in items:
                        cursor.execute("""
                            INSERT INTO detalles_ventas (id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            id_venta,
                            item.get("id_producto", ""),
                            item.get("nombre", ""),
                            item.get("cantidad", 1),
                            item.get("precio_unitario", 0),
                            item.get("subtotal", 0)
                        ))
                    
                    conn.commit()
                    conn.close()
                    exitosas.append(i)
                except Exception as e:
                    logger.error(f"Error sincronizando venta offline: {e}")
                    break # Parar y reintentar luego
            
            # Remover las sincronizadas
            if exitosas:
                queue = [q for idx, q in enumerate(queue) if idx not in exitosas]
                try:
                    with open(self.queue_file, "w", encoding="utf-8") as f:
                        json.dump(queue, f, indent=4)
                    logger.info(f"{len(exitosas)} ventas sincronizadas exitosamente.")
                except Exception as e:
                    logger.error(f"Error actualizando cola post-sync: {e}")

offline_sync_manager = OfflineSync()
