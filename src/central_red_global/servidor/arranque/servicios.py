"""Capa baja: MariaDB + LAN + presencia (sin UI)."""

from __future__ import annotations

from src.logger import logger


def encender_servicios_tienda(*, arrancar_mysqld: bool = False) -> None:
    if arrancar_mysqld:
        try:
            from src.services.mariadb_controller import mariadb_controller

            mariadb_controller.start_server()
        except Exception as e:
            logger.warning(f"MariaDB: {e}")
    else:
        try:
            from src.services.mariadb_controller import mariadb_controller

            mariadb_controller._ensure_firewall()
        except Exception as e:
            logger.warning(f"Firewall servidor: {e}")
    try:
        from src.base_de_datos.database import db_manager

        db_manager._init_db()
    except Exception as e:
        logger.error(f"Init DB servidor: {e}")
    try:
        from src.central_red_global.lan_server import init_lan_server

        init_lan_server()
    except Exception as e:
        logger.warning(f"LAN server: {e}")
    try:
        from src.carteleria.creador_png.servidor import asegurar_servidor

        asegurar_servidor()
    except Exception as e:
        logger.warning(f"Creador PNG en servidor: {e}")
    try:
        from src.central_red_global.master_presence import ensure_master_lan_presence

        ensure_master_lan_presence()
    except Exception as e:
        logger.warning(f"Presencia maestra: {e}")
