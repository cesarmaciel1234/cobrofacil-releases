import glob
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta

from src.logger import logger
from src.utils.paths import get_base_path


class Quien:
    _host_cache: tuple[str, float] = ("", 0.0)

    @classmethod
    def host_vivo(cls, pedido: str = "") -> str:
        """Quién tiene MariaDB ahora. Esta PC si es maestra; si no, la que se anuncia en la red."""
        ahora = time.time()
        guardado, cuando = cls._host_cache
        if cuando and (ahora - cuando) < 20:
            return guardado

        from src.base_de_datos.core.mariadb_probe import puerto_mariadb_abierto

        elegido = ""
        if cls._soy_maestra() and puerto_mariadb_abierto("127.0.0.1", timeout=0.8):
            elegido = "127.0.0.1"
        else:
            anunciada = cls._maestra_anunciada()
            if anunciada and cls._es_esta_pc(anunciada):
                if puerto_mariadb_abierto("127.0.0.1", timeout=0.8):
                    elegido = "127.0.0.1"
            elif anunciada and puerto_mariadb_abierto(anunciada, timeout=3.0):
                elegido = anunciada
            elif not anunciada:
                pedido_n = str(pedido or "").strip()
                if pedido_n.lower() == "localhost":
                    pedido_n = "127.0.0.1"
                if pedido_n and puerto_mariadb_abierto(
                    "127.0.0.1" if cls._host_local(pedido_n) else pedido_n,
                    timeout=0.8 if cls._host_local(pedido_n) else 3.0,
                ):
                    elegido = "127.0.0.1" if cls._es_esta_pc(pedido_n) else pedido_n
        cls._host_cache = (elegido, time.time())
        return elegido

    @classmethod
    def _soy_maestra(cls) -> bool:
        try:
            from src.config import config

            if config.get("carteleria_is_slave") or config.get("is_master") is False:
                return False
            return config.get("is_master") is True
        except Exception:
            return False

    @classmethod
    def _maestra_anunciada(cls) -> str:
        """La que contesta en la red, con la IP que tiene ahora. La reserva indica a la titular."""
        try:
            from src.central_red_global.servidor.pareja.buscar import elegir

            return elegir()
        except Exception as e:
            logger.info(f"Respaldo: no se anunció maestra ({e})")
            return ""

    @staticmethod
    def _host_local(host: str) -> bool:
        nombre = (socket.gethostname() or "").lower()
        return str(host or "").strip().lower() in ("127.0.0.1", "localhost", nombre, "")

    @classmethod
    def _es_esta_pc(cls, host: str) -> bool:
        if cls._host_local(host):
            return True
        propias: set[str] = set()
        try:
            propias.add(socket.gethostbyname(socket.gethostname()))
        except Exception:
            pass
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                if info and info[4]:
                    propias.add(str(info[4][0]))
        except Exception:
            pass
        return str(host or "").strip() in propias

    @staticmethod
    def _host_es_esta_pc(host: str | None) -> bool:
        h = str(host or "").strip().lower()
        if h in ("", "localhost", "127.0.0.1", "::1"):
            return True
        try:
            import socket

            nombre = socket.gethostname()
            return h in {nombre.lower(), *socket.gethostbyname_ex(nombre)[2]}
        except Exception:
            return False

