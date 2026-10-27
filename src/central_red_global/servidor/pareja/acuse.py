"""El ticket sigue en la cola hasta que la reserva lo tiene en el espejo."""

from __future__ import annotations

import json
import logging
import socket

logger = logging.getLogger("oficio_servidor")

_PUERTO = 37021


def tiene_en_espejo(request_id: str) -> bool:
    rid = str(request_id or "").strip()
    if not rid:
        return False
    try:
        import sqlite3
        from pathlib import Path

        from src.jefe.nodo_portable.espejo.copia import existe, ruta

        if not existe():
            return False
        conn = sqlite3.connect(Path(ruta()).as_uri() + "?mode=ro", uri=True, timeout=5)
        try:
            fila = conn.execute(
                "SELECT 1 FROM ventas WHERE request_id = ? LIMIT 1",
                (rid,),
            ).fetchone()
        finally:
            conn.close()
        return bool(fila)
    except Exception:
        return False


def debe_esperar(request_id: str) -> bool:
    """La titular ya lo guardó. Se suelta cuando esta PC es la tienda, o cuando el espejo de la reserva lo tiene."""
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        if es_pc_maestra_local():
            return False
    except Exception:
        pass
    try:
        from src.central_red_global.servidor.pareja.reserva import soy

        if soy():
            return not tiene_en_espejo(request_id)
    except Exception:
        pass
    return True


def pedir(ids: list[str]) -> None:
    """Pregunta a la reserva cuáles de estos tickets ya están en su espejo."""
    limpios = [str(i).strip() for i in ids if str(i or "").strip()][:40]
    if not limpios:
        return
    payload = {
        "origen": f"{socket.gethostname()}|esclava|servidor",
        "tipo": "CONFIRMAR",
        "datos": {"ids": limpios},
        "ts": 0,
    }
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(json.dumps(payload, ensure_ascii=False).encode("utf-8"), ("255.255.255.255", _PUERTO))
        sock.close()
    except Exception as e:
        logger.debug("pareja  no se pudo pedir acuse: %s", e)


def responder(destino: tuple, ids: list) -> None:
    """La reserva contesta solo los que ya están en su copia."""
    try:
        from src.central_red_global.servidor.pareja.reserva import soy

        if not soy():
            return
    except Exception:
        return
    listos = [str(i) for i in ids if tiene_en_espejo(str(i))]
    if not listos or not destino:
        return
    payload = {
        "origen": f"{socket.gethostname()}|reserva|servidor",
        "tipo": "ESPEJO_LISTO",
        "datos": {"ids": listos},
    }
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(payload, ensure_ascii=False).encode("utf-8"), destino)
        sock.close()
    except Exception as e:
        logger.debug("pareja  no se pudo acusar: %s", e)


def soltar_propios() -> None:
    """Esta PC es la reserva: suelta de su cola lo que ya quedó en su espejo."""
    try:
        from src.central_red_global.servidor.pareja.reserva import soy

        if not soy():
            return
        from src.base_de_datos.offline_sync import offline_sync_manager

        ids = []
        for registro in offline_sync_manager._cola_en_titular():
            rid = str((registro.get("venta_data") or {}).get("request_id") or "")
            if rid and tiene_en_espejo(rid):
                ids.append(rid)
        if ids:
            offline_sync_manager.soltar_confirmados(ids)
    except Exception as e:
        logger.warning("pareja  no se pudo soltar la cola propia: %s", e)
