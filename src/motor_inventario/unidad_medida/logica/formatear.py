from src.motor_inventario.unidad_medida.logica.normalizar import normalizar_unidad
from src.motor_inventario.unidad_medida.rubros.catalogo import unidad_por_departamento


def _es_pesable(prod) -> bool:
    try:
        return int((prod or {}).get("es_pesable") or 0) == 1
    except Exception:
        return False


def etiqueta_unidad(prod) -> str:
    p = prod or {}
    if _es_pesable(p):
        return "kilo"
    for clave in ("unidad", "tipo_unidad", "tipo_unidad_oferta"):
        u = normalizar_unidad(p.get(clave))
        if u:
            return u
    por_depto = unidad_por_departamento(p.get("departamento") or p.get("depto") or p.get("rubro"))
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
