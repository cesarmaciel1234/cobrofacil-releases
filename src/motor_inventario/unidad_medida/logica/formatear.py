from src.motor_inventario.unidad_medida.logica.normalizar import normalizar_unidad
from src.motor_inventario.unidad_medida.rubros.catalogo import unidad_por_departamento


def _as_map(prod) -> dict:
    if prod is None:
        return {}
    if isinstance(prod, dict):
        return prod
    if hasattr(prod, "keys"):
        try:
            return {k: prod[k] for k in prod.keys()}
        except Exception:
            pass
    return {}


def _campo(p: dict, clave, default=None):
    if hasattr(p, "get"):
        return p.get(clave, default)
    try:
        return p[clave]
    except Exception:
        return default


def _es_pesable(prod) -> bool:
    try:
        return int(_campo(_as_map(prod), "es_pesable") or 0) == 1
    except Exception:
        return False


def etiqueta_unidad(prod) -> str:
    p = _as_map(prod)
    if _es_pesable(p):
        return "kilo"
    for clave in ("unidad", "tipo_unidad", "tipo_unidad_oferta"):
        u = normalizar_unidad(_campo(p, clave))
        if u:
            return u
    por_depto = unidad_por_departamento(
        _campo(p, "departamento") or _campo(p, "depto") or _campo(p, "rubro")
    )
    if por_depto:
        return por_depto
    return "unidad"


def formatear_stock(prod, stock) -> str:
    try:
        val = float(stock or 0)
    except Exception:
        val = 0.0
    un = etiqueta_unidad(prod)
    if abs(val - round(val)) < 1e-6:
        return f"{int(round(val))} {un}"
    return f"{val:.3f} {un}"
