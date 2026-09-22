def permitir_cobro_sin_stock() -> bool:
    """True solo si la opción 'Permitir vender sin stock' está prendida."""
    from src.config import config

    return bool(config.get("opt_stock_negativo", False))


def alcanza_stock(disponible, cantidad, permitir_negativo: bool) -> bool:
    """Artículo común (disponible None) o venta con faltante permitido: pasa."""
    if permitir_negativo or disponible is None:
        return True
    try:
        return float(cantidad) <= float(disponible) + 1e-9
    except (TypeError, ValueError):
        return False
