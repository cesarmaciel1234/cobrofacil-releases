"""
La tienda chupa los eventos de clientes hechos sin red (en casa o en una notebook).

No copia fichas ni saldos: aplica eventos. Cada evento entra una sola vez porque su ID es
la clave de `clientes_auditoria`. Si dos PCs lo intentan a la vez, la segunda choca y no aplica.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
from pathlib import Path

from src.clientes_fiado.oficina.huella import pc as huella_pc
from src.clientes_fiado.oficina.huella import tabla
from src.clientes_fiado.oficina.huella.eventos import CAMPOS_FICHA, _dic, _insert_sql, limpio, valores

_despertar = threading.Event()
_hilo: threading.Thread | None = None
_estado: dict = {}


def _db():
    from src.base_de_datos.database import db_manager

    return db_manager


def _logger():
    from src.logger import logger

    return logger


# ── Leer eventos de un archivo SQLite (nodo o punpro.db) ──────────────────────

def leer_eventos(path: str, solo_pc: str | None = None) -> list[dict]:
    """Eventos hechos sin red (`base = 'LOCAL'`), por fecha. [] si el archivo no tiene el libro."""
    if not path or not os.path.isfile(path):
        return []
    try:
        conn = sqlite3.connect(Path(path).as_uri() + "?mode=ro", uri=True, timeout=5)
    except Exception:
        return []
    try:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM clientes_auditoria WHERE base = 'LOCAL'"
        params: tuple = ()
        if solo_pc:
            sql += " AND pc = ?"
            params = (solo_pc,)
        return [dict(r) for r in conn.execute(sql + " ORDER BY fecha, evento", params).fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def filtrar_cancelaciones_pendientes(eventos: list[dict], path: str) -> list[dict]:
    if not eventos or not path or not os.path.isfile(path):
        return eventos

    def es_cancelacion_f3(evento):
        if str(evento.get("accion") or "").upper() != "ANULACION":
            return False
        try:
            detalle = json.loads(evento.get("detalle") or "{}")
        except (TypeError, json.JSONDecodeError):
            return False
        return bool(detalle.get("cancelacion_f3"))

    try:
        with sqlite3.connect(Path(path).as_uri() + "?mode=ro", uri=True, timeout=5) as conn:
            filas = conn.execute(
                "SELECT local_venta_id, request_id FROM offline_cancelaciones"
            ).fetchall()
    except sqlite3.OperationalError as error:
        if "no such table" in str(error).lower():
            return eventos
        _logger().warning("No se pudieron leer cancelaciones pendientes de huella: %s", error)
        return [evento for evento in eventos if not es_cancelacion_f3(evento)]
    except sqlite3.Error as error:
        _logger().warning("No se pudieron leer cancelaciones pendientes de huella: %s", error)
        return [evento for evento in eventos if not es_cancelacion_f3(evento)]
    venta_ids = {str(fila[0]) for fila in filas}
    request_ids = {str(fila[1]) for fila in filas if fila[1]}
    salida = []
    for evento in eventos:
        if str(evento.get("accion") or "").upper() != "ANULACION":
            salida.append(evento)
            continue
        try:
            detalle = json.loads(evento.get("detalle") or "{}")
        except (TypeError, json.JSONDecodeError):
            detalle = {}
        if not detalle.get("cancelacion_f3"):
            salida.append(evento)
            continue
        venta_local = str(detalle.get("venta_id") or "")
        request_id = str(detalle.get("venta_request_id") or "")
        if venta_local not in venta_ids and request_id not in request_ids:
            salida.append(evento)
    return salida


# ── Aplicar en la tienda ──────────────────────────────────────────────────────

def _ya_estan(db, ids: list[str]) -> set[str]:
    hay: set[str] = set()
    for i in range(0, len(ids), 200):
        lote = ids[i:i + 200]
        filas = db.execute_query(
            f"SELECT evento FROM clientes_auditoria WHERE evento IN ({', '.join('?' * len(lote))})",
            tuple(lote),
        ) or []
        hay |= {str(_dic(f, ("evento",)).get("evento")) for f in filas}
    return hay


def _uno(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchone()


def _resolver(cur, uid) -> int | None:
    if not uid:
        return None
    fila = _uno(cur, "SELECT id FROM clientes WHERE uid = ?", (uid,))
    if fila:
        return _dic(fila, ("id",)).get("id")
    fila = _uno(
        cur,
        "SELECT cliente_id FROM clientes_auditoria WHERE accion = 'FUSION' AND cliente_uid = ?",
        (uid,),
    )
    return _dic(fila, ("cliente_id",)).get("cliente_id") if fila else None


def _dni(texto) -> str:
    d = "".join(c for c in str(texto or "") if c.isdigit())
    return d if len(d) >= 7 else ""


def _gemelo(cur, ficha: dict) -> int | None:
    """El mismo cliente ya cargado en la tienda: mismo DNI, o sin DNI y mismo nombre."""
    dni = _dni(ficha.get("dni"))
    if dni:
        fila = _uno(cur, "SELECT id FROM clientes WHERE dni = ?", (dni,))
        return _dic(fila, ("id",)).get("id") if fila else None
    nombre = limpio(ficha.get("nombre")).strip()
    if not nombre:
        return None
    fila = _uno(cur, "SELECT id FROM clientes WHERE nombre = ? AND (dni IS NULL OR dni = '')", (nombre,))
    return _dic(fila, ("id",)).get("id") if fila else None


def _deuda(cur, cid) -> float:
    fila = _uno(cur, "SELECT deuda_actual FROM clientes WHERE id = ?", (cid,))
    try:
        return float(_dic(fila, ("deuda_actual",)).get("deuda_actual") or 0)
    except (TypeError, ValueError):
        return 0.0


def _es_duplicado(e: Exception) -> bool:
    """El evento ya estaba (clave repetida). Otro error no es 'repetido': se reintenta en la próxima vuelta."""
    args = getattr(e, "args", ()) or ()
    texto = str(e)
    return (bool(args) and args[0] == 1062) or "Duplicate entry" in texto or "UNIQUE constraint" in texto


def _firma(ev: dict) -> str:
    return f"cargado en {ev.get('pc')} por {ev.get('usuario')} el {ev.get('fecha')}"


def _venta_remota(cur, venta_local, request_id=None) -> int:
    if request_id:
        fila = _uno(cur, "SELECT id FROM ventas WHERE request_id = ?", (request_id,))
    else:
        fila = _uno(cur, "SELECT id FROM ventas WHERE id = ?", (venta_local,))
    venta = _dic(fila, ("id",)).get("id") if fila else None
    if venta is None:
        raise ValueError(f"No llegó a la tienda el ticket offline {venta_local}")
    return int(venta)


def _remapear_reverso(descripcion: str, referencias: dict[str, str]) -> str:
    from src.clientes_fiado.oficina.cuenta.interes import MARCA_REVERSO

    inicio = descripcion.find(MARCA_REVERSO)
    if inicio < 0:
        return descripcion
    prefijo = descripcion[:inicio]
    reverso = json.loads(descripcion[inicio + len(MARCA_REVERSO):])
    ticket_local = str(reverso.get("ticket") or "")
    ticket_remoto = referencias.get(ticket_local)
    if not ticket_remoto:
        raise ValueError("No se pudo asociar la reversión de interés con el ticket remoto")
    numero_local = ticket_local[2:]
    numero_remoto = ticket_remoto[2:]
    prefijo = prefijo.replace(f"#{numero_local}", f"#{numero_remoto}")
    prefijo = re.sub(
        rf"(?i)(ticket\s+){re.escape(numero_local)}\b",
        rf"\g<1>{numero_remoto}",
        prefijo,
    )
    reverso["ticket"] = ticket_remoto
    return prefijo + MARCA_REVERSO + json.dumps(
        reverso, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )


def _movimiento(cur, ev: dict, cid: int, det: dict) -> None:
    monto = float(det.get("monto") or 0)
    if monto <= 0:
        return
    deuda = _deuda(cur, cid)
    accion = str(ev.get("accion") or "").upper()
    venta_id = None
    descripcion = str(det.get("descripcion") or accion.title())
    fecha = ev.get("fecha")
    if not fecha:
        raise ValueError(f"El evento offline {ev.get('evento')} no tiene fecha")
    if accion == "CARGO":
        tipo, saldo = "CARGO", deuda + monto
        interes_tickets = det.get("interes_tickets")
        if isinstance(interes_tickets, dict) and interes_tickets:
            from decimal import Decimal

            from src.clientes_fiado.oficina.cuenta.interes import descripcion_interes

            request_ids = det.get("interes_tickets_request_ids") or {}
            remapeo = {}
            detalle = {}
            for ticket, interes in interes_tickets.items():
                ticket = str(ticket)
                if not ticket.startswith("V:"):
                    raise ValueError("Clave de ticket inválida en evento offline")
                venta_local = ticket[2:]
                venta_id_remoto = _venta_remota(
                    cur,
                    venta_local,
                    request_ids.get(ticket),
                )
                ticket_remoto = f"V:{venta_id_remoto}"
                if ticket_remoto in detalle:
                    raise ValueError("Tickets duplicados al sincronizar el interés offline")
                remapeo[ticket] = ticket_remoto
                detalle[ticket_remoto] = Decimal(str(interes))
            descripcion = descripcion_interes(detalle)
            det["interes_tickets"] = {
                ticket: str(monto) for ticket, monto in detalle.items()
            }
            det["descripcion"] = descripcion
            det["interes_tickets_request_ids"] = {
                ticket: request_ids.get(ticket_local)
                for ticket_local, ticket in remapeo.items()
                if request_ids.get(ticket_local)
            }
    elif accion == "ANULACION":
        tipo, saldo = "ANULACION", deuda - monto
        venta_local = det.get("venta_id")
        if venta_local not in (None, "", 0, "0"):
            venta_id = _venta_remota(
                cur,
                str(venta_local),
                det.get("venta_request_id"),
            )
            referencia = {f"V:{venta_local}": f"V:{venta_id}"}
            descripcion = _remapear_reverso(descripcion, referencia)
            det["venta_id"] = venta_id
            det["descripcion"] = descripcion
            if det.get("venta_request_id"):
                det["venta_request_id"] = str(det["venta_request_id"])
            cur.execute(
                "SELECT estado FROM ventas WHERE id = ?",
                (venta_id,),
            )
            estado_venta = str(_dic(cur.fetchone(), ("estado",)).get("estado") or "").upper()
            if estado_venta in ("CANCELADA", "CANCELADO", "ANULADA", "ANULADO"):
                cur.execute(
                    "SELECT id FROM cuenta_corriente WHERE tipo = 'ANULACION' "
                    "AND venta_id IN (?, ?) LIMIT 1",
                    (venta_id, str(venta_id)),
                )
                if cur.fetchone():
                    return
            cur.execute(
                "SELECT id, descripcion FROM cuenta_corriente "
                "WHERE venta_id IN (?, ?) AND tipo = 'CARGO' ORDER BY id DESC LIMIT 1",
                (venta_id, str(venta_id)),
            )
            cargo = cur.fetchone()
            if cargo:
                fila_cargo = _dic(cargo, ("id", "descripcion"))
                actual = str(fila_cargo.get("descripcion") or "")
                if not actual.startswith(("CANCELADO · ", "BORRADO · ")):
                    cur.execute(
                        "UPDATE cuenta_corriente SET descripcion = ? WHERE id = ?",
                        (f"CANCELADO · {actual or f'Ticket #{venta_id}'}", fila_cargo.get("id")),
                    )
    else:
        tipo, saldo = "ABONO", max(0.0, deuda - monto)
    cur.execute("UPDATE clientes SET deuda_actual = ? WHERE id = ?", (saldo, cid))
    cur.execute(
        "INSERT INTO cuenta_corriente "
        "(cliente_id, fecha, tipo, monto, saldo_resultante, descripcion, venta_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            cid,
            fecha,
            tipo,
            monto,
            saldo,
            descripcion if tipo in ("CARGO", "ANULACION") and (
                descripcion.startswith("INTERÉS MENSUAL") or tipo == "ANULACION"
            ) else limpio(f"{descripcion} · {_firma(ev)}", 250),
            venta_id,
        ),
    )


def _ficha_vieja(cur, cid, fecha_evento) -> bool:
    """True si la tienda editó la ficha después del evento: gana la tienda."""
    fila = _uno(cur, "SELECT actualizado_en FROM clientes WHERE id = ?", (cid,))
    actual = str(_dic(fila, ("actualizado_en",)).get("actualizado_en") or "")
    return bool(actual) and actual > str(fecha_evento or "")


def _alta(cur, ev: dict, det: dict) -> tuple[int | None, str]:
    ficha = det.get("ficha") or {}
    uid = ev.get("cliente_uid")
    gemelo = _gemelo(cur, ficha)
    if gemelo:
        fusion = dict(ev, evento=f"FUS-{uid}"[:80], accion="FUSION", cliente_id=gemelo, base="TIENDA",
                      llego_en=huella_pc.ahora(), llego_via="MOTOR",
                      detalle=json.dumps({"uid_origen": uid, "motivo": "mismo DNI o nombre"}, ensure_ascii=True))
        cur.execute(_insert_sql(), valores(fusion))
        return gemelo, "FUSION"
    datos = {k: ficha.get(k) for k in CAMPOS_FICHA + ("limite_credito",) if k in ficha}
    datos["nombre"] = limpio(datos.get("nombre")) or "Sin nombre"
    datos.update(deuda_actual=0, uid=uid, origen_pc=ev.get("pc"), creado_por=ev.get("usuario"),
                 creado_en=ev.get("fecha"), actualizado_en=ev.get("fecha"))
    cols = list(datos.keys())
    cur.execute(
        f"INSERT INTO clientes ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
        tuple(datos[c] for c in cols),
    )
    return _resolver(cur, uid), ""


def aplicar_evento(ev: dict, via: str, db=None) -> str:
    """
    'aplicado' | 'repetido' | 'pendiente' (el cliente todavía no llegó) | 'error'.
    Todo en una transacción: el evento y su efecto entran juntos o no entra nada.
    """
    db = db or _db()
    conn = None
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        fila = dict(ev, llego_en=huella_pc.ahora(), llego_via=via)
        try:
            cur.execute(_insert_sql(), valores(fila))
        except Exception as e:
            conn.rollback()
            if _es_duplicado(e):
                return "repetido"
            raise
        try:
            det = json.loads(ev.get("detalle") or "{}")
        except Exception:
            det = {}
        accion = str(ev.get("accion") or "").upper()
        cid = _resolver(cur, ev.get("cliente_uid"))
        nota = ""
        if accion == "ALTA":
            if not cid:
                cid, nota = _alta(cur, ev, det)
        elif not cid:
            conn.rollback()
            return "pendiente"
        elif accion in ("EDICION", "LIMITE"):
            if _ficha_vieja(cur, cid, ev.get("fecha")):
                nota = "TIENDA_MAS_NUEVA"
            else:
                permitidos = CAMPOS_FICHA + ("limite_credito",)
                cambios = {k: v for k, v in (det.get("despues") or {}).items() if k in permitidos}
                if "nombre" in cambios:
                    cambios["nombre"] = limpio(cambios["nombre"])
                if cambios:
                    cambios["actualizado_en"] = ev.get("fecha")
                    sets = ", ".join(f"{k} = ?" for k in cambios)
                    cur.execute(f"UPDATE clientes SET {sets} WHERE id = ?", tuple(cambios.values()) + (cid,))
        elif accion in ("CARGO", "ABONO", "ANULACION"):
            _movimiento(cur, ev, cid, det)
            if accion in ("CARGO", "ANULACION"):
                cur.execute(
                    "UPDATE clientes_auditoria SET detalle = ? WHERE evento = ?",
                    (json.dumps(det, ensure_ascii=True, separators=(",", ":"), default=str), ev["evento"]),
                )
        cur.execute(
            "UPDATE clientes_auditoria SET cliente_id = ?, llego_via = ? WHERE evento = ?",
            (cid, f"{via}:{nota}" if nota else via, ev["evento"]),
        )
        conn.commit()
        return "aplicado"
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        try:
            _logger().warning(f"[huella] evento {ev.get('evento')} no entró: {e}")
        except Exception:
            pass
        return "error"
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def aplicar(eventos: list[dict], via: str, db=None) -> dict:
    db = db or _db()
    cuenta = {"aplicado": 0, "repetido": 0, "pendiente": 0, "error": 0}
    if not eventos or not tabla.asegurar(db):
        return cuenta
    ya = _ya_estan(db, [str(e.get("evento")) for e in eventos])
    for ev in eventos:
        if str(ev.get("evento")) in ya:
            cuenta["repetido"] += 1
            continue
        cuenta[aplicar_evento(ev, via, db)] += 1
    return cuenta


# ── Fuentes ───────────────────────────────────────────────────────────────────

def _punpro_local() -> str:
    try:
        from src.utils.paths import get_base_path

        return os.path.join(get_base_path(), "punpro.db")
    except Exception:
        return ""


def _nodo_db() -> str:
    try:
        from src.jefe.nodo_portable.motor_nodo import _negocio_db_path, estado_nodo, get_nodo_path

        root = get_nodo_path()
        return _negocio_db_path(root) if root and estado_nodo(root) == "ready" else ""
    except Exception:
        return ""


def llevar_al_nodo(nodo_db: str, db=None) -> int:
    """Sin red: copia al pendrive los eventos hechos en esta PC. El nodo los lleva a la tienda."""
    db = db or _db()
    if not nodo_db or not os.path.isfile(nodo_db) or tabla.es_tienda(db):
        return 0
    filas = db.execute_query("SELECT * FROM clientes_auditoria WHERE base = 'LOCAL'") or []
    if not filas:
        return 0
    conn = sqlite3.connect(nodo_db, timeout=10)
    try:
        conn.execute(tabla.DDL_EVENTOS)
        cols = tabla.COLUMNAS_EVENTO
        antes = conn.total_changes
        conn.executemany(
            f"INSERT OR IGNORE INTO clientes_auditoria ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            [tuple(_dic(f).get(c) for c in cols) for f in filas],
        )
        conn.commit()
        return conn.total_changes - antes
    finally:
        conn.close()


def turno() -> dict:
    """Con red: la tienda chupa de esta PC y del nodo. Sin red: esta PC deja sus eventos en el nodo."""
    db = _db()
    res: dict = {"hora": huella_pc.ahora(), "pc": huella_pc.pc_id()}
    if tabla.es_tienda(db):
        try:
            from src.jefe.nodo_portable.espejo.copia import tienda_rota

            rota = tienda_rota()
        except Exception:
            rota = ""
        if rota:
            res["error"] = f"tienda con tablas dañadas: {rota}"
            _estado.clear()
            _estado.update(res)
            return res
        if not tabla.asegurar(db):
            res["error"] = "sin columnas de huella en la tienda"
            return res
        tabla.completar_uids(db)
        path_local = _punpro_local()
        eventos_locales = filtrar_cancelaciones_pendientes(
            leer_eventos(path_local, solo_pc=huella_pc.pc_id()),
            path_local,
        )
        res["local"] = aplicar(eventos_locales, "LOCAL", db)
        nodo = _nodo_db()
        if nodo:
            res["nodo"] = aplicar(leer_eventos(nodo), "NODO", db)
    else:
        tabla.asegurar(db)
        nodo = _nodo_db()
        if nodo:
            res["al_nodo"] = llevar_al_nodo(nodo, db)
    _estado.clear()
    _estado.update(res)
    return res


def estado() -> dict:
    return dict(_estado)


def despertar() -> None:
    _despertar.set()


def arrancar(pausa: int = 120) -> None:
    """Un hilo por proceso. Primera vuelta a los 30 s; después cada `pausa` segundos o al despertar."""
    global _hilo
    if _hilo and _hilo.is_alive():
        return

    def _vuelta():
        time.sleep(30)
        while True:
            try:
                res = turno()
                movidos = sum(
                    (res.get(k) or {}).get("aplicado", 0) for k in ("local", "nodo")
                ) + int(res.get("al_nodo") or 0)
                if movidos:
                    _logger().info(f"[huella] clientes: {res}")
            except Exception as e:
                try:
                    _logger().warning(f"[huella] turno falló: {e}")
                except Exception:
                    pass
            _despertar.wait(pausa)
            _despertar.clear()

    _hilo = threading.Thread(target=_vuelta, name="huella_clientes", daemon=True)
    _hilo.start()
