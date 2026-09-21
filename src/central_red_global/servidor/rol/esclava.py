from __future__ import annotations

import time

from src.config import config
from src.central_red_global.servidor.rol.apagar import detener_servidor_tienda_local
from src.central_red_global.servidor.rol.constantes import SLAVE_FAIL_COOLDOWN_SEC
from src.central_red_global.servidor.rol.ip import es_ip_de_esta_pc, normalizar_ip, probe_mariadb

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

_last_slave_fail_at: dict[str, float] = {}


def convertir_en_esclava(logger, ip_maestra):
    ip_maestra = normalizar_ip(ip_maestra)

    if not ip_maestra or ip_maestra.lower() in ("localhost", "127.0.0.1"):
        return False, "Debes ingresar una IP válida de red (ej: 192.168.0.100)."
    if es_ip_de_esta_pc(ip_maestra):
        return False, (
            "Esa IP es esta misma PC. La esclava tiene que ser otra máquina.\n"
            "En esta PC dejá el modo MAESTRA o usá la IP de la caja servidor."
        )

    now = time.time()
    last_fail = _last_slave_fail_at.get(ip_maestra, 0)
    remaining = SLAVE_FAIL_COOLDOWN_SEC - (now - last_fail)
    if remaining > 0:
        return (
            False,
            f"La Maestra en {ip_maestra} no respondió hace poco. "
            f"Reintentá en {int(remaining)}s o verificá que esté encendida.",
        )

    if not probe_mariadb(ip_maestra):
        _last_slave_fail_at[ip_maestra] = now
        config.data["preferred_master_ip"] = ip_maestra
        try:
            config.save()
        except Exception:
            pass
        return (
            False,
            f"No hay MariaDB en {ip_maestra}:3306.\n\n"
            "La PC Maestra parece apagada o fuera de la red.\n"
            "Seguís en modo local (SQLite) sin cambios.",
        )

    prev_master = getattr(db_manager, "is_master", True)
    prev_engine = getattr(db_manager, "db_engine_type", "sqlite")
    prev_host = config.get("db_host", "") or "localhost"
    prev_cfg_engine = config.get("db_engine", "sqlite")
    prev_cfg_master = config.get("is_master", True)

    try:
        config.set("is_master", False)
        config.set("db_engine", "mariadb")
        config.set("db_host", ip_maestra)
        config.data["preferred_master_ip"] = ip_maestra

        db_manager.reconectar_mariadb(ip_maestra)

        if db_manager.is_connected():
            _last_slave_fail_at.pop(ip_maestra, None)
            try:
                config.set("carteleria_master_ip", ip_maestra)
                config.set("carteleria_is_slave", True)
                config.set("auto_start_store_server", False)
                config.set("api_url", f"http://{ip_maestra}:8000")
                config.data["preferred_master_ip"] = ip_maestra
                config.data["is_master"] = False
                config.data["db_host"] = ip_maestra
                config.save()
            except Exception:
                pass
            def _apagar_servidor_local():
                try:
                    detener_servidor_tienda_local()
                except Exception:
                    pass
                try:
                    from src.central_red_global.servidor.autostart import set_os_autostart

                    set_os_autostart(False)
                except Exception:
                    pass

            try:
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(500, _apagar_servidor_local)
            except Exception:
                _apagar_servidor_local()
            try:
                from src.central_red_global.sync_tienda import al_conectar_esclava

                al_conectar_esclava()
            except Exception as e_sync:
                logger.warning(f"Sync al conectar esclava (se ignora): {e_sync}")
            return True, f"Conexión exitosa a la Maestra en {ip_maestra}."

        _last_slave_fail_at[ip_maestra] = time.time()
        config.set("is_master", prev_cfg_master)
        config.set("db_engine", prev_cfg_engine)
        config.set("db_host", prev_host)
        if prev_engine == "mariadb" and prev_host not in ("", "localhost", "127.0.0.1"):
            db_manager.reconectar_mariadb(prev_host)
        else:
            db_manager.reconectar_local()
        return (
            False,
            "El puerto 3306 responde pero no se pudo usar la base.\n"
            "Verificá usuario/clave MariaDB en la Maestra. Se mantuvo el modo anterior.",
        )
    except Exception as e:
        _last_slave_fail_at[ip_maestra] = time.time()
        logger.error(f"Error convirtiendo a esclava: {e}")
        try:
            config.set("is_master", prev_cfg_master)
            config.set("db_engine", prev_cfg_engine)
            config.set("db_host", prev_host)
            if prev_master and prev_engine != "mariadb":
                db_manager.reconectar_local()
        except Exception:
            pass
        return False, f"Error inesperado: {e}"
