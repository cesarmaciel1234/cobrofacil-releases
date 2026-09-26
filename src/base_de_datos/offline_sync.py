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

    def guardar_venta_offline(self, venta_data, items, fiado=None):
        """Guarda la venta en el JSON local cuando la LAN falla."""
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)

            registro = {
                "venta_data": venta_data,
                "items": items,
                "timestamp": time.time(),
            }
            if fiado:
                registro["fiado"] = fiado
            queue.append(registro)

            with open(self.queue_file, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=4)
            logger.info("Venta guardada en BUFFER OFFLINE.")
            self._avisar_venta_sin_maestra(venta_data)
        except Exception as e:
            logger.error(f"Error escribiendo en buffer offline: {e}")

    def _avisar_venta_sin_maestra(self, venta_data):
        """Nexus escucha este aviso en la LAN. No espera a que la venta suba a la maestra."""
        datos = {
            "total": (venta_data or {}).get("total", 0),
            "metodo_pago": (venta_data or {}).get("metodo_pago", ""),
            "caja_id": (venta_data or {}).get("caja_id", 1),
            "request_id": (venta_data or {}).get("request_id") or "",
            "pago_efectivo": (venta_data or {}).get("pago_efectivo", 0),
            "pago_otro": (venta_data or {}).get("pago_otro", 0),
            "fuera_de_maestra": True,
        }
        try:
            from src.central_red_global.network_engine import get_network_engine

            engine = get_network_engine()
            if engine is not None:
                engine.broadcast("VENTA_NUEVA", datos)
                return
        except Exception as e:
            logger.warning(f"No se pudo avisar la venta por el motor de red: {e}")
        try:
            import socket
            from src.central_red_global.network_engine import NEXUS_UDP_PORT
            from src.config import config

            host = socket.gethostname()
            caja = datos["caja_id"] or config.get("caja_id", 1)
            payload = {
                "origen": f"{host}|cajero|caja{caja}",
                "tipo": "VENTA_NUEVA",
                "datos": datos,
                "ts": time.time(),
            }
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(
                    json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    ("255.255.255.255", NEXUS_UDP_PORT),
                )
            finally:
                sock.close()
        except Exception as e:
            logger.warning(f"Venta en cola; Nexus no recibió el aviso: {e}")

    def sync_pendientes(self):
        """Sincroniza ventas en offline_queue.json hacia la base de datos."""
        from src.base_de_datos.database import db_manager
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            queue = []
        if not queue:
            return 0

        logger.info(f"Sincronizando {len(queue)} ventas offline pendientes...")
        exitosas = []
        for i, record in enumerate(queue):
            if db_manager.sync_venta_to_master(
                record["venta_data"], record["items"], record.get("fiado")
            ):
                exitosas.append(i)
            else:
                break

        if exitosas:
            queue = [q for idx, q in enumerate(queue) if idx not in exitosas]
            try:
                with open(self.queue_file, "w", encoding="utf-8") as f:
                    json.dump(queue, f, indent=4)
                logger.info(f"{len(exitosas)} ventas offline sincronizadas.")
            except Exception as e:
                logger.error(f"Error actualizando cola post-sync: {e}")
        return len(exitosas)

    def _sync_loop(self):
        """Intenta sincronizar cada 15 segundos si hay red."""
        from src.base_de_datos.database import db_manager

        loop_counter = 0

        while True:
            time.sleep(15)
            loop_counter += 1

            if loop_counter % 8 == 0 and not db_manager.is_master:
                try:
                    from src.central_red_global.sync_tienda import bajar_pngs_de_maestra

                    bajar_pngs_de_maestra()
                except Exception:
                    pass
            # --- MODO OFFLINE EXTREMO: REPLICA DE PRODUCTOS ---
            # Cada ~5 minutos (20 iteraciones) si somos esclavos y estamos ONLINE (mariadb_engine existe)
            if loop_counter >= 20:
                loop_counter = 0
                if not db_manager.is_master and getattr(db_manager, 'mariadb_engine', None):
                    try:
                        # Descargar catálogo desde MariaDB
                        prods = db_manager.execute_query("SELECT id, codigo, nombre, precio, stock, categoria, es_pesable, cant_oferta, precio_oferta, tipo_unidad_oferta FROM productos")
                        if prods:
                            # Conectar al SQLite local (punpro.db)
                            import sqlite3
                            local_db_path = os.path.join(self.base_path, "punpro.db")
                            conn_loc = sqlite3.connect(local_db_path)
                            c_loc = conn_loc.cursor()

                            c_loc.execute("CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT, nombre TEXT, precio REAL, stock REAL, categoria TEXT, es_pesable INTEGER, cant_oferta REAL, precio_oferta REAL, tipo_unidad_oferta TEXT)")
                            c_loc.execute("DELETE FROM productos")

                            reg_prods = [
                                (p.get('id'), p.get('codigo'), p.get('nombre'), p.get('precio', 0),
                                 p.get('stock', 0), p.get('categoria', 'General'), p.get('es_pesable', 0),
                                 p.get('cant_oferta', 0), p.get('precio_oferta', 0), p.get('tipo_unidad_oferta', 'Kilos'))
                                for p in prods
                            ]

                            c_loc.executemany("INSERT INTO productos (id, codigo, nombre, precio, stock, categoria, es_pesable, cant_oferta, precio_oferta, tipo_unidad_oferta) VALUES (?,?,?,?,?,?,?,?,?,?)", reg_prods)
                            conn_loc.commit()
                            conn_loc.close()
                            logger.info("Modo Offline Extremo: Catálogo de productos sincronizado silenciosamente al respaldo local.")
                    except Exception as e_repl:
                        logger.warning(f"Modo Offline Extremo: Falló la réplica local de productos: {e_repl}")

            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    queue = json.load(f)
            except:
                queue = []

            if not queue:
                continue

            logger.info(f"Intentando sincronizar {len(queue)} ventas offline...")

            if getattr(db_manager, "_forced_local_offline", False) or getattr(db_manager, "db_engine_type", "") != "mariadb":
                host = ""
                try:
                    host = db_manager._host_tienda()
                except Exception:
                    host = ""
                if host and db_manager._puerto_maestra_vivo(host):
                    try:
                        db_manager.reconectar_mariadb(host)
                        db_manager.is_master = False
                    except Exception:
                        pass

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
