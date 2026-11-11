"""Única fuente de verdad para parámetros compartidos de la tienda (Maestra -> Esclavas)."""

from __future__ import annotations

import json
import math
import socket
import threading
import time

from src.logger import logger

CLAVES_CREDITO = (
    "fiado_mantenimiento_pct",
    "fiado_apalancamiento_pct",
    "fiado_plazo_dias",
)
CLAVES_NEGOCIO = (
    "business_name",
    "address",
    "phone",
    "business_cuit",
    "footer_message",
    "mensaje_zocalo",
)
CLAVES_MP = (
    "mp_access_token",
    "mp_user_id",
    "mp_device_id",
    "mp_qr_pos_external_id",
)
CLAVES_TIENDA = CLAVES_CREDITO + CLAVES_NEGOCIO + CLAVES_MP

_CLAVE_DB_ESTADO = "tienda_config_maestra"
_CLAVE_DB_VERSION = "tienda_config_version"
_LOCK = threading.RLock()


def _clamp_pct(valor, default: float) -> float:
    try:
        pct = float(valor)
    except (TypeError, ValueError):
        pct = float(default)
    if not math.isfinite(pct):
        pct = float(default)
    return round(max(0.0, min(50.0, pct)), 2)


def _clamp_plazo(valor, default: int = 30) -> int:
    try:
        dias = int(float(valor))
    except (TypeError, ValueError):
        dias = int(default)
    return max(1, min(3650, dias))


def sanitizar_cambios(cambios: dict) -> dict:
    """Filtra y normaliza solo las claves globales permitidas de tienda."""
    if not isinstance(cambios, dict):
        return {}
    salida: dict = {}
    for clave, valor in cambios.items():
        if clave not in CLAVES_TIENDA or valor is None:
            continue
        if clave in ("fiado_mantenimiento_pct", "fiado_apalancamiento_pct"):
            default = 3.0 if clave == "fiado_mantenimiento_pct" else 5.0
            salida[clave] = _clamp_pct(valor, default)
        elif clave == "fiado_plazo_dias":
            salida[clave] = _clamp_plazo(valor, 30)
        else:
            salida[clave] = str(valor).strip()
    return salida


def _extraer_snapshot_config() -> dict:
    from src.config import config

    config.reload()
    valores: dict = {}
    for clave in CLAVES_TIENDA:
        val = config.get(clave)
        if val is not None:
            valores[clave] = val
    return sanitizar_cambios(valores)


def _aplicar_snapshot_local(estado: dict) -> None:
    """Pisa en config.json local únicamente las claves globales oficiales + versión."""
    from src.config import config

    if not isinstance(estado, dict):
        return
    valores = sanitizar_cambios(estado.get("values") or {})
    try:
        version = max(0, int(estado.get("version") or 0))
    except (TypeError, ValueError):
        version = 0

    with _LOCK:
        config.reload()
        cambio = False
        for clave, valor in valores.items():
            if config.data.get(clave) != valor:
                config.data[clave] = valor
                cambio = True
        if version and int(config.data.get(_CLAVE_DB_VERSION) or 0) != version:
            config.data[_CLAVE_DB_VERSION] = version
            cambio = True
        if cambio:
            config.save()


def leer_version_local() -> int:
    try:
        from src.config import config

        config.reload()
        return max(0, int(config.get(_CLAVE_DB_VERSION, 0) or 0))
    except Exception:
        return 0


def _leer_de_mariadb() -> dict | None:
    try:
        from src.base_de_datos.database import db_manager

        filas = db_manager.execute_query(
            "SELECT valor FROM configuracion WHERE clave = ? LIMIT 1",
            (_CLAVE_DB_ESTADO,),
        )
        if not filas:
            return None
        fila = filas[0]
        raw = fila["valor"] if isinstance(fila, dict) or hasattr(fila, "keys") else fila[0]
        if not raw:
            return None
        data = json.loads(str(raw))
        if not isinstance(data, dict):
            return None
        return {
            "version": max(0, int(data.get("version") or 0)),
            "updated_at": float(data.get("updated_at") or 0.0),
            "updated_by": str(data.get("updated_by") or ""),
            "values": sanitizar_cambios(data.get("values") or {}),
        }
    except Exception:
        return None


def _persistir_en_mariadb(estado: dict) -> bool:
    try:
        from src.base_de_datos.database import db_manager

        payload = json.dumps(estado, ensure_ascii=False)
        ok = db_manager.execute_non_query(
            "REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
            (_CLAVE_DB_ESTADO, payload),
        )
        db_manager.execute_non_query(
            "REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
            (_CLAVE_DB_VERSION, str(int(estado.get("version") or 0))),
        )
        valores = estado.get("values") or {}
        for clave in CLAVES_MP:
            if clave in valores:
                db_manager.execute_non_query(
                    "REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
                    (clave, str(valores.get(clave) or "")),
                )
        return bool(ok)
    except Exception:
        return False


def leer_estado_maestra() -> dict:
    """Devuelve el estado oficial vigente en la PC Maestra."""
    with _LOCK:
        local_vals = _extraer_snapshot_config()
        local_ver = leer_version_local()
        remoto = _leer_de_mariadb()

        if remoto and remoto.get("values"):
            r_ver = int(remoto.get("version") or 0)
            if r_ver > local_ver:
                merged = {**local_vals, **remoto["values"]}
                estado = {
                    "version": r_ver,
                    "updated_at": float(remoto.get("updated_at") or time.time()),
                    "updated_by": str(remoto.get("updated_by") or ""),
                    "values": sanitizar_cambios(merged),
                }
                _aplicar_snapshot_local(estado)
                return estado
            if local_ver > r_ver:
                estado = {
                    "version": local_ver,
                    "updated_at": time.time(),
                    "updated_by": socket.gethostname(),
                    "values": local_vals,
                }
                _persistir_en_mariadb(estado)
                return estado
            merged = {**local_vals, **remoto["values"]}
            return {
                "version": max(1, r_ver, local_ver),
                "updated_at": float(remoto.get("updated_at") or time.time()),
                "updated_by": str(remoto.get("updated_by") or ""),
                "values": sanitizar_cambios(merged),
            }

        version = max(1, local_ver)
        estado = {
            "version": version,
            "updated_at": time.time(),
            "updated_by": socket.gethostname(),
            "values": local_vals,
        }
        _aplicar_snapshot_local(estado)
        _persistir_en_mariadb(estado)
        return estado


def _notificar_cambio_a_esclavas(version: int) -> None:
    """Avisa por UDP y refresca sello para que todas las esclavas bajen la versión oficial."""
    try:
        from src.central_red_global.sync_tienda.aviso_tv.avisar import repartir_desde_maestra

        repartir_desde_maestra()
    except Exception:
        pass
    try:
        from src.central_red_global.network_engine import get_network_engine, init_network_engine

        eng = get_network_engine() or init_network_engine("maestra")
        if eng is not None:
            eng.broadcast("CONFIG_TIENDA", {"version": int(version)})
    except Exception as exc:
        logger.debug("Aviso UDP CONFIG_TIENDA: %s", exc)


def _es_rol_maestra_real() -> bool:
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        return bool(es_pc_maestra_local())
    except Exception:
        from src.central_red_global.sync_tienda.rol import es_esclava

        return not es_esclava()


def aplicar_en_maestra(cambios: dict, origen: str = "") -> tuple[bool, dict, str]:
    """
    Aplica cambios oficiales en la PC Maestra, sube la versión, persiste en DB + config.json
    y notifica a todas las esclavas (la maestra es dueña única de la verdad).
    """
    if not _es_rol_maestra_real():
        return False, {}, "Solo la PC Maestra puede aceptar cambios globales de tienda."

    limpios = sanitizar_cambios(cambios)
    if not limpios:
        return False, {}, "No se enviaron parámetros globales válidos."

    with _LOCK:
        actual = leer_estado_maestra()
        nueva_version = max(1, int(actual.get("version") or 0) + 1)
        nuevos_valores = sanitizar_cambios({**(actual.get("values") or {}), **limpios})
        estado = {
            "version": nueva_version,
            "updated_at": time.time(),
            "updated_by": str(origen or socket.gethostname()).strip(),
            "values": nuevos_valores,
        }
        _aplicar_snapshot_local(estado)
        _persistir_en_mariadb(estado)

    _notificar_cambio_a_esclavas(nueva_version)
    logger.info(
        "Config Tienda v%s aceptada por Maestra (origen=%s, claves=%s)",
        nueva_version,
        estado["updated_by"],
        list(limpios.keys()),
    )
    return True, estado, ""


def _host_maestra_activo() -> str:
    from src.central_red_global.sync_tienda.rol import es_esta_pc, host_maestra

    host = host_maestra()
    if host and not es_esta_pc(host):
        return host
    try:
        from src.central_red_global.network_engine import get_network_engine

        eng = get_network_engine()
        if eng is not None:
            descubierto = eng.discover_master(timeout=2.0)
            if isinstance(descubierto, dict) and descubierto.get("ip"):
                ip = str(descubierto["ip"]).strip()
                if ip and not es_esta_pc(ip):
                    return ip
    except Exception:
        pass
    return host


def guardar_y_sincronizar(cambios: dict) -> tuple[bool, str]:
    """
    Punto único para guardar configuración compartida desde cualquier caja:
    - Maestra: valida, versiona y propaga a todas las esclavas.
    - Esclava: envía a la Maestra; solo si la Maestra acepta, actualiza su propio config.json
      con el snapshot oficial devuelto por la Maestra.
    """
    limpios = sanitizar_cambios(cambios)
    if not limpios:
        return False, "No hay cambios válidos para guardar."

    if _es_rol_maestra_real():
        ok, _estado, err = aplicar_en_maestra(limpios, origen=socket.gethostname())
        return ok, err

    from src.central_red_global.sync_tienda.rol import es_esta_pc, pedir_a_maestra, url_maestra

    host = _host_maestra_activo()
    if not host or es_esta_pc(host):
        return (
            False,
            "No se detectó la PC Maestra en la red. "
            "Para evitar diferencias entre cajas, estos ajustes solo se guardan estando en línea con la Maestra.",
        )

    payload = json.dumps(
        {"cambios": limpios, "origen": socket.gethostname()},
        ensure_ascii=False,
    ).encode("utf-8")
    try:
        with pedir_a_maestra(
            url_maestra("/api/tienda/config", host),
            data=payload,
            method="POST",
            extra={"Content-Type": "application/json"},
            timeout=6,
        ) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw or "{}")
        if not isinstance(data, dict) or not data.get("ok"):
            return False, str(data.get("error") or "La PC Maestra rechazó el cambio.")
        _aplicar_snapshot_local(data)
        return True, ""
    except Exception as exc:
        logger.warning("No se pudo enviar config global a la Maestra (%s): %s", host, exc)
        return (
            False,
            "No se pudo conectar con la PC Maestra para guardar los parámetros globales de la tienda.",
        )


def sincronizar_desde_maestra(forzar: bool = False) -> bool:
    """
    Esclava: consulta a la Maestra GET /api/tienda/config y pisa su config.json local
    si la versión oficial cambió (o si forzar=True).
    """
    if _es_rol_maestra_real():
        return False

    from src.central_red_global.sync_tienda.rol import es_esta_pc, pedir_a_maestra, url_maestra

    host = _host_maestra_activo()
    if not host or es_esta_pc(host):
        return False

    try:
        with pedir_a_maestra(
            url_maestra("/api/tienda/config", host),
            method="GET",
            timeout=2.5,
        ) as resp:
            raw = resp.read().decode("utf-8")
        remoto = json.loads(raw or "{}")
        if not isinstance(remoto, dict) or not remoto.get("ok"):
            return False
        remoto_ver = max(0, int(remoto.get("version") or 0))
        local_ver = leer_version_local()
        local_vals = _extraer_snapshot_config()
        remoto_vals = sanitizar_cambios(remoto.get("values") or {})
        difiere = any(local_vals.get(k) != v for k, v in remoto_vals.items())
        if forzar or remoto_ver != local_ver or difiere:
            _aplicar_snapshot_local(remoto)
            logger.info(
                "Esclava: configuración sincronizada desde Maestra (v%s -> v%s)",
                local_ver,
                remoto_ver,
            )
            return True
        return False
    except Exception as exc:
        logger.debug("Sync config_tienda desde Maestra (%s): %s", host, exc)
        return False
