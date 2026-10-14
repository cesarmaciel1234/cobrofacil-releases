"""Una fila de abono para la planilla de admin."""


def _ficha(fila):
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return fila
    try:
        return dict(fila)
    except Exception:
        return {}


def fecha_corta(fecha):
    f = str(fecha or "")
    if len(f) >= 16 and f[4] == "-" and f[7] == "-":
        return f"{f[8:10]}/{f[5:7]}/{f[:4]} {f[11:16]}"
    return f


def titulo_persona(texto):
    t = " ".join(str(texto or "").split())
    if t.isupper() and len(t) > 1:
        return t.title()
    return t


def _parentesis(descripcion):
    desc = str(descripcion or "").strip()
    if desc.endswith(")") and "(" in desc:
        return desc.rsplit("(", 1)[-1].rstrip(")").strip()
    return ""


def medio_de(fila):
    """El medio guardado al cobrar. Si la columna vino vacía, lo lee del paréntesis."""
    ficha = _ficha(fila)
    medio = str(ficha.get("medio_pago") or "").strip()
    if medio:
        return medio.split(":", 1)[0].strip() or medio
    dentro = _parentesis(ficha.get("descripcion"))
    if not dentro:
        return ""
    return dentro.split(":", 1)[0].strip() or dentro


def detalle_de(fila):
    """Id de Mercado Pago o F9 MANUAL. Efectivo no tiene id digital."""
    ficha = _ficha(fila)
    dentro = _parentesis(ficha.get("descripcion"))
    if ":" not in dentro:
        return ""
    bruto = dentro.split(":", 1)[1].strip()
    try:
        from src.motor_auditoria_digital.consultas.ids import id_pago

        f9 = "F9" in bruto.upper()
        return id_pago(bruto, f9=f9) or bruto
    except Exception:
        return bruto


def armar(fila):
    ficha = _ficha(fila)
    try:
        monto = float(ficha.get("monto") or 0)
    except (TypeError, ValueError):
        monto = 0.0
    try:
        saldo = float(ficha.get("saldo_resultante") or 0)
    except (TypeError, ValueError):
        saldo = 0.0
    try:
        from src.motor_auditoria_digital.consultas.ids import ticket_cobro

        cobro = ticket_cobro(ficha.get("id"))
    except Exception:
        cobro = f"COB-{ficha.get('id')}" if ficha.get("id") else ""
    medio = medio_de(ficha)
    detalle = detalle_de(ficha)
    if not detalle and medio.lower() == "efectivo":
        detalle = "Caja"
    perfil = titulo_persona(ficha.get("perfil"))
    quien = titulo_persona(ficha.get("registrado_por"))
    if quien.lower() == perfil.lower():
        quien = quien or perfil
    fecha_raw = str(ficha.get("fecha") or "")
    return {
        "id": str(ficha.get("id") or "").strip(),
        "ticket_cobro": cobro,
        "fecha": fecha_corta(fecha_raw) or fecha_raw,
        "fecha_raw": fecha_raw,
        "nombre": str(ficha.get("nombre") or "").strip(),
        "dni": str(ficha.get("dni") or "").strip(),
        "monto": monto,
        "medio": medio,
        "detalle": detalle,
        "perfil": perfil,
        "quien": quien,
        "saldo": saldo,
        "digital": medio.lower() in ("qr", "transferencia", "tarjeta", "mixto"),
    }
