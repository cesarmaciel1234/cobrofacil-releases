"""Qué se pide de pollo: la caja, o en el caso extremo un corte que rinde.

La decisión la toman solo los cortes que generan ganancia: suprema y pata y muslo.
Las alitas no cuentan. Menudos y carcasa viajan adentro de la caja y tampoco se piden solos.
La merma no es stock.

El día vende de 3 a 5 cajas. Con las dos de plata en 3 o más, no se pide.
Si las dos están por debajo de 3, se piden cajas hasta que la que más tiene llegue a 5.
Si una ya cubre el día y la otra no, es el caso extremo: se piden los kilos de esa,
hasta 5 cajas de ese corte, y no se carga la otra.

Mejoras futuras del pedido: un corte pasa a decidir cuando _rol lo marca plata.
El piso y el techo son _DIA_MIN y _DIA_MAX. Cerdo y carne no usan este módulo.
"""

import math

_DIA_MIN = 3
_DIA_MAX = 5
_CORTE_MAX = 6
_DIFERENCIA_CORTE = 3


def consultar(db) -> dict:
    """Lee la composición y el stock. No escribe."""
    cortes = _composicion(db)
    merma = _merma(db)
    stocks = _stocks(db)
    costo_kg = _costo_kg(db)
    filas = []
    for nombre, kilos in cortes:
        stock = stocks.get(nombre.upper())
        if stock is None:
            stock = 0.0
        filas.append({"nombre": nombre, "kilos": kilos, "stock": stock})
    return desde(filas, merma, costo_kg)


def desde(filas, merma=0.0, costo_kg=0.0) -> dict:
    """La misma cuenta, con los stocks que ya se leyeron. No vuelve a consultar."""
    try:
        merma = float(merma or 0)
    except (TypeError, ValueError):
        merma = 0.0
    try:
        costo_kg = float(costo_kg or 0)
    except (TypeError, ValueError):
        costo_kg = 0.0
    armadas = []
    for fila in filas or []:
        nombre = str((fila or {}).get("nombre") or "").strip()
        try:
            kilos = float((fila or {}).get("kilos") or 0)
            stock = float((fila or {}).get("stock") or 0)
        except (TypeError, ValueError):
            continue
        if not nombre or kilos <= 0:
            continue
        armadas.append({
            "nombre": nombre,
            "kilos": kilos,
            "stock": stock,
            "cajas": stock / kilos,
            "rol": (fila or {}).get("rol") or _rol(nombre),
        })
    filas = armadas
    plata = [f for f in filas if f["rol"] == "plata"]
    if not plata:
        return _vacio(merma, filas, costo_kg)
    peor = min(plata, key=lambda f: (f["cajas"], f["nombre"]))
    mejor = max(plata, key=lambda f: (f["cajas"], f["nombre"]))
    enteras = math.floor(peor["cajas"] + 1e-9)
    if enteras < 0:
        enteras = 0
    utiles = sum(f["kilos"] for f in filas)
    costo_caja = round(costo_kg * utiles, 2) if costo_kg > 0 and utiles > 0 else 0.0
    corto = [f for f in plata if f["cajas"] <= _DIA_MIN]
    decision = _decidir(corto, peor, mejor, costo_kg, costo_caja, enteras)
    decision.update({
        "merma": merma,
        "filas": filas,
        "texto": _texto(decision, peor, mejor, filas, merma),
    })
    return decision


def _decidir(corto, peor, mejor, costo_kg, costo_caja, enteras) -> dict:
    base = {
        "enteras": enteras,
        "costo_kg": costo_kg,
        "costo_caja": costo_caja,
        "corte": "",
        "stock_pedido": enteras,
        "min_kg": float(_DIA_MIN),
        "max_kg": float(_DIA_MAX),
    }
    diferencia = mejor["cajas"] - peor["cajas"]
    if diferencia >= _DIFERENCIA_CORTE:
        # El bulto sumaría ambos cortes y agrandaría el desbalance. Se repone
        # únicamente el corte menor, con seis cajas como colchón de venta.
        falta = (_CORTE_MAX * peor["kilos"]) - float(peor["stock"] or 0)
        if falta > 0:
            base.update({
                "modo": "corte",
                "pedir": round(falta, 2),
                "unidad": "kg",
                "nombre": peor["nombre"],
                "corte": peor["nombre"],
                "stock_pedido": peor["stock"],
                "min_kg": round(_DIA_MIN * peor["kilos"], 2),
                "max_kg": round(_CORTE_MAX * peor["kilos"], 2),
                "costo": costo_kg,
            })
            return base
    if not corto:
        base.update({
            "modo": "nada",
            "pedir": 0,
            "unidad": "caja",
            "nombre": "Pollo entero",
            "costo": costo_caja,
        })
        return base
    if float(peor["stock"] or 0) <= 0:
        return _refuerzo(base, peor, mejor, costo_caja)
    pedir = int(math.ceil(_DIA_MAX - mejor["cajas"]))
    if pedir < 1:
        pedir = 1
    parejo = (mejor["cajas"] - peor["cajas"]) <= 1
    base.update({
        "modo": "caja",
        "pedir": pedir,
        "unidad": "caja",
        "nombre": "Pollo entero" if parejo else "Caja de pollo",
        "costo": costo_caja,
    })
    return base


def _refuerzo(base, peor, mejor, costo_caja) -> dict:
    """El corte vacío llega a 6. Las cajas paran cuando el que todavía tiene stock llega a 6."""
    pedir = int(math.ceil(_CORTE_MAX - float(mejor["cajas"])))
    if pedir < 0:
        pedir = 0
    queda = float(peor["cajas"]) + pedir
    falta = _CORTE_MAX - queda
    extra = round(falta * peor["kilos"], 2) if falta > 0 else 0.0
    base.update({
        "modo": "refuerzo",
        "pedir": pedir,
        "unidad": "caja",
        "nombre": "Caja de pollo",
        "costo": costo_caja,
        "corte": peor["nombre"],
        "extra_kg": extra,
        "extra_nombre": peor["nombre"],
        "extra_stock": peor["stock"],
        "extra_min": round(_DIA_MIN * peor["kilos"], 2),
        "extra_max": round(_CORTE_MAX * peor["kilos"], 2),
        "max_kg": float(_CORTE_MAX),
    })
    return base


def _rol(nombre: str) -> str:
    texto = str(nombre or "").upper()
    if "ALITA" in texto:
        return "no_cuenta"
    if "SUPREMA" in texto or "PATA" in texto:
        return "plata"
    return "caja"


def _composicion(db) -> list:
    try:
        from src.proveedor_global.frontend.formula.motores.orden import cortes
        pares = cortes(db, "Pollo") or []
    except Exception:
        pares = []
    if not pares:
        from src.jefe.promedios.pollo.motor_pollo import MotorPollo
        pares = list(MotorPollo.get_cortes())
    salida = []
    for nombre, kilos in pares:
        try:
            kilos = float(kilos or 0)
        except (TypeError, ValueError):
            continue
        nombre = str(nombre or "").strip()
        if nombre and kilos > 0:
            salida.append((nombre, kilos))
    return salida


def _stocks(db) -> dict:
    try:
        from src.proveedor_global.frontend.formula.motores.carne_stock import consultar as leer
        dato = leer(db, "Pollo") or {}
    except Exception:
        return {}
    salida = {}
    for fila in dato.get("cortes") or []:
        nombre = str(fila.get("nombre") or "").strip().upper()
        try:
            numero = float(fila.get("stock") or 0)
        except (TypeError, ValueError):
            numero = 0.0
        if nombre:
            salida[nombre] = numero
    return salida


def _merma(db) -> float:
    try:
        from src.proveedor_global.frontend.formula.motores.orden import merma_de
        return float(merma_de(db, "Pollo") or 0)
    except Exception:
        return 0.0


def _costo_kg(db) -> float:
    try:
        from src.proveedor_global.frontend.formula.motores.orden import costo_de
        return float(costo_de(db, "Pollo") or 0)
    except Exception:
        return 0.0


def _texto(decision, peor, mejor, filas, merma) -> str:
    alitas = next((f for f in filas if f["rol"] == "no_cuenta"), None)
    nota_alitas = " Las alitas no cuentan: no generan ganancia y no se piden."
    if alitas is None:
        nota_alitas = ""
    modo = decision["modo"]
    if modo == "nada":
        frase = (
            f"Suprema y pata cubren el día "
            f"({peor['nombre']} {peor['cajas']:.0f} cajas, {mejor['nombre']} {mejor['cajas']:.0f})."
            f"{nota_alitas}"
        )
    elif modo == "corte":
        frase = (
            f"{decision['corte']} quedó {_DIFERENCIA_CORTE:g} o más cajas por debajo de "
            f"{mejor['nombre']}. No se pide la caja, porque agrandaría esa diferencia. "
            f"Se piden {decision['pedir']:g} kg de {decision['corte']} para completar "
            f"{_CORTE_MAX} cajas.{nota_alitas}"
        )
    elif modo == "refuerzo":
        extra = float(decision.get("extra_kg") or 0)
        frase = (
            f"{mejor['nombre']} tiene {mejor['cajas']:.0f} cajas y {peor['nombre']} no queda. "
            f"Se piden {decision['pedir']} cajas de pollo"
        )
        if extra > 0:
            frase += (
                f" y {extra:g} kg de {decision['extra_nombre']} "
                f"para llegar a {_CORTE_MAX}."
            )
        else:
            frase += f" para llegar a {_CORTE_MAX}."
        frase += nota_alitas
    else:
        frase = (
            f"Suprema y pata están por debajo de {_DIA_MIN} cajas. "
            f"Se piden {decision['pedir']} cajas de {decision['nombre']} "
            f"para llegar a {_DIA_MAX}.{nota_alitas}"
        )
    if merma > 0:
        frase += f" La merma es {merma:g} kg y no entra."
    return frase


def _vacio(merma, filas, costo_kg) -> dict:
    return {
        "modo": "nada",
        "enteras": 0,
        "pedir": 0,
        "unidad": "caja",
        "nombre": "Pollo entero",
        "corte": "",
        "stock_pedido": 0,
        "min_kg": float(_DIA_MIN),
        "max_kg": float(_DIA_MAX),
        "costo_kg": costo_kg,
        "costo_caja": 0.0,
        "costo": 0.0,
        "merma": merma,
        "filas": filas,
        "texto": "Faltan suprema y pata en la composición. Sin esos cortes no se arma el pedido.",
    }
