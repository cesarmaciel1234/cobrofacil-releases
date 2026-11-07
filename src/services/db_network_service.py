import sys
import socket
from src.logger import logger

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

        elif (
            getattr(db_manager, "db_engine_type", "") == "mariadb"
            and not getattr(db_manager, "_forced_local_offline", False)
        ):
            eng = getattr(db_manager, "mariadb_engine", None)
            host = str(getattr(eng, "host", "") or "").strip()
            if host and host.lower() not in ("localhost", "127.0.0.1"):
                try:
                    from src.base_de_datos.autoblindaje_db import AutoBlindajeDB
                    AutoBlindajeDB.verificar_y_respaldar_diario("mariadb", host)
                except Exception as e:
                    logger.warning(f"Esclava: no se pudo traer el respaldo ({e})")
                try:
                    from src.cerebro_global.backup_cerebro import cerebro_backup
                    cerebro_backup.start("mariadb", host)
                    logger.info(f"Esclava: respaldo local cada 1 min desde {host}")
                except Exception as e_cb:
                    logger.warning(f"Esclava CerebroBackup: {e_cb}")

        # 2. Esclava: enlazar identidad y redescubrir la tienda fuera del hilo de UI.
        if not getattr(db_manager, "is_master", True):
            esta_offline = bool(getattr(db_manager, "_forced_local_offline", False))
            if esta_offline:
                logger.info("NetworkDBService: Buscando en la red la tienda ya enlazada...")

            def _descubrir_y_conectar():
                try:
                    from src.central_red_global.servidor.pareja.buscar import buscar

                    discovered_host = buscar()
                    if not discovered_host:
                        logger.info("NetworkDBService: no respondió una maestra enlazada.")
                        return
                    engine = getattr(db_manager, "mariadb_engine", None)
                    host_actual = str(getattr(engine, "host", "") or "")
                    if (
                        getattr(db_manager, "_forced_local_offline", False)
                        or getattr(db_manager, "db_engine_type", "") != "mariadb"
                        or host_actual != discovered_host
                    ):
                        db_manager.reconectar_mariadb(discovered_host)
                except Exception as e:
                    logger.info("NetworkDBService: descubrimiento/reconexión pendiente: %s", e)

            try:
                import threading

                threading.Thread(
                    target=_descubrir_y_conectar,
                    name="red-descubrir-arranque",
                    daemon=True,
                ).start()
            except Exception as e:
                logger.warning("NetworkDBService: no se pudo iniciar descubrimiento: %s", e)
