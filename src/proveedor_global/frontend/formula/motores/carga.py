"""Cuánto sale de 1 cajón y qué stock le toca a cada porción. No vende.

El stock no lo escribe esta cuenta. Lo manda motores/inventario.py."""

MAPLES_POR_CAJON = 12
HUEVOS_POR_MAPLE = 30
HUEVOS_POR_CAJON = MAPLES_POR_CAJON * HUEVOS_POR_MAPLE


def cerrar(valor) -> float:
    """Saca el decimal que no cierra. 11.999999 queda 12. 11.8 queda 11.8."""
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        return 0.0
    cercano = round(numero, 4)
    if abs(cercano - round(cercano)) < 1e-6:
        return float(int(round(cercano)))
    return cercano


def huevos_en(cajones) -> int:
    """Los huevos que hay en esos cajones: cajón × 12 maples × 30 huevos."""
    try:
        cajones = float(cajones or 0)
    except (TypeError, ValueError):
        return 0
    if cajones <= 0:
        return 0
    return int(round(cajones * HUEVOS_POR_CAJON))


def maples_en(cajones) -> float:
    return cerrar(huevos_en(cajones) / HUEVOS_POR_MAPLE)


def stock_de(cajones, huevos_porcion) -> float:
    """Cuántas porciones salen de esos cajones. Entero cuando la división cierra."""
    try:
        huevos_porcion = int(round(float(huevos_porcion)))
    except (TypeError, ValueError):
        return 0.0
    if huevos_porcion <= 0:
        return 0.0
    return cerrar(huevos_en(cajones) / huevos_porcion)


def unidades(cajones, huevos_porcion) -> int:
    """Unidades enteras. Si el cajón queda corto, el número sigue en -1, -2, -3."""
    try:
        cajones = float(cajones or 0)
        porcion = int(round(float(huevos_porcion)))
    except (TypeError, ValueError):
        return 0
    if porcion <= 0:
        return 0
    huevos = int(round(cajones * HUEVOS_POR_CAJON))
    return huevos // porcion


def texto_maples(huevos) -> str:
    """30 huevos = 1 maple. 15 = 1/2. 10 = 1/3. 6 = 1/5."""
    try:
        huevos = int(round(float(huevos)))
    except (TypeError, ValueError):
        return "0"
    if huevos <= 0:
        return "0"
    from math import gcd
    divisor = gcd(huevos, HUEVOS_POR_MAPLE)
    numerador = huevos // divisor
    denominador = HUEVOS_POR_MAPLE // divisor
    if denominador == 1:
        return str(numerador)
    return f"{numerador}/{denominador}"


def texto_total_maples(huevos_totales) -> str:
    """350 huevos = 11 2/3 maples. 354 = 11 4/5. 360 = 12."""
    try:
        total = int(round(float(huevos_totales)))
    except (TypeError, ValueError):
        return "0"
    if total <= 0:
        return "0"
    enteros = total // HUEVOS_POR_MAPLE
    resto = total % HUEVOS_POR_MAPLE
    if resto == 0:
        return str(enteros)
    parte = texto_maples(resto)
    if enteros == 0:
        return parte
    return f"{enteros} {parte}"


def texto_se_va(huevos) -> str:
    try:
        huevos = int(round(float(huevos)))
    except (TypeError, ValueError):
        return "0"
    if huevos <= 0:
        return "0"
    if huevos % HUEVOS_POR_MAPLE == 0:
        maples = huevos // HUEVOS_POR_MAPLE
        return "1 maple" if maples == 1 else f"{maples} maples"
    return f"{huevos} huevos"


def de_un_cajon(cortes) -> list:
    """De cada corte, cuántas unidades salen de un cajón. No toca la base."""
    salida = []
    for nombre, huevos in cortes or []:
        try:
            huevos = float(huevos)
        except (TypeError, ValueError):
            continue
        if huevos <= 0:
            continue
        salida.append({
            "nombre": str(nombre),
            "huevos": cerrar(huevos),
            "salen": stock_de(1, huevos),
            "piezas": huevos / HUEVOS_POR_MAPLE,
            "maples": texto_maples(huevos),
        })
    return salida


def stock_cajon(db) -> dict:
    """El cajón de huevo, si existe. Si no, la cuenta se muestra sobre 1 cajón."""
    vacio = {"hallado": False, "id": "", "nombre": "Cajón de huevo", "stock": 1.0}
    try:
        filas = db.execute_query(
            "SELECT id, nombre, stock FROM productos "
            "WHERE UPPER(nombre) LIKE '%CAJ%' AND UPPER(nombre) LIKE '%HUEV%' LIMIT 1"
        ) or []
    except Exception:
        return vacio
    if not filas:
        return vacio
    fila = filas[0]
    if not isinstance(fila, dict):
        try:
            fila = {"id": fila[0], "nombre": fila[1], "stock": fila[2]}
        except Exception:
            return vacio
    try:
        stock = float(fila.get("stock") or 0)
    except (TypeError, ValueError):
        stock = 0.0
    return {
        "hallado": True,
        "id": str(fila.get("id") or ""),
        "nombre": fila.get("nombre") or "Cajón de huevo",
        "stock": stock,
    }


def stock_porciones(rendimiento, cajones: float) -> list:
    filas = []
    for item in rendimiento or []:
        filas.append({
            "nombre": item["nombre"],
            "huevos": item["huevos"],
            "salen": item["salen"],
            "piezas": item["piezas"],
            "maples": item.get("maples") or texto_maples(item["huevos"]),
            "stock": stock_de(cajones, item["huevos"]),
        })
    return filas


def publicar_formula(db, rendimiento, base_nombre: str) -> int:
    """Deja la fórmula lista para la venta. Si falla, no borra lo anterior."""
    if not rendimiento:
        return 0
    try:
        from src.jefe.promedios.formula.motor import guardar
        lineas = [{"nombre": i["nombre"], "piezas": i["piezas"]} for i in rendimiento]
        return int(guardar(db, base_nombre, MAPLES_POR_CAJON, lineas, "producto") or 0)
    except Exception:
        return 0


def aplicar(db, porciones, base_id: str = "") -> int:
    """Pide al motor de inventario que lea el cajón y mande el stock.

    Sin el id del cajón no escribe: el número que ya trae la lista puede ser viejo.
    """
    if not str(base_id or "").strip():
        return 0
    try:
        from src.proveedor_global.frontend.formula.motores.inventario import enviar
        lineas = [
            {"nombre": item.get("nombre"), "salen": item.get("salen")}
            for item in (porciones or [])
        ]
        return int(enviar(db, base_id, lineas).get("enviados") or 0)
    except Exception:
        return 0
