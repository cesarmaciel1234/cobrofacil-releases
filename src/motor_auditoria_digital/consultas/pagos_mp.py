"""Pregunta al historial CSV de Mercado Pago. No baja la API."""


def listar():
    try:
        from src.admin.mercadopago.historial.archivo import leer

        return list((leer() or {}).get("pagos") or [])
    except Exception:
        return []
