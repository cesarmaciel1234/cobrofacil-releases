"""Si la maestra cambia de IP, las esclavas buscan otra que se anuncie."""

from __future__ import annotations

import json
import logging
import socket
import time

logger = logging.getLogger("oficio_servidor")

PUERTO = 37020
_ESPERA = 1.6


def puerto_abierto(host: str, timeout: float = 0.6) -> bool:
    if not host:
        return False
    sonda = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sonda.settimeout(timeout)
    try:
        return sonda.connect_ex((host, 3306)) == 0
    except Exception:
        return False
    finally:
        sonda.close()


def oir_anuncios() -> list[dict]:
    """Todas las respuestas a PUNPRO_DISCOVER. La titular y la reserva pueden contestar las dos."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    avisos: list[dict] = []
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.4)
        sock.sendto(b"PUNPRO_DISCOVER", ("255.255.255.255", PUERTO))
        fin = time.time() + _ESPERA
        while time.time() < fin:
            sock.settimeout(max(0.2, fin - time.time()))
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                break
            try:
                info = json.loads(data.decode("utf-8", errors="ignore"))
            except Exception:
                continue
            if not isinstance(info, dict):
                continue
            if str(info.get("mode") or "").upper() != "MAESTRA":
                continue
            info["_desde"] = addr[0] if addr else ""
            avisos.append(info)
    except Exception as e:
        logger.info("pareja  nadie se anuncio: %s", e)
    finally:
        try:
            sock.close()
        except Exception:
            pass
    return avisos


def _ip_de(aviso: dict) -> str:
    if aviso.get("reserva"):
        return str(aviso.get("titular_ip") or "").strip()
    return str(aviso.get("server_ip") or aviso.get("_desde") or "").strip()


def tiene_la_tienda(host: str) -> bool:
    """El puerto 3306 no alcanza. Otra PC puede abrir MariaDB sin la tabla productos."""
    if not puerto_abierto(host, timeout=1.2):
        return False
    try:
        from src.db_engines.mariadb_engine import MariaDBEngine

        motor = MariaDBEngine(host=host)
        conn = motor.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM productos LIMIT 1")
            cur.fetchone()
            return True
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception as e:
        logger.info("pareja  %s no tiene la tienda: %s", host, e)
        return False


def _guardada() -> str:
    try:
        from src.config import config

        return str(config.get("db_host", "") or "").strip()
    except Exception:
        return ""


def elegir(avisos: list[dict] | None = None) -> str:
    """La MariaDB que contesta. Si la IP guardada sigue viva, esa. Si no, la que se anunció."""
    vivas: list[str] = []
    for aviso in avisos if avisos is not None else oir_anuncios():
        ip = _ip_de(aviso)
        if not ip or ip in vivas:
            continue
        if tiene_la_tienda(ip):
            vivas.append(ip)
    if not vivas:
        return ""
    guardada = _guardada()
    if guardada in vivas:
        return guardada
    return vivas[0]


def adoptar(ip: str) -> bool:
    """La esclava deja la IP vieja y sigue a la maestra que contestó. No se vuelve titular."""
    ip = str(ip or "").strip()
    if not ip or ip.lower() in ("localhost", "127.0.0.1"):
        return False
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        if es_pc_maestra_local():
            return False
    except Exception:
        return False
    if ip == _guardada():
        return False
    if not tiene_la_tienda(ip):
        return False
    try:
        from src.config import config

        config.data["db_host"] = ip
        config.data["preferred_master_ip"] = ip
        config.data["carteleria_master_ip"] = ip
        config.data["api_url"] = f"http://{ip}:8000"
        config.data["is_master"] = False
        config.save()
    except Exception as e:
        logger.warning("pareja  no se pudo guardar la maestra %s: %s", ip, e)
        return False
    logger.info("pareja  la maestra ahora es %s", ip)
    return True


def buscar() -> str:
    """IP de la tienda. Si la guardada no contesta, la que se anuncie en la red."""
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        if es_pc_maestra_local():
            return "127.0.0.1" if puerto_abierto("127.0.0.1") else ""
    except Exception:
        pass
    guardada = _guardada()
    if guardada and guardada.lower() not in ("localhost", "127.0.0.1") and tiene_la_tienda(guardada):
        return guardada
    ip = elegir()
    if ip:
        adoptar(ip)
    return ip
