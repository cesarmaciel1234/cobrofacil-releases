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
    """Id de transferencia, QR, Point o F9 MANUAL, si quedó en la descripción."""
    ficha = _ficha(fila)
    dentro = _parentesis(ficha.get("descripcion"))
    if ":" not in dentro:
        return ""
    return dentro.split(":", 1)[1].strip()


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
    return {
        "fecha": str(ficha.get("fecha") or ""),
        "nombre": str(ficha.get("nombre") or "").strip(),
        "dni": str(ficha.get("dni") or "").strip(),
        "monto": monto,
        "medio": medio_de(ficha),
        "detalle": detalle_de(ficha),
        "perfil": str(ficha.get("perfil") or "").strip(),
        "quien": str(ficha.get("registrado_por") or "").strip(),
        "saldo": saldo,
    }
