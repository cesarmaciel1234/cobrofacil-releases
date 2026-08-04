"""
Diario externo de ventas — "nube local" anti-wipe (estilo multinacional).

Arquitectura:
  Cobro  → encola JSON en AppData (rápido, no bloquea UI)
  Worker → hilo aparte drena la cola → diario/ + ultimo_cobro.json
  Arranque → lazy hydrate de tickets faltantes hacia la DB
  Cierre → zip del día

Ruta (fuera de la instalación del programa):
  %LOCALAPPDATA%\\CobroFacil_PRO\\ventas_externas\\
    cola/          ← pendientes (append-only)
    diario/        ← confirmados por día
    zips/          ← sello nocturno
    ultimo_cobro.json
    cloud/         ← reservado: futuro sync a la nube real

Más adelante, subir/sincronizar esta carpeta = "mandar a la nube".
"""
from __future__ import annotations

import json
import os
import socket
import threading
import time
import zipfile
from datetime import datetime, timedelta
from typing import Any, Iterable

_lock = threading.Lock()
_hydrate_started = False
_worker_started = False
_worker_stop = threading.Event()
_wake = threading.Event()

WORKER_IDLE_SEC = 2.0


def get_external_root() -> str:
    """Carpeta 'nube local' fuera del install. Override: config.ventas_externas_path."""
    try:
        from src.config import config

        custom = str(config.get("ventas_externas_path", "") or "").strip()
        if custom:
            os.makedirs(custom, exist_ok=True)
            return custom
    except Exception:
        pass
    user = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    root = os.path.join(user, "CobroFacil_PRO", "ventas_externas")
    os.makedirs(root, exist_ok=True)
    return root


def cloud_ready_root() -> str:
    """Misma raíz que un día se sincronizará a la nube (OneDrive/S3/etc.)."""
    root = get_external_root()
    cloud = os.path.join(root, "cloud")
    os.makedirs(cloud, exist_ok=True)
    return cloud


def _origen_host() -> str:
    try:
        return socket.gethostname() or ""
    except Exception:
        return ""


def _fecha_str(dt: datetime | None = None) -> str:
    return (dt or datetime.now()).strftime("%Y-%m-%d")


def _cola_dir() -> str:
    d = os.path.join(get_external_root(), "cola")
    os.makedirs(d, exist_ok=True)
    return d


def _diario_dir(fecha: str | None = None) -> str:
    d = os.path.join(get_external_root(), "diario", fecha or _fecha_str())
    os.makedirs(d, exist_ok=True)
    return d


def _zips_dir() -> str:
    d = os.path.join(get_external_root(), "zips")
    os.makedirs(d, exist_ok=True)
    return d


def _ultimo_path() -> str:
    return os.path.join(get_external_root(), "ultimo_cobro.json")


def _normalize_items(items: Iterable[Any] | None) -> list[dict]:
    out: list[dict] = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        out.append(
            {
                "id": it.get("id"),
                "nombre": it.get("nombre") or it.get("nombre_producto") or "",
                "cant": it.get("cant") if it.get("cant") is not None else it.get("cantidad", 0),
                "precio": it.get("precio") if it.get("precio") is not None else it.get("precio_unitario", 0),
                "subtotal": it.get("subtotal", 0),
            }
        )
    return out


def _build_payload(id_venta: Any, header: dict | None, items: Iterable[Any] | None) -> dict | None:
    if not id_venta or id_venta == 9999999:
        return None
    try:
        from src.config import config

        caja_id = config.get("caja_id", 1)
    except Exception:
        caja_id = 1

    hdr = dict(header or {})
    fecha = str(hdr.get("fecha") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return {
        "id": int(id_venta) if str(id_venta).isdigit() else id_venta,
        "fecha": fecha,
        "caja_id": hdr.get("caja_id", caja_id),
        "origen_host": _origen_host(),
        "total": hdr.get("total"),
        "pago_con": hdr.get("pago_con"),
        "cambio": hdr.get("cambio"),
        "pago_efectivo": hdr.get("pago_efectivo"),
        "pago_otro": hdr.get("pago_otro"),
        "usuario": hdr.get("usuario"),
        "usuario_secundario": hdr.get("usuario_secundario"),
        "metodo_pago": hdr.get("metodo_pago"),
        "estado": hdr.get("estado") or "COMPLETADA",
        "descuento": hdr.get("descuento", 0),
        "recargo": hdr.get("recargo", 0),
        "cliente_nombre": hdr.get("cliente_nombre") or "",
        "items": _normalize_items(items),
        "enqueued_at": datetime.now().isoformat(timespec="seconds"),
    }


def _persistir_payload(payload: dict) -> bool:
    """Escribe diario confirmado + ultimo_cobro (trabajo del worker)."""
    try:
        fecha = str(payload.get("fecha") or "")
        day = fecha[:10] if len(fecha) >= 10 else _fecha_str()
        raw = json.dumps(payload, ensure_ascii=False, indent=2)
        with _lock:
            path = os.path.join(_diario_dir(day), f"venta_{payload['id']}.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write(raw)
            with open(_ultimo_path(), "w", encoding="utf-8") as f:
                f.write(raw)
        return True
    except Exception:
        return False


def encolar_venta(id_venta: Any, header: dict | None, items: Iterable[Any] | None = None) -> bool:
    """
    Cobro → solo encola en AppData/cola (rápido).
    El hilo worker confirma al diario. Nunca debe tumbar el cobro.
    """
    try:
        payload = _build_payload(id_venta, header, items)
        if not payload:
            return False
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        name = f"pendiente_{stamp}_{payload['id']}.json"
        tmp = os.path.join(_cola_dir(), name + ".tmp")
        final = os.path.join(_cola_dir(), name)
        raw = json.dumps(payload, ensure_ascii=False, indent=2)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(raw)
        os.replace(tmp, final)
        _wake.set()
        start_motor_nube_local()
        return True
    except Exception:
        return False


def registrar_venta(id_venta: Any, header: dict | None, items: Iterable[Any] | None = None) -> bool:
    """Compat: el cobro encola; el motor de fondo persiste (nube local)."""
    return encolar_venta(id_venta, header, items)


def drenar_cola(max_items: int = 200) -> int:
    """Procesa pendientes cola/ → diario/. Idempotente. Devuelve cantidad."""
    done = 0
    try:
        cola = _cola_dir()
        names = sorted(n for n in os.listdir(cola) if n.endswith(".json") and not n.endswith(".tmp"))
        for name in names[:max_items]:
            path = os.path.join(cola, name)
            payload = _load_json(path)
            if not payload:
                try:
                    os.remove(path)
                except OSError:
                    pass
                continue
            if _persistir_payload(payload):
                try:
                    os.remove(path)
                except OSError:
                    pass
                done += 1
            else:
                break
    except Exception:
        pass
    return done


def sellar_dia(fecha: str | None = None) -> str | None:
    """Drena cola + zip diario/YYYY-MM-DD → zips/ventas_YYYY-MM-DD.zip."""
    try:
        drenar_cola(max_items=2000)
        day = fecha or _fecha_str()
        src = os.path.join(get_external_root(), "diario", day)
        if not os.path.isdir(src):
            return None
        files = [n for n in os.listdir(src) if n.endswith(".json")]
        if not files:
            return None
        out = os.path.join(_zips_dir(), f"ventas_{day}.zip")
        with _lock:
            with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for name in files:
                    zf.write(os.path.join(src, name), arcname=f"{day}/{name}")
        return out
    except Exception:
        return None


def _load_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _iter_payloads(max_archivos: int = 500) -> list[dict]:
    # Primero drenar cola para no perder pendientes al reconcile
    drenar_cola(max_items=max_archivos)
    root = get_external_root()
    days = [_fecha_str(), _fecha_str(datetime.now() - timedelta(days=1))]
    candidates: list[dict] = []

    for day in days:
        d = os.path.join(root, "diario", day)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".json"):
                continue
            data = _load_json(os.path.join(d, name))
            if data:
                candidates.append(data)

    ult = _load_json(_ultimo_path())
    if ult:
        candidates.append(ult)

    zdir = os.path.join(root, "zips")
    if os.path.isdir(zdir):
        for day in days:
            zp = os.path.join(zdir, f"ventas_{day}.zip")
            if not os.path.isfile(zp):
                continue
            try:
                with zipfile.ZipFile(zp, "r") as zf:
                    for info in zf.infolist():
                        if info.is_dir() or not info.filename.endswith(".json"):
                            continue
                        try:
                            data = json.loads(zf.read(info).decode("utf-8"))
                            if isinstance(data, dict):
                                candidates.append(data)
                        except Exception:
                            pass
            except Exception:
                pass

    seen: set[Any] = set()
    out: list[dict] = []
    for data in candidates:
        vid = data.get("id")
        if vid is None or vid in seen or vid == 9999999:
            continue
        seen.add(vid)
        out.append(data)
        if len(out) >= max_archivos:
            break
    return out


def _venta_existe(vid: Any) -> bool:
    try:
        from src.base_de_datos.database import db_manager

        row = db_manager.execute_query(
            "SELECT id FROM ventas WHERE id = ? LIMIT 1", (vid,)
        )
        return bool(row)
    except Exception:
        return False


def _insertar_faltante(payload: dict) -> bool:
    """Inserta venta + detalles si el id no existe. Intenta conservar el id original."""
    try:
        from src.base_de_datos.database import db_manager

        vid = payload.get("id")
        if vid is None:
            return False
        items = payload.get("items") or []
        venta_data = {
            "total": payload.get("total") or 0,
            "pago_con": payload.get("pago_con") or 0,
            "cambio": payload.get("cambio") or 0,
            "pago_efectivo": payload.get("pago_efectivo") or 0,
            "pago_otro": payload.get("pago_otro") or 0,
            "usuario": payload.get("usuario") or "",
            "estado": payload.get("estado") or "COMPLETADA",
            "metodo_pago": payload.get("metodo_pago") or "Efectivo",
            "descuento": payload.get("descuento") or 0,
            "recargo": payload.get("recargo") or 0,
            "cliente_nombre": payload.get("cliente_nombre") or "",
            "caja_id": payload.get("caja_id") or 1,
        }
        fecha = payload.get("fecha") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO ventas (
                        id, total, pago_con, cambio, pago_efectivo, pago_otro,
                        usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        vid,
                        venta_data["total"],
                        venta_data["pago_con"],
                        venta_data["cambio"],
                        venta_data["pago_efectivo"],
                        venta_data["pago_otro"],
                        venta_data["usuario"],
                        venta_data["estado"],
                        venta_data["metodo_pago"],
                        fecha,
                        venta_data["caja_id"],
                        venta_data["descuento"],
                        venta_data["recargo"],
                        venta_data["cliente_nombre"],
                    ),
                )
                new_id = vid
            except Exception:
                cur.execute(
                    """
                    INSERT INTO ventas (
                        total, pago_con, cambio, pago_efectivo, pago_otro,
                        usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        venta_data["total"],
                        venta_data["pago_con"],
                        venta_data["cambio"],
                        venta_data["pago_efectivo"],
                        venta_data["pago_otro"],
                        venta_data["usuario"],
                        venta_data["estado"],
                        venta_data["metodo_pago"],
                        fecha,
                        venta_data["caja_id"],
                        venta_data["descuento"],
                        venta_data["recargo"],
                        venta_data["cliente_nombre"],
                    ),
                )
                new_id = cur.lastrowid

            for it in items:
                try:
                    cur.execute(
                        """
                        INSERT INTO detalles_ventas (
                            id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            new_id,
                            it.get("id"),
                            it.get("nombre") or "",
                            it.get("cant") or 0,
                            it.get("precio") or 0,
                            it.get("subtotal") or 0,
                        ),
                    )
                except Exception:
                    try:
                        cur.execute(
                            """
                            INSERT INTO detalle_ventas (
                                id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                new_id,
                                it.get("id"),
                                it.get("nombre") or "",
                                it.get("cant") or 0,
                                it.get("precio") or 0,
                                it.get("subtotal") or 0,
                            ),
                        )
                    except Exception:
                        pass
            conn.commit()
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        return False


def hidratar_faltantes(max_archivos: int = 500) -> int:
    """Reinyecta en la DB solo tickets que faltan (lazy reconcile)."""
    restored = 0
    try:
        for payload in _iter_payloads(max_archivos=max_archivos):
            vid = payload.get("id")
            if vid is None:
                continue
            try:
                if _venta_existe(vid):
                    continue
            except Exception:
                continue
            if _insertar_faltante(payload):
                restored += 1
        if restored:
            try:
                from src.logger import logger

                logger.warning(
                    "diario_ventas_externo: reinyectados %s tickets faltantes (nube local)",
                    restored,
                )
            except Exception:
                pass
    except Exception:
        pass
    return restored


def _worker_loop() -> None:
    while not _worker_stop.is_set():
        try:
            n = drenar_cola()
            if n == 0:
                _wake.wait(timeout=WORKER_IDLE_SEC)
                _wake.clear()
            else:
                # Si hubo trabajo, seguir sin dormir largo
                time.sleep(0.05)
        except Exception:
            time.sleep(WORKER_IDLE_SEC)


def start_motor_nube_local() -> None:
    """Arranca hilo worker (idempotente). El cobro solo encola; este hilo persiste."""
    global _worker_started
    cloud_ready_root()  # asegura carpeta cloud/ para futuro sync
    with _lock:
        if _worker_started:
            return
        _worker_started = True
        _worker_stop.clear()
    try:
        t = threading.Thread(target=_worker_loop, name="nube-local-diario", daemon=True)
        t.start()
        try:
            from src.logger import logger

            logger.info(
                "Nube local ventas: worker activo → %s",
                get_external_root(),
            )
        except Exception:
            pass
    except Exception:
        _worker_started = False


def schedule_hidratar_faltantes(max_archivos: int = 80) -> None:
    """Arranca worker + hydrate lazy. Nunca bloquea el hilo de UI (Admin/Jefe)."""
    global _hydrate_started
    with _lock:
        if _hydrate_started:
            return
        _hydrate_started = True

    def _run():
        try:
            # Pequeña demora: dejar que Admin pinte el dashboard primero
            time.sleep(2.0)
            start_motor_nube_local()
            drenar_cola(max_items=200)
            hidratar_faltantes(max_archivos=max_archivos)
        except Exception:
            pass

    try:
        t = threading.Thread(target=_run, name="diario-ventas-hydrate", daemon=True)
        t.start()
    except Exception:
        pass
