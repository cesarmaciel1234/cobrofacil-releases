"""Si la titular no contesta, la reserva pasa a ser la tienda con el espejo que ya tiene."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger("oficio_servidor")

ESPERA_SEG = 300
_desde: float | None = None


def _titular_vive() -> bool:
    from src.central_red_global.servidor.pareja.buscar import _guardada, elegir, puerto_abierto

    host = _guardada()
    if host and host.lower() not in ("localhost", "127.0.0.1") and puerto_abierto(host):
        return True
    return bool(elegir())


def vigilar() -> None:
    """La reserva cuenta el silencio. A los cinco minutos levanta la tienda."""
    global _desde
    try:
        from src.central_red_global.servidor.pareja.reserva import soy

        if not soy():
            _desde = None
            return
    except Exception:
        return
    try:
        if _titular_vive():
            _desde = None
            return
    except Exception as e:
        logger.warning("pareja  no se pudo mirar la titular: %s", e)
        return
    if _desde is None:
        _desde = time.time()
        logger.info("pareja  la titular no contesta, la reserva espera cinco minutos")
        return
    if time.time() - _desde < ESPERA_SEG:
        return
    try:
        if not _promover():
            _desde = time.time()
    except Exception as e:
        _desde = time.time()
        logger.warning("pareja  no se pudo promover la reserva: %s", e)


def _promover() -> bool:
    from src.jefe.nodo_portable.espejo.copia import existe, ruta

    if not existe():
        logger.warning("pareja  no hay espejo para promover")
        return False
    if _titular_vive():
        logger.info("pareja  la titular contesto, no me promuevo")
        return False
    logger.info("pareja  la titular murio, esta reserva pasa a ser la tienda")
    from src.services.mariadb_controller import mariadb_controller

    mariadb_controller.start_server()
    from src.central_red_global.servidor.pareja.buscar import puerto_abierto

    limite = time.time() + 40
    while time.time() < limite and not puerto_abierto("127.0.0.1"):
        time.sleep(1)
    if not puerto_abierto("127.0.0.1"):
        raise RuntimeError("MariaDB local no abrio")
    if _titular_vive():
        logger.info("pareja  la titular volvio mientras abria MariaDB, no me promuevo")
        try:
            mariadb_controller.stop_server()
        except Exception:
            pass
        return False

    from src.base_de_datos.database import db_manager

    db_manager.reconectar_mariadb("127.0.0.1")
    db_manager.is_master = True
    try:
        db_manager._create_tables()
        db_manager._migrate_db()
    except Exception as e:
        logger.warning("pareja  el esquema local quedo a medias: %s", e)
    motor = getattr(db_manager, "mariadb_engine", None)
    if motor is None:
        raise RuntimeError("no hay motor local")
    from src.base_de_datos.restaurar.aplicar.destino import Destino
    from src.base_de_datos.restaurar.aplicar.sumar import sumar

    destino = Destino("mariadb", host="127.0.0.1", conexion=motor._connect_kwargs())
    res = sumar(ruta(), destino)
    if "ventas" in (res.get("sin_lugar") or []):
        logger.warning("pareja  el espejo no entro en la tienda, sigo esclava")
        try:
            mariadb_controller.stop_server()
        except Exception:
            pass
        return False
    if _titular_vive():
        logger.info("pareja  la titular volvio mientras cargaba el espejo, no me promuevo")
        try:
            mariadb_controller.stop_server()
        except Exception:
            pass
        return False

    from src.config import config

    config.data["is_master"] = True
    config.data["db_engine"] = "mariadb"
    config.data["db_host"] = "127.0.0.1"
    config.data["carteleria_is_slave"] = False
    config.data["api_url"] = "http://127.0.0.1:8000"
    config.save()
    logger.info("pareja  espejo cargado, esta PC es la titular")
    from src.central_red_global.servidor.oficio.agente import retomar_oficio

    retomar_oficio()
    return True


def ceder_si_hay_otra() -> bool:
    """Si al prender ya hay una titular viva en la red, esta PC no abre una segunda tienda."""
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        if not es_pc_maestra_local():
            return False
    except Exception:
        return False
    from src.base_de_datos.autoblindaje.quien.maestra import Quien
    from src.central_red_global.servidor.pareja.buscar import oir_anuncios, puerto_abierto

    for aviso in oir_anuncios():
        if aviso.get("reserva"):
            continue
        if str(aviso.get("db_engine") or "").lower() not in ("", "mariadb"):
            continue
        ip = str(aviso.get("server_ip") or aviso.get("_desde") or "").strip()
        if not ip or Quien._es_esta_pc(ip):
            continue
        if not puerto_abierto(ip):
            continue
        from src.config import config

        config.data["is_master"] = False
        config.data["db_host"] = ip
        config.data["preferred_master_ip"] = ip
        config.data["carteleria_master_ip"] = ip
        config.data["carteleria_is_slave"] = True
        config.data["api_url"] = f"http://{ip}:8000"
        config.save()
        logger.info("pareja  ya hay titular en %s, esta PC queda esclava", ip)
        try:
            from src.services.mariadb_controller import mariadb_controller

            mariadb_controller.stop_server()
        except Exception as e:
            logger.warning("pareja  MariaDB local sigue prendida: %s", e)
        return True
    return False
