"""Rastro firmado de cancelaciones. Lo escribe la base; acá solo se lee."""


def cajas_conocidas() -> list[int]:
    from src.base_de_datos.database import db_manager

    rows = db_manager.execute_query(
        "SELECT DISTINCT caja_id FROM ventas WHERE caja_id IS NOT NULL ORDER BY caja_id"
    ) or []
    out = []
    for r in rows:
        try:
            out.append(int(r["caja_id"]))
        except (TypeError, ValueError, KeyError):
            continue
    return out or [1]


def linea_cancelacion(venta) -> str:
    if venta is None:
        return ""
    estado = str(_get(venta, "estado") or "").upper()
    if not estado.startswith("CANCELAD"):
        return ""
    quien = _get(venta, "cancelado_por") or "sin firmar"
    cuando = _get(venta, "fecha_cancel") or "—"
    perfil = _get(venta, "perfil_cancel") or "—"
    caja_acc = _get(venta, "caja_cancel")
    caja_ori = _get(venta, "caja_id")
    acc = f"caja {caja_acc}" if caja_acc not in (None, "") else "caja sin dato"
    ori = f"caja {caja_ori}" if caja_ori not in (None, "") else "caja sin dato"
    return f"Canceló {quien} ({perfil}) el {cuando} · actuó desde {acc} · ticket de {ori}"


def _get(row, key):
    try:
        if hasattr(row, "keys") and key in row.keys():
            return row[key]
        return row[key]
    except Exception:
        return None
