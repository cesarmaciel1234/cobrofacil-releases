"""Pregunta a cada fórmula por separado. Si una falla, las otras responden."""

from src.proveedor_global.frontend.formula.motores.huevo import maple30, maple15, maple10, maple6

_MODULOS = {
    30: maple30,
    15: maple15,
    10: maple10,
    6: maple6,
}


def revisar() -> list:
    """Cada una tiene que rendir 360 huevos. No se suman entre sí."""
    salida = []
    for mod in (maple30, maple15, maple10, maple6):
        salida.append(_una(mod, 1))
    huevos = [fila["huevos_cajon"] for fila in salida if fila.get("ok")]
    mismo = len(huevos) == 4 and len(set(huevos)) == 1 and huevos[0] == 360
    for fila in salida:
        fila["mismo_cajon"] = mismo
    return salida


def pedir(cajones, cortes) -> list:
    """Una fórmula por llamada. El error de una no borra a las demás."""
    salida = []
    for nombre, huevos in cortes or []:
        try:
            huevos_n = int(round(float(huevos)))
        except (TypeError, ValueError):
            salida.append({"nombre": nombre, "ok": False, "huevos": 0, "salen": 0, "entran": 0})
            continue
        mod = _MODULOS.get(huevos_n)
        if mod is None:
            salida.append(_suelta(nombre, huevos_n, cajones))
            continue
        fila = _una(mod, cajones)
        fila["nombre"] = nombre or mod.NOMBRE
        salida.append(fila)
    return salida


def _una(mod, cajones) -> dict:
    try:
        salen = mod.salen()
        return {
            "nombre": mod.NOMBRE,
            "huevos": mod.HUEVOS,
            "salen": salen,
            "entran": mod.stock(cajones),
            "huevos_cajon": salen * mod.HUEVOS,
            "ok": bool(mod.cuadra()),
        }
    except Exception:
        return {
            "nombre": getattr(mod, "NOMBRE", ""),
            "huevos": getattr(mod, "HUEVOS", 0),
            "salen": 0,
            "entran": 0,
            "huevos_cajon": 0,
            "ok": False,
        }


def _suelta(nombre, huevos, cajones) -> dict:
    try:
        from src.proveedor_global.frontend.formula.motores.carga import stock_de
        salen = stock_de(1, huevos)
        return {
            "nombre": nombre,
            "huevos": huevos,
            "salen": salen,
            "entran": stock_de(cajones, huevos),
            "huevos_cajon": salen * huevos,
            "ok": abs(salen * huevos - 360) < 1e-6,
        }
    except Exception:
        return {"nombre": nombre, "huevos": huevos, "salen": 0, "entran": 0, "huevos_cajon": 0, "ok": False}
