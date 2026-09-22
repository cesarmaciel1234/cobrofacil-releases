from __future__ import annotations

from src.config import config
from src.central_red_global.servidor.rol.ip import probe_mariadb
from src.central_red_global.servidor.rol.mariadb_local import intentar_arrancar_mariadb_local


def convertir_en_maestra(logger):
    from src.base_de_datos.database import db_manager

    prev_engine = getattr(db_manager, "db_engine_type", "sqlite")
    prev_host = (config.get("db_host") or "").strip() or "localhost"
    prev_cfg_engine = config.get("db_engine", "sqlite")
    prev_cfg_master = config.get("is_master", True)
    prev_slave = bool(config.get("carteleria_is_slave"))
    prev_preferred = str(
        config.get("preferred_master_ip") or config.data.get("preferred_master_ip") or ""
    ).strip()
    prev_carteleria_ip = str(config.get("carteleria_master_ip") or "").strip()
    prev_auto_store = config.get("auto_start_store_server", True)

    def _rollback(msg_extra: str = ""):
        try:
            config.set("is_master", prev_cfg_master)
            config.set("db_engine", prev_cfg_engine)
            config.set("db_host", prev_host)
            config.set("carteleria_is_slave", prev_slave)
            config.set("auto_start_store_server", prev_auto_store)
            if prev_preferred:
                config.data["preferred_master_ip"] = prev_preferred
            if prev_carteleria_ip:
                config.set("carteleria_master_ip", prev_carteleria_ip)
            config.save()
        except Exception:
            pass
        try:
            if prev_engine == "mariadb" and prev_host not in ("", "localhost", "127.0.0.1"):
                db_manager.reconectar_mariadb(prev_host)
            elif prev_engine == "mariadb" and probe_mariadb("127.0.0.1"):
                db_manager.reconectar_mariadb("localhost")
            else:
                db_manager.reconectar_local()
        except Exception as e:
            logger.error(f"Rollback tras fallar maestra: {e}")
        return False, msg_extra

    try:
        if not probe_mariadb("127.0.0.1"):
            logger.info("MariaDB local no responde; intentando arrancar mysqld portable...")
            if not intentar_arrancar_mariadb_local(logger):
                hint_slave = ""
                remote = prev_preferred or prev_carteleria_ip or (
                    prev_host if prev_host not in ("", "localhost", "127.0.0.1") else ""
                )
                if remote:
                    hint_slave = (
                        f"\n\nEsta PC seguía como esclava de {remote}. "
                        "Volvé a 'Convertir en ESCLAVA' con esa IP si hace falta."
                    )
                return (
                    False,
                    "No hay MariaDB en esta PC (localhost:3306).\n\n"
                    "Para ser MAESTRA necesitás el Servidor de Tienda / MariaDB "
                    "instalado y corriendo aquí.\n"
                    "En una cartelería o caja esclava no uses 'Convertir en MAESTRA'."
                    + hint_slave,
                )

        config.set("is_master", True)
        config.set("db_engine", "mariadb")
        config.set("db_host", "localhost")
        config.set("auto_start_store_server", True)
        try:
            config.set("carteleria_is_slave", False)
            config.set("carteleria_master_ip", "")
            config.data["preferred_master_ip"] = ""
            config.save()
        except Exception:
            pass

        db_manager.reconectar_mariadb("localhost")
        if not db_manager.is_connected():
            return _rollback(
                "MariaDB local abrió el puerto pero no responde consultas.\n"
                "Se mantuvo el modo anterior."
            )

        try:
            from src.central_red_global.lan_server import init_lan_server

            init_lan_server()
        except Exception as e:
            logger.debug(f"LAN tras MAESTRA: {e}")
        try:
            from src.central_red_global.servidor.autostart import set_os_autostart

            set_os_autostart(True)
        except Exception:
            pass

        return True, "Configurado exitosamente como MAESTRA (Servidor MariaDB Local)."
    except Exception as e:
        logger.error(f"Error convirtiendo a maestra: {e}")
        return _rollback(
            f"No se pudo activar MAESTRA local:\n{e}\n\nSe restauró el modo anterior."
        )
