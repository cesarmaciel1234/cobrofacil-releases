import sys
import socket
import json as _json
from src.logger import logger
from src.base_de_datos.core.mariadb_probe import puerto_mariadb_abierto

class NetworkDBService:
    @staticmethod
    def boot(db_manager):
        # 1. Maestro: Iniciar servidor y backups
        if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb" and getattr(db_manager, "is_master", False):
            host = getattr(db_manager.mariadb_engine, "host", "127.0.0.1") if db_manager.mariadb_engine else "127.0.0.1"
            if host in ("localhost", "127.0.0.1", socket.gethostname().lower()):
                from src.services.mariadb_controller import mariadb_controller
                logger.info("NetworkDBService: Arrancando Auto-Servidor MariaDB...")
                mariadb_controller.start_server()

            _skip_blindaje = False
            try:
                from src.utils.candados import is_store_server_running
                if is_store_server_running() and "--server" not in sys.argv:
                    _skip_blindaje = True
            except Exception:
                pass

            if not _skip_blindaje:
                try:
                    from src.base_de_datos.autoblindaje_db import AutoBlindajeDB
                    AutoBlindajeDB.verificar_y_respaldar_diario("mariadb", host)
                except Exception as e:
                    logger.warning(f"Aviso en autoblindaje MariaDB: {e}")
                
                try:
                    from src.cerebro_global.backup_cerebro import cerebro_backup
                    cerebro_backup.start("mariadb", host)
                except Exception as e_cb:
                    logger.warning(f"Aviso CerebroBackup: {e_cb}")

        # 2. Esclava Offline: Auto-descubrimiento y Reintentos
        if getattr(db_manager, "_forced_local_offline", False):
            master_ok = False
            logger.info("NetworkDBService: Intentando auto-descubrir maestra en la red...")
            try:
                sock_scan = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock_scan.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock_scan.settimeout(2.0)
                sock_scan.sendto(b"PUNPRO_DISCOVER", ("255.255.255.255", 37020))
                data, addr = sock_scan.recvfrom(1024)
                sock_scan.close()
                info = _json.loads(data.decode("utf-8"))
                from src.central_red_global.lan_server import es_anuncio_tienda

                if es_anuncio_tienda(info):
                    discovered_host = info.get("server_ip", addr[0])
                    try:
                        s_self = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s_self.connect(("8.8.8.8", 80))
                        mi_ip = s_self.getsockname()[0]
                        s_self.close()
                    except Exception:
                        mi_ip = ""
                    
                    from src.config import config
                    old_host = config.get("db_host", "")
                    if discovered_host and discovered_host not in (mi_ip, "127.0.0.1", "localhost", old_host):
                        logger.info(f"Nueva Maestra auto-descubierta en {discovered_host}.")
                        config.set("db_host", discovered_host)
                        config.set("is_master", False)
                        config.set("api_url", f"http://{discovered_host}:8000")
                        config.save()
                        
                        from src.db_engines.mariadb_engine import MariaDBEngine
                        new_engine = MariaDBEngine(host=discovered_host)
                        try:
                            conn = new_engine.get_connection()
                            conn._conn.ping()
                            master_ok = True
                            
                            db_manager.db_path = "mariadb://" + discovered_host
                            db_manager.db_engine_type = "mariadb"
                            db_manager._forced_local_offline = False
                            db_manager.is_master = False
                            db_manager.mariadb_engine = new_engine
                        except Exception:
                            master_ok = False
                    else:
                        logger.warning(f"Discovery no usable ({discovered_host}); offline local.")
            except Exception as e:
                logger.info(f"Auto-descubrimiento falló: {e}")

            if not master_ok:
                try:
                    from PyQt6.QtCore import QTimer
                    from src.config import config
                    host_to_retry = config.get("db_host", "")
                    if not host_to_retry:
                        # Fallback for host
                        host_to_retry = getattr(db_manager, "db_path", "").replace("mariadb://", "")
                    
                    if host_to_retry:
                        def _retry_mariadb_connection():
                            try:
                                if puerto_mariadb_abierto(host_to_retry, 2.0):
                                    logger.info(f"Servidor MariaDB en {host_to_retry} ahora disponible, reconectando...")
                                    db_manager.reconectar_mariadb(host_to_retry)
                            except Exception as retry_e:
                                logger.debug(f"Reintento conexión falló: {retry_e}")
                        
                        QTimer.singleShot(30000, _retry_mariadb_connection)
                except Exception as timer_e:
                    logger.warning(f"No se pudo programar reintento: {timer_e}")
