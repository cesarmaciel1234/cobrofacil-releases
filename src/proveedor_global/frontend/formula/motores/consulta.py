"""La puerta de la fórmula. Recepción pregunta acá y no hace la cuenta.

Promedios dice cuántas fórmulas hay. Esta responde el stock que cada una
representa en un cajón. La venta, si saca una, deja el cajón y rearma el resto.
"""

import re


def cuantas(db, tipo: str = "Huevo") -> list:
    """Le pregunta a Promedios. Si todavía no publicó, usa las cuatro de huevo."""
    try:
        from src.proveedor_global.frontend.formula.motores.lectura import leer
        pares = leer(db, tipo) or []
    except Exception:
        pares = []
    if pares:
        return [(str(n), float(h)) for n, h in pares]
    if tipo == "Huevo":
        return [
            ("Maple 30 huevos", 30),
            ("Maple 15 huevos", 15),
            ("Maple 10 huevos", 10),
            ("Maple 6 huevos", 6),
        ]
    return []


def representa(db, bultos: float = 1, tipo: str = "Huevo") -> dict:
    """1 cajón: cuánto stock le toca a cada fórmula, en su producto."""
    try:
        bultos = float(bultos or 0)
    except (TypeError, ValueError):
        bultos = 0.0
    if bultos < 0:
        bultos = 0.0
    from src.proveedor_global.frontend.formula.motores.carga import de_un_cajon
    from src.proveedor_global.frontend.formula.motores.huevo.cuadro import pedir

    cortes = cuantas(db, tipo)
    rendimiento = de_un_cajon(cortes)
    cuentas = pedir(bultos, cortes)
    por_huevos = {}
    for cuenta in cuentas:
        try:
            por_huevos[int(round(float(cuenta.get("huevos") or 0)))] = cuenta
        except (TypeError, ValueError):
            continue
    productos = _productos(db, tipo)
    lineas = []
    for item in rendimiento:
        huevos = item["huevos"]
        cuenta = por_huevos.get(int(round(float(huevos)))) or {}
        if cuenta.get("ok") is False and not cuenta.get("salen"):
            continue
        prod = _emparejar(productos, huevos, item["nombre"])
        entran = cuenta.get("entran")
        if entran is None:
            entran = 0
        actual = float(prod.get("stock") or 0) if prod else 0
        lineas.append({
            "formula": item["nombre"],
            "huevos": huevos,
            "maples": item.get("maples") or "",
            "salen": cuenta.get("salen") if cuenta.get("salen") is not None else item["salen"],
            "entran": entran,
            "stock_actual": actual,
            "quedaria": actual + entran,
            "producto": prod,
            "ok": bool(cuenta.get("ok", True)),
        })
    lineas.sort(key=lambda f: (-float(f["huevos"]), f["formula"]))
    return {"tipo": tipo, "bultos": bultos, "lineas": lineas}


def _productos(db, tipo: str) -> list:
    try:
        filas = db.execute_query(
            "SELECT id, codigo, nombre, stock, costo, departamento FROM productos "
            "WHERE UPPER(nombre) LIKE ?",
            (f"%{tipo[:4].upper()}%",),
        ) or []
    except Exception:
        return []
    salida = []
    for fila in filas:
        datos = _dict(fila)
        if not datos:
            continue
        salida.append({
            "id": str(datos.get("id") or ""),
            "codigo": str(datos.get("codigo") or datos.get("id") or ""),
            "nombre": datos.get("nombre") or "",
            "stock": float(datos.get("stock") or 0),
            "costo": float(datos.get("costo") or 0),
            "departamento": datos.get("departamento") or "",
        })
    return salida


def _emparejar(productos, huevos, nombre_formula):
    """huevo x 6 un es la de 6. huevo maple es la de 30."""
    buscado = int(round(float(huevos)))
    exacto = None
    maple = None
    for prod in productos:
        numero = _numero(prod.get("nombre") or "")
        if numero == buscado:
            exacto = prod
            break
        if buscado == 30 and numero is None and "MAPLE" in str(prod.get("nombre") or "").upper():
            maple = prod
    if exacto:
        return exacto
    if maple:
        return maple
    for prod in productos:
        if str(prod.get("nombre") or "").strip().upper() == str(nombre_formula).strip().upper():
            return prod
    return None


def _numero(nombre: str):
    texto = nombre or ""
    hallado = re.search(r"x\s*(\d+)", texto, re.IGNORECASE)
    if hallado:
        return int(hallado.group(1))
    hallado = re.search(r"(\d+)\s*un", texto, re.IGNORECASE)
    if hallado:
        return int(hallado.group(1))
    return None


def modulos() -> list:
    """Lo que se carga por bulto. Media res, Mocho y Pecho son recetas distintas."""
    return ["Huevo", "Media res", "Mocho", "Pecho", "Cerdo", "Pollo", "Congelado"]


_TIPO = {
    "huevo": "Huevo",
    "carne": "Media Res",
    "media res": "Media Res",
    "mocho": "Mocho",
    "pecho": "Pecho",
    "cerdo": "Cerdo",
    "pollo": "Pollo",
    "congelado": "Congelado",
}


def _tipo(modulo: str) -> str:
    return _TIPO.get((modulo or "").strip().lower(), (modulo or "").strip())


def _receta(tipo: str) -> list:
    """Los cortes de esa carpeta. No junta media res con mocho ni con pecho."""
    try:
        if tipo in ("Media Res", "Mocho", "Pecho"):
            from src.jefe.promedios.carne.motor_carne import MotorCarne
            return list(MotorCarne.get_cortes(tipo))
        if tipo == "Cerdo":
            from src.jefe.promedios.cerdo.motor_cerdo import MotorCerdo
            return list(MotorCerdo.get_cortes())
        if tipo == "Pollo":
            from src.jefe.promedios.pollo.motor_pollo import MotorPollo
            return list(MotorPollo.get_cortes())
    except Exception:
        return []
    return []


def al_elegir(db, modulo: str, bultos: float, precio: float = 0) -> dict:
    """La recepción elige un módulo y manda el precio del bulto. La fórmula devuelve el costo."""
    nombre = (modulo or "").strip()
    try:
        precio = float(precio or 0)
    except (TypeError, ValueError):
        precio = 0.0
    if nombre == "Huevo":
        from src.proveedor_global.frontend.formula.motores.costo import _parte

        vista = representa(db, bultos, "Huevo")
        productos = []
        for linea in vista.get("lineas") or []:
            prod = linea.get("producto") or {}
            if not prod.get("id"):
                continue
            productos.append({
                "id": prod["id"],
                "codigo": prod.get("codigo") or prod["id"],
                "nombre": prod.get("nombre") or linea.get("formula") or "",
                "departamento": prod.get("departamento") or "",
                "stock_actual": linea.get("stock_actual") or 0,
                "cantidad": linea.get("entran") or 0,
                "costo": _parte(precio, linea.get("salen")),
            })
        partes = []
        for linea in vista.get("lineas") or []:
            prod = linea.get("producto") or {}
            rotulo = prod.get("nombre") or linea.get("formula")
            partes.append(f"{rotulo} {_parte(precio, linea.get('salen')):g}")
        from src.proveedor_global.backend.moneda import texto
        nota = ""
        if bultos:
            nota = (
                f"Huevo · precio del cajón {texto(precio)} · total {texto(precio * bultos)}. "
                + " · ".join(partes)
            )
        return {
            "origen": "consulta",
            "productos": productos,
            "nota": nota,
            "precio": precio,
            "monto": round(precio * bultos, 2),
        }
    arma = _desde_promedio(db, nombre, bultos)
    productos = arma.get("productos") or []
    utiles = sum(float(p.get("kilos") or 0) for p in productos)
    total = round(precio * bultos, 2)
    costo_kg = round(precio / utiles, 2) if precio > 0 and utiles > 0 else 0.0
    acumulado = 0.0
    for indice, prod in enumerate(productos):
        kilos = float(prod.get("kilos") or 0)
        prod["cantidad"] = round(kilos * bultos, 4)
        prod["costo"] = costo_kg
        if costo_kg > 0 and kilos > 0 and indice < len(productos) - 1:
            parte = round(total * (kilos / utiles), 2)
            acumulado += parte
            prod["subtotal"] = parte
        elif costo_kg > 0 and kilos > 0:
            prod["subtotal"] = round(total - acumulado, 2)
        else:
            prod["subtotal"] = 0.0
    arma["productos"] = _colgar(db, nombre, productos, bultos, costo_kg, utiles)
    try:
        from src.proveedor_global.frontend.formula.motores.orden import merma_de
        merma = float(merma_de(db, nombre) or 0)
    except Exception:
        merma = 0.0
    arma["precio"] = precio
    arma["bultos"] = bultos
    arma["modulo"] = nombre
    arma["monto"] = total
    arma["merma"] = merma
    arma["kilos_receta"] = utiles
    if bultos > 0 and precio > 0:
        from src.proveedor_global.backend.moneda import texto
        partes = [
            f"{prod.get('nombre')} {_txt_num(prod.get('cantidad'))} kg"
            for prod in productos
        ]
        arma["nota"] = (
            f"{nombre} · {_txt_num(bultos)} bultos × {texto(precio)} = {texto(total)}. "
            f"El cajón se divide por {_txt_num(utiles)} kg, sin la merma. "
            + ", ".join(partes)
            + "."
        )
    return arma


def _txt_num(valor) -> str:
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        return "0"
    if abs(numero - round(numero)) < 1e-4:
        return str(int(round(numero)))
    return f"{numero:.2f}".rstrip("0").rstrip(".")


def _desde_promedio(db, modulo: str, bultos: float) -> dict:
    """Una receta. Pecho no arrastra el mocho ni la media res."""
    from src.proveedor_global.frontend.formula.motores.lectura import leer

    try:
        bultos = float(bultos or 0)
    except (TypeError, ValueError):
        bultos = 0.0
    tipo = _tipo(modulo)
    try:
        from src.proveedor_global.frontend.formula.motores.orden import cortes, codigos
        lista = cortes(db, tipo) or []
        mapa = codigos(db, tipo) or {}
    except Exception:
        lista = []
        mapa = {}
    if not lista:
        lista = leer(db, tipo) or []
    if not lista:
        lista = _receta(tipo)
    try:
        from src.proveedor_global.frontend.formula.motores.pieza import listar
        piezas = listar(db, modulo) or {}
    except Exception:
        piezas = {}
    productos = []
    for nombre, valor in lista:
        try:
            kilos = float(valor or 0)
        except (TypeError, ValueError):
            kilos = 0.0
        codigo = str(mapa.get(str(nombre).strip().upper()) or "").strip()
        prod = _por_codigo(db, codigo) if codigo else None
        base = (piezas.get(str(nombre).upper()) or {}).get("base") or {}
        if not prod:
            prod = _por_id(db, base.get("id")) if base.get("id") else None
        if not prod and not codigo:
            prod = _por_nombre(db, nombre)
        if not prod or bultos <= 0:
            continue
        productos.append({
            "id": prod["id"],
            "codigo": prod.get("codigo") or prod["id"],
            "nombre": prod.get("nombre") or nombre,
            "departamento": prod.get("departamento") or "",
            "stock_actual": prod.get("stock") if prod.get("stock") is not None else 0,
            "cantidad": bultos,
            "kilos": kilos,
            "corte": nombre,
        })
    if not lista:
        nota = f"{modulo} no tiene receta."
    else:
        nota = f"{modulo} · {len(lista)} cortes de esa receta."
    return {"origen": "consulta", "productos": productos, "nota": nota, "limpiar": True}


def _colgar(db, modulo, productos, bultos, costo, utiles) -> list:
    """El enlace y el pollo entero se ven. No suman plata ni kilos de la fórmula."""
    try:
        from src.proveedor_global.frontend.formula.motores.pieza import listar
        piezas = listar(db, modulo) or {}
    except Exception:
        piezas = {}
    salida = []
    for prod in productos:
        salida.append(prod)
        corte = str(prod.get("corte") or "").strip().upper()
        for pieza in (piezas.get(corte) or {}).get("piezas") or []:
            hallado = _por_id(db, pieza.get("id")) or _por_codigo(db, pieza.get("codigo"))
            if not hallado or str(hallado.get("id")) == str(prod.get("id")):
                continue
            salida.append({
                "id": hallado["id"],
                "codigo": hallado.get("codigo") or hallado["id"],
                "nombre": hallado.get("nombre") or pieza.get("nombre") or "",
                "departamento": hallado.get("departamento") or "",
                "stock_actual": prod.get("stock_actual") or 0,
                "cantidad": prod.get("cantidad") or 0,
                "costo": costo,
                "subtotal": 0.0,
                "extension": "enlace",
                "origen_id": prod.get("id"),
            })
    if str(modulo or "").strip() != "Pollo" or utiles <= 0 or bultos <= 0:
        return salida
    entero = _por_nombre(db, "Pollo entero")
    if not entero or any(str(p.get("id")) == str(entero.get("id")) for p in salida):
        return salida
    salida.append({
        "id": entero["id"],
        "codigo": entero.get("codigo") or entero["id"],
        "nombre": entero.get("nombre") or "Pollo entero",
        "departamento": entero.get("departamento") or "",
        "stock_actual": entero.get("stock") or 0,
        "cantidad": round(float(utiles) * float(bultos), 4),
        "costo": costo,
        "subtotal": 0.0,
        "extension": "entero",
    })
    return salida


def _por_id(db, ident):
    texto = str(ident or "").strip()
    if not texto:
        return None
    try:
        filas = db.execute_query(
            "SELECT id, codigo, nombre, stock, departamento FROM productos WHERE id = ? LIMIT 1",
            (texto,),
        ) or []
    except Exception:
        return None
    if not filas:
        return None
    fila = _dict(filas[0])
    return _producto(fila) if fila else None


def _producto(fila) -> dict:
    return {
        "id": str(fila.get("id") or ""),
        "codigo": str(fila.get("codigo") or fila.get("id") or ""),
        "nombre": fila.get("nombre") or "",
        "stock": float(fila.get("stock") or 0),
        "departamento": fila.get("departamento") or "",
    }


def _por_codigo(db, codigo: str):
    texto = str(codigo or "").strip()
    if not texto:
        return None
    try:
        filas = db.execute_query(
            "SELECT id, codigo, nombre, stock, departamento FROM productos "
            "WHERE codigo = ? OR CAST(id AS CHAR) = ? LIMIT 1",
            (texto, texto),
        ) or []
    except Exception:
        return None
    if not filas:
        return None
    return _producto(_dict(filas[0]))


def _por_nombre(db, nombre: str):
    fila = _uno_nombre(db, nombre)
    if not fila:
        return None
    prod = _producto(fila)
    if not prod["nombre"]:
        prod["nombre"] = nombre
    return prod


def _uno_nombre(db, nombre: str):
    try:
        filas = db.execute_query(
            "SELECT id, codigo, nombre, stock, departamento FROM productos "
            "WHERE UPPER(nombre) = UPPER(?) LIMIT 1",
            (nombre,),
        ) or []
    except Exception:
        return None
    if not filas:
        return None
    return _dict(filas[0])


def _dict(fila):
    if fila is None:
        return None
    if isinstance(fila, dict):
        return fila
    try:
        return {k: fila[k] for k in fila.keys()}
    except Exception:
        return None
