"""El cobro escucha el importe. No espera al monitor de admin."""


def _token(token=""):
    if token:
        return token
    try:
        from src.config import config

        config._load_config()
        return str(config.get("mp_access_token", "") or "").strip()
    except Exception:
        return ""


def _libre(pago):
    if not isinstance(pago, dict) or not pago.get("id"):
        return False
    try:
        from src.cajero.paso6_cobro.vinculo_mp.libro import asociado

        return not asociado(str(pago.get("id")))
    except Exception:
        return True


def pago_llegado(monto, token="", desde=None):
    """Pago aprobado del mismo importe, todavía no usado en un ticket."""
    try:
        importe = float(monto or 0)
    except (TypeError, ValueError):
        return None
    if importe <= 0:
        return None
    clave = _token(token)
    if not clave:
        return None
    try:
        from src.cajero.paso6_cobro.qr_en_cobro.pedido import pago_por_importe

        pago = pago_por_importe(clave, importe, desde=desde)
    except Exception:
        return None
    return pago if _libre(pago) else None


def ultimo_libre(token="", desde=None):
    """Último aprobado sin ticket, de los últimos 3 minutos, todavía libre."""
    clave = _token(token)
    if not clave:
        return None
    try:
        from src.cajero.paso6_cobro.qr_en_cobro.pedido import pagos_aprobados_recientes

        for pago in pagos_aprobados_recientes(clave, desde=desde):
            if _libre(pago):
                return pago
    except Exception:
        return None
    return None


def texto_enlazar(importe, nombre=None, destino="ticket"):
    quien = str(nombre or "").strip()
    if quien.lower() in ("", "none", "none none", "cliente", "desconocido", "transferencia recibida"):
        extra = ""
    else:
        extra = f" de {quien}"
    cosa = "abono" if destino == "abono" else "ticket"
    return (
        f"Llegó ${float(importe):,.2f}{extra}. ¿Desea enlazar al {cosa}? "
        "Presione F9 (emergencia) o espere el monto exacto."
    )
