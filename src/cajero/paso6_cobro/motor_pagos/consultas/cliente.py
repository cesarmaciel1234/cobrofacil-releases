from src.repositories.cliente_repository import ClienteRepository


def obtener_cliente(cliente_id):
    if not cliente_id:
        return None
    c = ClienteRepository.obtener_por_id(cliente_id)
    return dict(c) if c else None


def deuda_actual(cliente_id) -> float:
    c = obtener_cliente(cliente_id)
    if not c:
        return 0.0
    try:
        return float(c.get("deuda_actual") or 0)
    except Exception:
        return 0.0
