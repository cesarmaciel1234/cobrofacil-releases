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


def _store_id_guardado() -> str:
    try:
        from src.config import config

        return str(config.get("store_id", "") or "").strip()
    except Exception:
        return ""


def _guardar_identidad(store_id: str) -> bool:
    store_id = str(store_id or "").strip()
    if not store_id:
        return False
    actual = _store_id_guardado()
    if actual:
        return actual == store_id
    try:
        from src.config import config

        config.data["store_id"] = store_id
        config.save()
        return True
    except Exception as e:
        logger.warning("pareja  no se pudo guardar la identidad de tienda: %s", e)
        return False


def identidad_para_ip(ip: str, store_id: str = "") -> str:
    """Devuelve la identidad solo si el anuncio y la MariaDB confirman esa tienda."""
    ip = str(ip or "").strip()
    if not ip or ip.lower() in ("localhost", "127.0.0.1"):
        return ""
    anuncios = oir_anuncios()
    info = next(
        (
            aviso
            for aviso in anuncios
            if _ip_de(aviso) == ip
            and (not store_id or str(aviso.get("store_id") or "").strip() == store_id)
        ),
        {},
    )
    identidad = str(store_id or info.get("store_id") or "").strip()
    identidad_guardada = _store_id_guardado()
    guardada = _guardada()
    if not identidad or (identidad_guardada and identidad != identidad_guardada):
        return ""
    if (
        not identidad_guardada
        and guardada
        and guardada.lower() not in ("localhost", "127.0.0.1")
        and ip != guardada
    ):
        return ""
    if not info or not tiene_la_tienda(ip):
        return ""
    if not identidad_guardada and not _guardar_identidad(identidad):
        return ""
    return identidad


def _elegir_aviso(avisos: list[dict]) -> dict:
    """Solo acepta otra IP si su anuncio presenta la identidad ya enlazada."""
    guardada = _guardada()
    identidad = _store_id_guardado()
    candidatas = []
    for aviso in avisos:
        ip = _ip_de(aviso)
        store_id = str(aviso.get("store_id") or "").strip()
        if not ip or any(_ip_de(candidata) == ip for candidata in candidatas):
            continue
        if (
            not identidad
            and guardada
            and guardada.lower() not in ("localhost", "127.0.0.1")
            and ip != guardada
        ):
            continue
        if identidad and store_id != identidad:
            continue
        if not store_id:
            continue
        if tiene_la_tienda(ip):
            candidatas.append(aviso)
    if guardada:
        preferida = next(
            (aviso for aviso in candidatas if _ip_de(aviso) == guardada),
            None,
        )
        if preferida:
            return preferida
    return candidatas[0] if candidatas else {}


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
    info = _elegir_aviso(avisos if avisos is not None else oir_anuncios())
    return _ip_de(info) if info else ""


def adoptar(ip: str, store_id: str = "") -> bool:
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
    identidad = identidad_para_ip(ip, store_id)
    identidad_guardada = _store_id_guardado()
    if not identidad or (identidad_guardada and identidad != identidad_guardada):
        logger.warning("pareja  no se enlaza %s: identidad de tienda ausente o distinta", ip)
        return False
    guardada = _guardada()
    if (
        not identidad_guardada
        and guardada
        and guardada.lower() not in ("localhost", "127.0.0.1")
        and ip != guardada
    ):
        logger.warning(
            "pareja  no se enlaza %s: falta confirmar la identidad de la tienda anterior",
            ip,
        )
        return False
    return _guardar_adopcion(ip, identidad)


def _guardar_adopcion(ip: str, identidad: str) -> bool:
    """Persiste una IP ya verificada por identidad y MariaDB."""
    identidad = str(identidad or "").strip()
    identidad_guardada = _store_id_guardado()
    if not identidad or (identidad_guardada and identidad != identidad_guardada):
        return False
    try:
        from src.config import config

        config.data["db_host"] = ip
        config.data["preferred_master_ip"] = ip
        config.data["carteleria_master_ip"] = ip
        config.data["api_url"] = f"http://{ip}:8000"
        config.data["store_id"] = identidad
        config.data["is_master"] = False
        config.save()
    except Exception as e:
        logger.warning("pareja  no se pudo guardar la maestra %s: %s", ip, e)
        return False
    logger.info("pareja  la maestra ahora es %s", ip)
    return True


def buscar() -> str:
    """Devuelve solo una IP anunciada y verificada para la identidad enlazada."""
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        if es_pc_maestra_local():
            return "127.0.0.1" if puerto_abierto("127.0.0.1") else ""
    except Exception:
        pass
    avisos = oir_anuncios()
    info = _elegir_aviso(avisos)
    ip = _ip_de(info) if info else ""
    if ip:
        identidad = str(info.get("store_id") or "").strip()
        guardada = _guardada()
        if ip == guardada:
            if not _guardar_identidad(identidad):
                return ""
        elif not _guardar_adopcion(ip, identidad):
            return ""
    return ip
