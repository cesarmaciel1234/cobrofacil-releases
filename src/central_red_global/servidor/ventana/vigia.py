"""Lee la cola y los cambios. No los envía: solo los cuenta para la ventana."""

from __future__ import annotations

import json
import os
from datetime import datetime

from src.utils.paths import get_base_path


def canal(mensaje: str) -> str:
    """A qué panel va una línea del log."""
    m = (mensaje or "").lower()
    if m.startswith("reparto"):
        return "reparto"
    if "espejo" in m or m.startswith("nodo:"):
        return "espejo"
    if any(x in m for x in ("venta", "ticket", "buffer offline", "sincroniz")):
        return "tickets"
    if any(x in m for x in ("producto", "cliente", "recepcion", "recepción", "nutric")):
        return "cambios"
    return "red"


def acortar(mensaje: str) -> str:
    """Junta los avisos repetidos de red. Una traza no entra a la consola."""
    m = (mensaje or "").lower()
    if "traceback" in m or m.startswith("file ") or "sqlite3.row" in m:
        return ""
    if (
        "can't connect" in m
        or "no disponible" in m
        or "no responde" in m
        or "reconectar_mariadb" in m
    ):
        return "maestra sin respuesta"
    if "timed out" in m and "png" in m:
        return "carteleria  png sin respuesta"
    return " ".join((mensaje or "").split())


def _hora(valor) -> str:
    """Día y hora. Sin el día, un ticket del 13 y otro del 24 parecen la misma jornada."""
    if isinstance(valor, str) and len(valor) >= 16 and valor[4] == "-":
        return f"{valor[8:10]}/{valor[5:7]} {valor[11:16]}"
    try:
        return datetime.fromtimestamp(float(valor)).strftime("%d/%m %H:%M")
    except Exception:
        return "--:--"


def _plata(valor) -> str:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return ""
    if abs(numero - round(numero)) < 0.001:
        return f"${int(round(numero))}"
    return f"${numero:.2f}"


def _leer_json(nombre: str, vacio):
    ruta = os.path.join(get_base_path(), nombre)
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return vacio


def filas_tickets(tope: int = 40) -> tuple[int, list[tuple[str, str, str, str, str]]]:
    """Filas de la cola. No las envía. Lo más nuevo, primero."""
    cola = _leer_json("offline_queue.json", [])
    if not isinstance(cola, list):
        return 0, []
    filas = []
    for registro in reversed(cola[:]):
        if not isinstance(registro, dict):
            continue
        venta = registro.get("venta_data") or {}
        items = registro.get("items") or []
        nombre = ""
        cant = ""
        if items and isinstance(items[0], dict):
            nombre = str(items[0].get("nombre") or "").strip()
            cruda = items[0].get("cant")
            if isinstance(cruda, (int, float)):
                cant = f" x{cruda:g}"
        extra = f" +{len(items) - 1}" if len(items) > 1 else ""
        filas.append(
            (
                _hora(registro.get("timestamp")),
                _plata(venta.get("total")),
                str(venta.get("metodo_pago") or "—"),
                f"{nombre}{cant}{extra}".strip() or "—",
                "EN COLA",
            )
        )
        if len(filas) >= tope:
            break
    return len(cola), filas


def _cant(valor) -> str:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "—"
    if abs(numero - round(numero)) < 0.001:
        return str(int(round(numero)))
    return f"{numero:.3f}".rstrip("0").rstrip(".")


def _leer_auditoria(ruta: str, origen: str, tope: int) -> list[tuple]:
    """Conteos ya guardados. No escribe y no crea la tabla."""
    import sqlite3

    if not ruta or not os.path.isfile(ruta) or os.path.getsize(ruta) <= 0:
        return []
    try:
        from pathlib import Path

        conn = sqlite3.connect(Path(ruta).as_uri() + "?mode=ro", uri=True, timeout=0.4)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=400")
    except Exception:
        return []
    try:
        existe = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='auditorias_inventario'"
        ).fetchone()
        if not existe:
            return []
        crudas = conn.execute(
            "SELECT fecha, nombre_producto, stock_sistema, stock_fisico, diferencia, responsable "
            "FROM auditorias_inventario ORDER BY fecha DESC, id DESC LIMIT ?",
            (tope,),
        ).fetchall()
    except Exception:
        return []
    finally:
        conn.close()
    salida = []
    for fila in crudas:
        antes = _cant(fila["stock_sistema"])
        despues = _cant(fila["stock_fisico"])
        try:
            diferencia = float(fila["diferencia"] or 0)
        except (TypeError, ValueError):
            diferencia = 0.0
        signo = _cant(diferencia)
        if diferencia > 0:
            signo = f"+{signo}"
        fecha = str(fila["fecha"] or "")
        salida.append(
            (
                (fecha, str(fila["nombre_producto"] or ""), despues),
                fecha,
                (
                    _hora(fecha),
                    str(fila["nombre_producto"] or "—"),
                    f"{antes} → {despues}  ({signo})",
                    str(fila["responsable"] or "—"),
                    origen,
                ),
            )
        )
    return salida


def filas_auditoria(tope: int = 40) -> tuple[int, list[tuple[str, str, str, str, str]]]:
    """El conteo físico, leído de la tabla de auditoría. No sale de la cola de cambios."""
    juntas = _leer_auditoria(os.path.join(get_base_path(), "punpro.db"), "local", tope)
    try:
        from src.jefe.nodo_portable.espejo.copia import ruta

        juntas.extend(_leer_auditoria(ruta(), "réplica", tope))
    except Exception:
        pass
    elegidas: dict[tuple, tuple] = {}
    for clave, orden, fila in juntas:
        previa = elegidas.get(clave)
        if previa is None or fila[4] == "réplica":
            elegidas[clave] = (orden, fila)
    ordenadas = sorted(elegidas.values(), key=lambda par: par[0] or "", reverse=True)
    filas = [fila for _, fila in ordenadas[:tope]]
    return len(filas), filas


def filas_cambios(tope: int = 40) -> tuple[int, list[tuple[str, str, str, str, str]]]:
    """Precios, remitos y clientes que esperan. No los envía. No mezcla la auditoría."""
    cola = _leer_json("offline_cambios.json", {})
    if not isinstance(cola, dict):
        cola = {}
    ordenados = []
    for registro in cola.get("productos") or []:
        if not isinstance(registro, dict):
            continue
        datos = registro.get("datos") or {}
        ordenados.append(
            (
                registro.get("timestamp") or 0,
                (
                    _hora(registro.get("fecha") or registro.get("timestamp")),
                    "precio",
                    str(registro.get("nombre") or datos.get("nombre") or "—"),
                    f"{_plata(datos.get('precio'))}  stock {datos.get('stock', '—')}".strip(),
                    "EN COLA",
                ),
            )
        )
    for registro in cola.get("recepciones") or []:
        if not isinstance(registro, dict):
            continue
        ordenados.append(
            (
                registro.get("timestamp") or 0,
                (
                    _hora(registro.get("fecha") or registro.get("timestamp")),
                    "remito",
                    str(registro.get("proveedor") or "—"),
                    _plata(registro.get("total_monto")),
                    "EN COLA",
                ),
            )
        )
    for registro in cola.get("clientes") or []:
        if not isinstance(registro, dict):
            continue
        datos = registro.get("datos") or {}
        ordenados.append(
            (
                registro.get("timestamp") or 0,
                (
                    _hora(registro.get("fecha") or registro.get("timestamp")),
                    "cliente",
                    str(datos.get("nombre") or datos.get("razon_social") or "—"),
                    str(registro.get("accion") or ""),
                    "EN COLA",
                ),
            )
        )
    ordenados.sort(key=lambda par: par[0] or 0, reverse=True)
    return len(ordenados), [fila for _, fila in ordenados[:tope]]


def _leer_base(ruta: str, tope: int = 12) -> tuple[list[tuple[str, str]], int]:
    """Las tablas más grandes y cuántas hay. Solo lectura. Una sola apertura."""
    import sqlite3

    if not ruta or not os.path.isfile(ruta) or os.path.getsize(ruta) <= 0:
        return [], 0
    try:
        from pathlib import Path

        conn = sqlite3.connect(Path(ruta).as_uri() + "?mode=ro", uri=True, timeout=0.4)
        conn.execute("PRAGMA busy_timeout=400")
    except Exception:
        return [], 0
    try:
        nombres = [
            fila[0]
            for fila in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            if fila and str(fila[0]).replace("_", "").isalnum()
        ]
        contadas = []
        for nombre in nombres:
            try:
                cantidad = conn.execute(f'SELECT COUNT(*) FROM "{nombre}"').fetchone()[0]
            except Exception:
                cantidad = "—"
            contadas.append((nombre, cantidad))
        contadas.sort(key=lambda par: par[1] if isinstance(par[1], int) else -1, reverse=True)
        filas = [(nombre, str(cantidad)) for nombre, cantidad in contadas[:tope]]
        return filas, len(nombres)
    except Exception:
        return [], 0
    finally:
        conn.close()


_cache_catalogo = {"t": 0.0, "local": [], "replica": [], "n_local": 0, "n_replica": 0}


def _conservar(nuevo, n_nuevo, previo, n_previo, ruta: str):
    """Si la base está ocupada, se queda el último conteo. No se borra la grilla."""
    if nuevo or not previo or not ruta or not os.path.isfile(ruta):
        return nuevo, n_nuevo
    return previo, n_previo


def catalogo() -> tuple[list[tuple[str, str]], int, list[tuple[str, str]], int]:
    """Las 12 tablas más grandes y el total real. No abre MariaDB. Recuenta cada 15 s."""
    import time

    ahora = time.time()
    if _cache_catalogo["t"] and ahora - _cache_catalogo["t"] < 15:
        return (
            _cache_catalogo["local"],
            _cache_catalogo["n_local"],
            _cache_catalogo["replica"],
            _cache_catalogo["n_replica"],
        )
    ruta_local = os.path.join(get_base_path(), "punpro.db")
    local, n_local = _leer_base(ruta_local)
    local, n_local = _conservar(
        local, n_local, _cache_catalogo["local"], _cache_catalogo["n_local"], ruta_local
    )
    replica: list[tuple[str, str]] = []
    n_replica = 0
    ruta_replica = ""
    try:
        from src.jefe.nodo_portable.espejo.copia import ruta

        ruta_replica = ruta()
        replica, n_replica = _leer_base(ruta_replica)
    except Exception:
        replica = []
        n_replica = 0
    replica, n_replica = _conservar(
        replica, n_replica, _cache_catalogo["replica"], _cache_catalogo["n_replica"], ruta_replica
    )
    _cache_catalogo["t"] = ahora
    _cache_catalogo["local"] = local
    _cache_catalogo["replica"] = replica
    _cache_catalogo["n_local"] = n_local
    _cache_catalogo["n_replica"] = n_replica
    return local, n_local, replica, n_replica


def foto_tickets(tope: int = 8) -> tuple[int, list[str]]:
    """Tickets que todavía no subieron. Lo más nuevo, primero."""
    cola = _leer_json("offline_queue.json", [])
    if not isinstance(cola, list):
        return 0, ["sin tickets en espera"]
    lineas = []
    for registro in reversed(cola[-tope:]):
        if not isinstance(registro, dict):
            continue
        venta = registro.get("venta_data") or {}
        items = registro.get("items") or []
        nombre = ""
        if items and isinstance(items[0], dict):
            nombre = str(items[0].get("nombre") or "").strip()
        cant = ""
        if items and isinstance(items[0], dict):
            cant = items[0].get("cant") or ""
            cant = f" x{cant:g}" if isinstance(cant, (int, float)) else ""
        extra = f"  +{len(items) - 1}" if len(items) > 1 else ""
        lineas.append(
            f"{_hora(registro.get('timestamp'))}  {_plata(venta.get('total')):>8}  "
            f"{venta.get('metodo_pago') or '—':<10}  {nombre}{cant}{extra}".rstrip()
        )
    if len(cola) > tope:
        lineas.append(f"… y {len(cola) - tope} más en espera")
    return len(cola), lineas or ["sin tickets en espera"]


def foto_cambios(tope: int = 8) -> tuple[int, list[str]]:
    """Precios, stock, recepciones y clientes que esperan a la maestra."""
    cola = _leer_json("offline_cambios.json", {})
    if not isinstance(cola, dict):
        cola = {}
    filas = []
    for registro in cola.get("productos") or []:
        if not isinstance(registro, dict):
            continue
        datos = registro.get("datos") or {}
        filas.append(
            (
                registro.get("timestamp") or 0,
                f"{_hora(registro.get('fecha') or registro.get('timestamp'))}  "
                f"precio   {registro.get('nombre') or datos.get('nombre') or '—'}  "
                f"{_plata(datos.get('precio'))}  stock {datos.get('stock', '—')}",
            )
        )
    for registro in cola.get("recepciones") or []:
        if not isinstance(registro, dict):
            continue
        filas.append(
            (
                registro.get("timestamp") or 0,
                f"{_hora(registro.get('fecha') or registro.get('timestamp'))}  "
                f"remito   {registro.get('proveedor') or '—'}  "
                f"{_plata(registro.get('total_monto'))}",
            )
        )
    for registro in cola.get("clientes") or []:
        if not isinstance(registro, dict):
            continue
        datos = registro.get("datos") or {}
        filas.append(
            (
                registro.get("timestamp") or 0,
                f"{_hora(registro.get('fecha') or registro.get('timestamp'))}  "
                f"cliente  {registro.get('accion') or ''}  "
                f"{datos.get('nombre') or datos.get('razon_social') or '—'}",
            )
        )
    filas.sort(key=lambda par: par[0] or 0, reverse=True)
    lineas = [texto for _, texto in filas[:tope]]
    if len(filas) > tope:
        lineas.append(f"… y {len(filas) - tope} cambios más")
    return len(filas), lineas or ["sin cambios en espera"]
