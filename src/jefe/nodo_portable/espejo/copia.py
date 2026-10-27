"""Copia de la tienda en esta PC. Se refresca sola mientras hay maestra; el pendrive copia este archivo."""

from __future__ import annotations

import datetime as _dt
import decimal
import os
import socket
import sqlite3
import sys
import threading
import time

from src.logger import logger

ARCHIVO = "espejo_tienda.db"
DIAS_VIVOS = 3
# MariaDB: tabla dañada / no existe en el motor / fallo de lectura del motor
CODIGOS_ROTA = (1877, 1932, 1030, 145, 126, 1034)
_lock = threading.Lock()
_hilo: threading.Thread | None = None
_estado = {"cuando": "", "resultado": "", "detalle": ""}
_salud = {"hasta": 0.0, "rota": ""}
# Tablas que se leen enteras en cada vuelta, y su clave si no es `id`
ENTERAS = ("productos", "clientes", "clientes_auditoria", "mp_pagos", "gastos")
CLAVE = {"clientes_auditoria": "evento", "mp_pagos": "payment_id"}
# El resto de la tienda también se copia, para poder restaurarla desde acá. Estas no: son del momento.
NO_COPIAR = ("terminales_activos",)
# Una tabla del resto con más filas que esto se trae desde el último id; las chicas, enteras
GRANDE = 5000
# Un ticket más nuevo que esto, sin sus líneas, todavía se está cargando. Uno viejo no frena la copia.
GRACIA_EDICION_SEG = 120
_CERRADOS = {
    "COMPLETADA", "CERRADA", "CANCELADA", "ANULADA",
    "COMPLETADO", "CERRADO", "CANCELADO", "ANULADO",
}


def carpeta() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "CobroFacil_PRO", "espejo_tienda")


def ruta() -> str:
    return os.path.join(carpeta(), ARCHIVO)


def rutas_nodo() -> list[str]:
    """Tres sitios en esta PC. La primera es la que lee el jefe; las otras son respaldo."""
    from src.utils.paths import get_base_path

    user = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    return [
        ruta(),
        os.path.join(get_base_path(), "backups", "nodo", ARCHIVO),
        os.path.join(user, "Documents", "CobroFacil_Backups", "nodo", ARCHIVO),
    ]


def existe(path: str | None = None) -> bool:
    p = path or ruta()
    return os.path.isfile(p) and os.path.getsize(p) > 0


def _ahora() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _valor(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (_dt.datetime, _dt.date, _dt.time, _dt.timedelta)):
        return str(v)
    return v


def _abrir_ro(path: str) -> sqlite3.Connection:
    from pathlib import Path

    conn = sqlite3.connect(Path(path).as_uri() + "?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def meta(path: str | None = None) -> dict:
    p = path or ruta()
    if not existe(p):
        return {}
    try:
        conn = _abrir_ro(p)
        try:
            return {r["clave"]: r["valor"] for r in conn.execute("SELECT clave, valor FROM espejo_meta")}
        finally:
            conn.close()
    except Exception:
        return {}


def _meta_poner(conn: sqlite3.Connection, **datos) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS espejo_meta (clave TEXT PRIMARY KEY, valor TEXT)")
    conn.executemany(
        "INSERT OR REPLACE INTO espejo_meta (clave, valor) VALUES (?, ?)",
        [(k, str(v)) for k, v in datos.items()],
    )


def _max_id(conn: sqlite3.Connection, tabla: str) -> int:
    try:
        fila = conn.execute(f'SELECT MAX(id) FROM "{tabla}"').fetchone()
        return int(fila[0] or 0) if fila else 0
    except sqlite3.Error:
        return 0


def _conectar_tienda():
    """Conexión propia a la MariaDB de la maestra. Nunca cae a SQLite: si no hay tienda, None."""
    from src.base_de_datos.database import db_manager

    if getattr(db_manager, "db_engine_type", "") != "mariadb" or getattr(db_manager, "_forced_local_offline", False):
        return None
    motor = getattr(db_manager, "mariadb_engine", None)
    if motor is None:
        return None
    import pymysql

    kw = motor._connect_kwargs()
    kw.update(connect_timeout=3, read_timeout=90, write_timeout=10, cursorclass=pymysql.cursors.DictCursor)
    return pymysql.connect(**kw)


def _motivo_rota(e: Exception) -> str:
    args = getattr(e, "args", ()) or ()
    if args and args[0] in CODIGOS_ROTA:
        return str(args[1] if len(args) > 1 else e)
    return ""


def tienda_rota() -> str:
    """Motivo si la maestra contesta pero sus tablas no se leen; '' si está sana o no hay maestra. Cache 60 s."""
    ahora = time.monotonic()
    if ahora < _salud["hasta"]:
        return _salud["rota"]
    motivo = ""
    try:
        tienda = _conectar_tienda()
        if tienda is not None:
            try:
                _leer(tienda, "SELECT id FROM ventas ORDER BY id DESC LIMIT 1")
                _leer(tienda, "SELECT id FROM clientes LIMIT 1")
            finally:
                tienda.close()
    except Exception as e:
        motivo = _motivo_rota(e)
    _salud.update(hasta=ahora + 60, rota=motivo)
    return motivo


def _leer(tienda, sql: str, params: tuple = ()) -> list[dict]:
    with tienda.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall() or [])


def _tablas_tienda(tienda) -> dict[str, dict]:
    """Todas las tablas de la tienda: su clave primaria y si guardan archivos (blob)."""
    tablas = {
        str(r["t"]): {"clave": [], "blob": False}
        for r in _leer(
            tienda,
            "SELECT TABLE_NAME AS t FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'",
        )
    }
    for r in _leer(
        tienda,
        "SELECT TABLE_NAME AS t, COLUMN_NAME AS c FROM information_schema.KEY_COLUMN_USAGE "
        "WHERE TABLE_SCHEMA = DATABASE() AND CONSTRAINT_NAME = 'PRIMARY' ORDER BY ORDINAL_POSITION",
    ):
        if r["t"] in tablas:
            tablas[r["t"]]["clave"].append(str(r["c"]))
    for r in _leer(
        tienda,
        "SELECT DISTINCT TABLE_NAME AS t FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND DATA_TYPE LIKE '%%blob'",
    ):
        if r["t"] in tablas:
            tablas[r["t"]]["blob"] = True
    return tablas


def _resto(tablas: dict[str, dict], negocio: tuple) -> list[str]:
    """Tablas de la tienda que no son las del jefe. `detalle_ventas` vieja ya entra como detalles si no hay otra."""
    fuera = set(negocio) | set(NO_COPIAR)
    if "detalles_ventas" not in tablas:
        fuera.add("detalle_ventas")
    return sorted(t for t in tablas if t not in fuera)


def _leer_resto(tienda, tabla: str, info: dict, local: sqlite3.Connection, completo: bool) -> list[dict] | None:
    """None = esta vuelta no se trae (tabla con archivos fuera de la copia completa del día)."""
    if info["blob"] and not completo:
        return None
    if tabla in ENTERAS:
        return _leer(tienda, f"SELECT * FROM `{tabla}`")
    desde_id = _max_id(local, tabla) if info["clave"] == ["id"] and not completo else 0
    if desde_id:
        n = int((_leer(tienda, f"SELECT COUNT(*) AS n FROM `{tabla}`")[0] or {}).get("n") or 0)
        if n > GRANDE:
            return _leer(tienda, f"SELECT * FROM `{tabla}` WHERE id > %s", (desde_id,))
    return _leer(tienda, f"SELECT * FROM `{tabla}`")


def _leer_tabla(tienda, tabla: str, local: sqlite3.Connection, completo: bool, info: dict | None = None):
    import pymysql

    try:
        if info is not None:
            return _leer_resto(tienda, tabla, info, local, completo)
        return _leer_tabla_tienda(tienda, tabla, local, completo)
    except pymysql.err.ProgrammingError as e:
        # 1146 = la tienda no tiene esa tabla. Una tabla dañada (1877, 1932) sí corta la copia.
        if e.args and e.args[0] == 1146:
            return []
        raise


def _abrir_foto(tienda) -> None:
    """Un instante de la tienda. Lo que se está editando no entra en esta vuelta."""
    try:
        with tienda.cursor() as cur:
            cur.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT")
        return
    except Exception:
        pass
    try:
        tienda.begin()
    except Exception:
        pass


def _cerrar_foto(tienda) -> None:
    try:
        tienda.rollback()
    except Exception:
        pass


def _edad_seg(fila: dict) -> float | None:
    fecha = fila.get("fecha")
    if isinstance(fecha, _dt.datetime):
        momento = fecha
    else:
        try:
            momento = _dt.datetime.strptime(str(fecha or "")[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    return (_dt.datetime.now() - momento).total_seconds()


def _lineas_de(detalles: list[dict], locales: sqlite3.Connection, id_venta: int) -> int:
    n = 0
    for fila in detalles:
        try:
            if int(fila.get("id_venta") or 0) == id_venta:
                n += 1
        except (TypeError, ValueError):
            continue
    if n:
        return n
    for tabla in ("detalles_ventas", "detalle_ventas"):
        try:
            fila = locales.execute(
                f'SELECT COUNT(*) FROM "{tabla}" WHERE id_venta = ?',
                (id_venta,),
            ).fetchone()
        except sqlite3.Error:
            continue
        if fila and int(fila[0] or 0):
            return int(fila[0])
    return 0


def _en_edicion(fila: dict, lineas: int) -> bool:
    """Cerrado y con líneas: se baja. Sin líneas y recién cargado: se deja para la vuelta que viene."""
    estado = str(fila.get("estado") or "").upper()
    edad = _edad_seg(fila)
    reciente = edad is None or edad < GRACIA_EDICION_SEG
    if not reciente:
        return False
    if estado not in _CERRADOS:
        return True
    if lineas > 0:
        return False
    try:
        total = float(fila.get("total") or 0)
    except (TypeError, ValueError):
        total = 0
    return abs(total) > 0.001


def recortar_tickets(ventas: list[dict], detalles: list[dict], locales: sqlite3.Connection) -> tuple[list[dict], list[dict], int]:
    """No baja el ticket en edición ni nada posterior: si no, el id siguiente tapa el hueco."""
    corte = 0
    for fila in ventas or []:
        try:
            vid = int(fila.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if vid and _en_edicion(fila, _lineas_de(detalles or [], locales, vid)) and (not corte or vid < corte):
            corte = vid
    if not corte:
        return list(ventas or []), list(detalles or []), 0
    ventas_ok = []
    for fila in ventas or []:
        try:
            if int(fila.get("id") or 0) < corte:
                ventas_ok.append(fila)
        except (TypeError, ValueError):
            ventas_ok.append(fila)
    detalles_ok = []
    for fila in detalles or []:
        try:
            padre = int(fila.get("id_venta") or 0)
        except (TypeError, ValueError):
            detalles_ok.append(fila)
            continue
        if padre < corte:
            detalles_ok.append(fila)
    return ventas_ok, detalles_ok, corte


def _leer_tabla_tienda(tienda, tabla: str, local: sqlite3.Connection, completo: bool) -> list[dict]:
    """Tablas chicas enteras; las que crecen, desde el último id. Ventas: también los últimos días."""
    nombre = tabla
    if tabla == "detalles_ventas":
        hay = _leer(tienda, "SHOW TABLES LIKE 'detalles_ventas'")
        nombre = "detalles_ventas" if hay else "detalle_ventas"
    if completo or tabla in ENTERAS:
        return _leer(tienda, f"SELECT * FROM {nombre}")
    desde_id = _max_id(local, tabla)
    if tabla == "ventas":
        dia = (_dt.date.today() - _dt.timedelta(days=DIAS_VIVOS)).strftime("%Y-%m-%d 00:00:00")
        return _leer(tienda, "SELECT * FROM ventas WHERE id > %s OR fecha >= %s", (desde_id, dia))
    return _leer(tienda, f"SELECT * FROM {nombre} WHERE id > %s", (desde_id,))


def _asegurar_tabla(conn: sqlite3.Connection, tabla: str, claves: list[str], pk: list[str] | None = None) -> bool:
    """Crea o ensancha la tabla con las columnas de la tienda. True si tiene clave primaria."""
    info = conn.execute(f'PRAGMA table_info("{tabla}")').fetchall()
    if not info:
        pk = [CLAVE.get(tabla, "id")] if pk is None else [c for c in pk if c in claves]
        if pk == ["id"]:
            cols = ", ".join('"id" INTEGER PRIMARY KEY' if c == "id" else f'"{c}"' for c in claves)
        else:
            cols = ", ".join(f'"{c}"' for c in claves)
            if pk:
                cols += ", PRIMARY KEY (" + ", ".join(f'"{c}"' for c in pk) + ")"
        conn.execute(f'CREATE TABLE "{tabla}" ({cols})')
        return bool(pk)
    tiene = {r[1] for r in info}
    for c in claves:
        if c not in tiene:
            conn.execute(f'ALTER TABLE "{tabla}" ADD COLUMN "{c}"')
    return any(r[5] for r in info)


def _volcar_filas(conn: sqlite3.Connection, tabla: str, filas: list[dict] | None, pk: list[str] | None = None) -> int:
    """Con clave: agrega o reemplaza, nunca borra. Sin clave: la tabla se reemplaza entera (vino completa)."""
    if not filas:
        return 0
    claves = list(filas[0].keys())
    if not _asegurar_tabla(conn, tabla, claves, pk):
        conn.execute(f'DELETE FROM "{tabla}"')
    cols = ", ".join(f'"{c}"' for c in claves)
    marcas = ", ".join("?" * len(claves))
    conn.executemany(
        f'INSERT OR REPLACE INTO "{tabla}" ({cols}) VALUES ({marcas})',
        [tuple(_valor(f.get(c)) for c in claves) for f in filas],
    )
    return len(filas)


CUPO_VIEJAS = 10


def podar_viejas(cupo: int = CUPO_VIEJAS) -> int:
    """Deja las diez copias viejas más nuevas. La más antigua se va, como una cámara."""
    borradas = 0
    carpetas = {carpeta()}
    for dest in rutas_nodo():
        carpetas.add(os.path.dirname(dest))
    for folder in carpetas:
        if not os.path.isdir(folder):
            continue
        viejas = [
            os.path.join(folder, nombre)
            for nombre in os.listdir(folder)
            if nombre.startswith("espejo_tienda_hasta_") and nombre.endswith(".db")
        ]
        viejas.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        for path in viejas[max(1, int(cupo)):]:
            try:
                os.remove(path)
                borradas += 1
            except OSError:
                pass
    if borradas:
        logger.info(f"Cámara del espejo: se fueron {borradas} copias viejas")
    return borradas


def _archivar(path: str) -> str:
    """La tienda volvió atrás o es otra maestra: se guarda la copia vieja entera y se arranca otra."""
    destino = os.path.join(carpeta(), f"espejo_tienda_hasta_{_dt.datetime.now():%Y%m%d_%H%M%S}.db")
    for sufijo in ("-wal", "-shm"):
        try:
            os.remove(path + sufijo)
        except OSError:
            pass
    os.replace(path, destino)
    podar_viejas()
    return destino


def _refrescar(tienda, completo: bool) -> dict:
    os.makedirs(carpeta(), exist_ok=True)
    path = ruta()
    _abrir_foto(tienda)
    try:
        return _refrescar_foto(tienda, completo, path)
    finally:
        _cerrar_foto(tienda)


def _refrescar_foto(tienda, completo: bool, path: str) -> dict:
    from src.jefe.nodo_portable.motor_nodo import TABLAS_NEGOCIO, _ensure_negocio_schema

    tope_tienda = int((_leer(tienda, "SELECT MAX(id) AS m FROM ventas")[0] or {}).get("m") or 0)
    servidor = str((_leer(tienda, "SELECT @@hostname AS h")[0] or {}).get("h") or "")
    if existe(path):
        conn = sqlite3.connect(path, timeout=15)
        tope_copia = _max_id(conn, "ventas")
        try:
            fila = conn.execute("SELECT valor FROM espejo_meta WHERE clave = 'servidor'").fetchone()
        except sqlite3.Error:
            fila = None
        conn.close()
        servidor_copia = str(fila[0]) if fila and fila[0] else ""
        motivo = ""
        if servidor and servidor_copia != servidor:
            motivo = f"es otra maestra ({servidor}, la copia era de {servidor_copia or 'sin anotar'})"
        elif tope_copia and tope_tienda < tope_copia:
            motivo = f"la maestra tiene menos ventas (id {tope_tienda}) que la copia ({tope_copia})"
        if motivo:
            viejo = _archivar(path)
            logger.warning(f"Espejo tienda: {motivo}. Copia anterior guardada en {viejo}.")
            completo = True

    conn = sqlite3.connect(path, timeout=15)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        _ensure_negocio_schema(conn)
        previo = {}
        try:
            previo = {r[0]: r[1] for r in conn.execute("SELECT clave, valor FROM espejo_meta")}
        except sqlite3.Error:
            pass
        hoy = _dt.date.today().isoformat()
        completo = completo or str(previo.get("ultimo_completo", ""))[:10] != hoy

        tablas = _tablas_tienda(tienda)
        resto = _resto(tablas, TABLAS_NEGOCIO)
        lotes = {t: _leer_tabla(tienda, t, conn, completo) for t in TABLAS_NEGOCIO}
        lotes_resto = {t: _leer_tabla(tienda, t, conn, completo, tablas[t]) for t in resto}
        _, _, corte = recortar_tickets(
            lotes.get("ventas") or [],
            lotes.get("detalles_ventas") or [],
            conn,
        )
        if corte:
            conn.rollback()
            logger.info("espejo  ticket %s en edicion, la vuelta no se pasa", corte)
            return {"estado": "en_edicion", "corte": corte}
        stats = {t: _volcar_filas(conn, t, filas) for t, filas in lotes.items()}
        stats.update({t: _volcar_filas(conn, t, filas, tablas[t]["clave"]) for t, filas in lotes_resto.items()})
        cuando = _ahora()
        datos = {
            "ultima_copia": cuando,
            "origen": socket.gethostname() or "",
            "servidor": servidor,
            "tablas": len(TABLAS_NEGOCIO) + len(resto),
            "completa": "1",
        }
        if completo:
            datos["ultimo_completo"] = cuando
        _meta_poner(conn, **datos)
        conn.commit()
        return {"estado": "ok", "cuando": cuando, "completo": completo, **stats}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _anotar(resultado: str, detalle: str = "") -> dict:
    _estado.update(cuando=_ahora(), resultado=resultado, detalle=detalle)
    return {"estado": resultado, "detalle": detalle}


def _candado_proceso():
    """Un solo proceso escribe la copia. El otro deja la vuelta para después."""
    os.makedirs(carpeta(), exist_ok=True)
    fh = open(os.path.join(carpeta(), "espejo.lock"), "a+b")
    try:
        if fh.seek(0, os.SEEK_END) < 1:
            fh.write(b" ")
            fh.flush()
        fh.seek(0)
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return None
    return fh


def _soltar_candado(fh) -> None:
    try:
        if sys.platform == "win32":
            import msvcrt

            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        fh.close()
    except OSError:
        pass


def refrescar(completo: bool = False) -> dict:
    """Tienda → copia local. Sin maestra no toca nada. Si la tienda da error, la copia queda como estaba."""
    if not _lock.acquire(blocking=False):
        return {"estado": "ocupado"}
    try:
        candado = _candado_proceso()
    except Exception:
        _lock.release()
        raise
    if candado is None:
        _lock.release()
        return {"estado": "ocupado"}
    try:
        tienda = _conectar_tienda()
        if tienda is None:
            return _anotar("sin_tienda")
        try:
            res = _refrescar(tienda, completo)
        finally:
            tienda.close()
        if res.get("estado") == "en_edicion":
            return _anotar("en_edicion", str(res.get("corte") or ""))
        _anotar("ok", res.get("cuando", ""))
        _salud.update(hasta=time.monotonic() + 60, rota="")
        replicar_rutas()
        return res
    except Exception as e:
        logger.warning(f"Espejo tienda: no se refrescó, la copia queda como estaba ({e})")
        motivo = _motivo_rota(e)
        if motivo:
            _salud.update(hasta=time.monotonic() + 60, rota=motivo)
        return _anotar("error", str(e))
    finally:
        _soltar_candado(candado)
        _lock.release()


def volcar_a(destino: str) -> None:
    """Copia entera y consistente de la copia local al pendrive (backup de SQLite, no copia de archivo)."""
    if not existe():
        raise RuntimeError("Esta PC todavía no tiene copia de la tienda. Conectate a la maestra una vez.")
    tmp = destino + ".nuevo"
    try:
        os.remove(tmp)
    except OSError:
        pass
    origen = _abrir_ro(ruta())
    copia = sqlite3.connect(tmp)
    try:
        origen.backup(copia)
        copia.execute("PRAGMA journal_mode=DELETE")
        copia.commit()
    finally:
        copia.close()
        origen.close()
    os.replace(tmp, destino)


def replicar_rutas() -> int:
    """La copia que ya está en AppData se vuelca a las otras rutas del nodo."""
    if not existe():
        return 0
    origen = os.path.normcase(os.path.abspath(ruta()))
    hechas = 0
    for dest in rutas_nodo():
        if os.path.normcase(os.path.abspath(dest)) == origen:
            continue
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            volcar_a(dest)
            hechas += 1
        except Exception as e:
            logger.warning(f"Nodo: no se pudo copiar a {dest} ({e})")
    if hechas:
        logger.info(f"Nodo: copia en {hechas + 1} rutas de esta PC")
    return hechas


def estado() -> dict:
    return {**_estado, **meta()}


def arrancar(pausa: int = 60) -> None:
    """Hilo de fondo: refresca cada `pausa` segundos (un minuto). Una sola vez por proceso."""
    global _hilo
    if _hilo is not None and _hilo.is_alive():
        return

    def _vuelta():
        try:
            podar_viejas()
            if existe():
                replicar_rutas()
        except Exception as e:
            logger.warning("Hilo del espejo: no pudo podar ni volcar al arrancar (%s)", e)
        time.sleep(20)
        while True:
            try:
                refrescar()
            except Exception as e:
                logger.warning("Hilo del espejo: la vuelta falló y la copia queda (%s)", e)
            time.sleep(pausa)

    _hilo = threading.Thread(target=_vuelta, name="espejo_tienda", daemon=True)
    _hilo.start()
