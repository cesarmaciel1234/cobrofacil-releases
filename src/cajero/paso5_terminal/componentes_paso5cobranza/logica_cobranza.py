from __future__ import annotations
import re
from datetime import datetime
from src.base_de_datos.database import db_manager
from src.repositories.cliente_repository import ClienteRepository

def _parse_fecha(texto: str) -> str | None:
    t = texto.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(t, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

def _parse_monto(texto: str) -> float | None:
    t = texto.strip().replace("$", "").replace(" ", "")
    if not t:
        return None
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        parts = t.split(",")
        t = parts[0].replace(".", "") + "." + parts[1] if len(parts) == 2 else t.replace(",", ".")
    else:
        t = t.replace(".", "") if t.count(".") > 1 else t
    try:
        val = float(t)
        return val if val > 0 else None
    except ValueError:
        return None

def parse_consulta_cobranza(texto: str) -> dict:
    raw = (texto or "").strip()
    if not raw:
        return {"tipo": "todos", "valor": "", "etiqueta": "Todos los deudores"}

    dni = ClienteRepository.normalizar_dni(raw)
    digits_only = re.sub(r"\D", "", raw)
    if dni and len(digits_only) >= 7 and len(digits_only) / max(len(raw.replace(" ", "")), 1) >= 0.85:
        return {"tipo": "dni", "valor": dni, "etiqueta": f"DNI {dni}"}

    fecha = _parse_fecha(raw)
    if fecha:
        return {"tipo": "fecha", "valor": fecha, "etiqueta": f"Fecha {fecha}"}

    monto = _parse_monto(raw)
    if monto is not None and re.match(r"^[\d$.,\s]+$", raw):
        return {"tipo": "monto", "valor": monto, "etiqueta": f"Monto ${monto:,.2f}"}

    return {"tipo": "nombre", "valor": raw, "etiqueta": f"Nombre «{raw}»"}

def buscar_deudores(consulta: str) -> list:
    p = parse_consulta_cobranza(consulta)
    base = """
        SELECT c.id, c.nombre, c.dni, c.deuda_actual, c.limite_credito, c.tipo_cliente,
               (SELECT MAX(cc.fecha) FROM cuenta_corriente cc
                WHERE cc.cliente_id = c.id AND cc.tipo = 'CARGO') AS ultimo_cargo
        FROM clientes c
        WHERE c.deuda_actual > 0.01
    """
    params: list = []

    if p["tipo"] == "dni":
        v = p["valor"]
        base += " AND (c.dni = ? OR c.dni LIKE ? OR c.nombre LIKE ?)"
        params.extend([v, f"%{v}%", f"%{v}%"])
    elif p["tipo"] == "nombre":
        v = p["valor"]
        base += " AND (c.nombre LIKE ? OR COALESCE(c.dni, '') LIKE ?)"
        params.extend([f"%{v}%", f"%{v}%"])
    elif p["tipo"] == "monto":
        m = float(p["valor"])
        base += """
            AND (
                ABS(c.deuda_actual - ?) < 0.05
                OR EXISTS (
                    SELECT 1 FROM cuenta_corriente cc
                    WHERE cc.cliente_id = c.id AND ABS(cc.monto - ?) < 0.05
                )
            )
        """
        params.extend([m, m])
    elif p["tipo"] == "fecha":
        base += """
            AND EXISTS (
                SELECT 1 FROM cuenta_corriente cc
                WHERE cc.cliente_id = c.id AND DATE(cc.fecha) = ?
            )
        """
        params.append(p["valor"])

    base += " ORDER BY c.deuda_actual DESC, c.nombre ASC LIMIT 50"
    rows = db_manager.execute_query(base, tuple(params)) or []
    for r in rows:
        r["_parse"] = p
    return rows
