_CLAVE = "opt_stock_negativo"
# Si la caja no tiene la clave, se puede vender en negativo (mismo valor que config.DEFAULT_CONFIG).
_PERMITE_SI_FALTA = True


def permitir_cobro_sin_stock() -> bool:
    """True si «No vender sin stock» está apagado y el stock puede seguir en negativo."""
    from src.config import config

    return bool(config.get(_CLAVE, _PERMITE_SI_FALTA))


def bloquear_venta_sin_stock() -> bool:
    """Estado del check «No vender sin stock». El valor guardado es el inverso."""
    return not permitir_cobro_sin_stock()


def guardar_bloqueo_venta_sin_stock(bloquear: bool) -> None:
    """Marcado = no se cobra sin existencia. Lo guarda invertido en opt_stock_negativo."""
    from src.config import config

    config.set(_CLAVE, not bool(bloquear))


def alcanza_stock(disponible, cantidad, permitir_negativo: bool) -> bool:
    """Artículo común (disponible None) o venta con faltante permitido: pasa."""
    if permitir_negativo or disponible is None:
        return True
    try:
        return float(cantidad) <= float(disponible) + 1e-9
    except (TypeError, ValueError):
        return False
