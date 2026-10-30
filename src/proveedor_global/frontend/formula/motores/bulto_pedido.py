"""El pedido no lista los cortes. Pide el cajón o el bulto, con el nombre de la fórmula."""

import math

_ORDEN = (
    ("Mocho", "Mocho"),
    ("Pecho", "Pecho"),
    ("Media Res", "Media res"),
    ("Cerdo", "Cerdo"),
    ("Pollo", "Pollo"),
    ("Congelado", "Congelado"),
)


def agrupar(db, filas) -> list:
    """Saca las presentaciones y deja un renglón por fórmula. El stock de cada una queda adentro."""
    indice = _indice(db)
    grupos = {}
    sueltos = []
    for fila in filas or []:
        modulo = _modulo(fila, indice)
        if not modulo:
            sueltos.append(fila)
            continue
        grupos.setdefault(modulo, []).append(fila)
    carne = []
    propios = []
    for modulo, miembros in grupos.items():
        if modulo in ("Mocho", "Pecho", "Media res"):
            carne.extend(miembros)
            continue
        if modulo in ("Pollo", "Cerdo", "Congelado"):
            propios.append((modulo, miembros))
            continue
        linea = _linea(db, modulo, miembros)
        if linea:
            sueltos.append(linea)
    if carne:
        sueltos.extend(_carne(db, grupos, carne))
    for modulo, miembros in propios:
        sueltos.extend(_umbral(db, modulo, miembros))
    if not any(modulo == "Pollo" for modulo, _miembros in propios):
        sueltos.extend(_pollo(db, []))
    return sueltos


def _carne(db, grupos, miembros) -> list:
    """Pide el bulto cuando esa fórmula vendió el 60%. El stock de los cortes se ve igual."""
    try:
        from src.proveedor_global.frontend.formula.motores.carne_stock import decidir
        nombres = decidir(db)
    except Exception:
        nombres = None
    salida = []
    for modulo in ("Mocho", "Pecho", "Media res"):
        propios = grupos.get(modulo) or []
        if not propios:
            continue
        linea = _linea(db, modulo, propios)
        if not linea:
            continue
        if nombres is not None and modulo not in nombres:
            _sin_comprar(linea)
        salida.append(linea)
    if nombres and "Media res" in nombres and not any(it.get("nombre") == "Media res" and float(it.get("cantidad_a_pedir") or 0) > 0 for it in salida):
        linea = _linea(db, "Media res", miembros)
        if linea:
            salida.append(linea)
    _explicar([it for it in salida if it.get("nombre") == "Media res"], "Media res")
    return salida


def _umbral(db, formula, miembros) -> list:
    """Pide el bulto cuando esa fórmula vendió el 60%. Pollo mira la composición."""
    if formula == "Pollo":
        return _pollo(db, miembros)
    linea = _linea(db, formula, miembros)
    if not linea:
        return []
    try:
        from src.proveedor_global.frontend.formula.motores.carne_stock import decidir_de
        nombres = decidir_de(db, formula)
    except Exception:
        nombres = None
    if nombres is not None and formula not in nombres:
        _sin_comprar(linea)
    return [linea]


_FIJO = {
    "POLLO ENTERO": "Pollo",
    "PECHUGA": "Pollo",
    "POLLO TROZADO": "Pollo",
}


def _modulo(fila, indice) -> str:
    ident = str((fila or {}).get("id") or "")
    if ident.startswith("formula:"):
        return ident.split(":", 1)[1]
    por_id, por_codigo, por_nombre = indice
    if ident and ident in por_id:
        return por_id[ident]
    codigo = str((fila or {}).get("codigo") or "").strip()
    if codigo and codigo in por_codigo:
        return por_codigo[codigo]
    nombre = str((fila or {}).get("nombre") or "").strip()
    if nombre.lower() in ("cajón de huevo", "cajon de huevo", "huevo"):
        return "Huevo"
    from src.proveedor_global.frontend.formula.motores.verdad import es_formula

    if es_formula(nombre):
        return "Huevo"
    return por_nombre.get(nombre.upper(), "")


def _indice(db):
    """Nombre, código e id de lo que se vende dentro de la fórmula. No se compra suelto."""
    por_id = {}
    por_codigo = {}
    por_nombre = dict(_FIJO)
    for tipo, etiqueta in _ORDEN:
        for corte in _cortes(db, tipo):
            clave = str(corte).strip().upper()
            if clave and clave not in por_nombre:
                por_nombre[clave] = etiqueta
        _sumar_codigos(db, tipo, etiqueta, por_codigo)
        _sumar_piezas(db, etiqueta, por_id, por_codigo, por_nombre)
    return por_id, por_codigo, por_nombre


def _sumar_codigos(db, tipo, etiqueta, por_codigo) -> None:
    try:
        from src.proveedor_global.frontend.formula.motores.orden import codigos
        mapa = codigos(db, tipo) or {}
    except Exception:
        return
    for codigo in mapa.values():
        texto = str(codigo or "").strip()
        if texto and texto not in por_codigo:
            por_codigo[texto] = etiqueta


def _sumar_piezas(db, etiqueta, por_id, por_codigo, por_nombre) -> None:
    try:
        from src.proveedor_global.frontend.formula.motores.pieza import listar
        grupos = listar(db, etiqueta) or {}
    except Exception:
        return
    for grupo in grupos.values():
        piezas = [grupo.get("base")] + list(grupo.get("piezas") or [])
        for pieza in piezas:
            if not pieza:
                continue
            ident = str(pieza.get("id") or "").strip()
            codigo = str(pieza.get("codigo") or "").strip()
            nombre = str(pieza.get("nombre") or "").strip().upper()
            if ident:
                por_id[ident] = etiqueta
            if codigo:
                por_codigo.setdefault(codigo, etiqueta)
            if nombre:
                por_nombre.setdefault(nombre, etiqueta)


def _cortes(db, tipo: str) -> list:
    try:
        from src.proveedor_global.frontend.formula.motores.orden import cortes
        pares = cortes(db, tipo) or []
    except Exception:
        pares = []
    if not pares:
        try:
            from src.proveedor_global.frontend.formula.motores.lectura import leer
            pares = leer(db, tipo) or []
        except Exception:
            pares = []
    if pares:
        return [par[0] for par in pares]
    try:
        if tipo in ("Media Res", "Mocho", "Pecho"):
            from src.jefe.promedios.carne.motor_carne import MotorCarne
            return [corte[0] for corte in MotorCarne.get_cortes(tipo)]
        if tipo == "Cerdo":
            from src.jefe.promedios.cerdo.motor_cerdo import MotorCerdo
            return [corte[0] for corte in MotorCerdo.get_cortes()]
        if tipo == "Pollo":
            from src.jefe.promedios.pollo.motor_pollo import MotorPollo
            return [corte[0] for corte in MotorPollo.get_cortes()]
    except Exception:
        return []
    return []


def _linea(db, modulo: str, miembros) -> dict | None:
    detector = any("stock_actual" in (m or {}) or "cantidad_a_pedir" in (m or {}) for m in miembros)
    if modulo == "Huevo":
        from src.proveedor_global.frontend.formula.motores.verdad import leer
        dato = leer(db, "Huevo")
        cajones = float(dato.get("cajones") or 0)
        costo = float(dato.get("costo") or 0)
        if cajones > 0:
            return None
        pedir = _pedir_cajones(cajones)
        return _armar(detector, "Huevo", "Huevo", cajones, pedir, costo, miembros)
    return _armar(detector, modulo, modulo, 0.0, 1, 0.0, miembros)


def _pollo(db, miembros) -> list:
    """Caja si faltan los dos cortes que rinden. Kilos de uno solo en el caso extremo."""
    try:
        from src.proveedor_global.frontend.formula.motores.caja_pollo import consultar
        dato = consultar(db)
    except Exception:
        return []
    nombre = dato["nombre"]
    if dato.get("unidad") == "kg" and dato["pedir"] > 0:
        nombre = f"{nombre} (kg)"
    elif dato.get("unidad") == "caja" and dato["pedir"] > 0:
        nombre = f"{nombre} (cajas)"
    linea = _armar(True, "Pollo", nombre, dato["stock_pedido"], dato["pedir"], dato["costo"], [])
    linea["stock_minimo"] = dato["min_kg"]
    linea["stock_maximo"] = dato["max_kg"]
    linea["adentro"] = _vista_pollo(dato, miembros)
    if dato["pedir"] <= 0:
        linea["cantidad_a_pedir"] = 0
        linea["costo_estimado_total"] = 0
        linea["presupuesto_linea"] = 0
        linea["motivo"] = "en_formula"
    lineas = [linea]
    extra = float(dato.get("extra_kg") or 0)
    if extra > 0:
        corte = _armar(
            True, "Pollo", f"{dato['extra_nombre']} (kg)",
            dato.get("extra_stock") or 0, extra, dato.get("costo_kg") or 0, [],
        )
        corte["id"] = f"formula:Pollo:{dato['extra_nombre']}"
        corte["stock_minimo"] = dato.get("extra_min") or 0
        corte["stock_maximo"] = dato.get("extra_max") or 0
        corte["adentro"] = []
        lineas.append(corte)
    _explicar(lineas[:1], "Pollo")
    _aplicar_rango(lineas[0], "Pollo", db)
    return lineas


def _aplicar_rango(linea, modulo: str, db) -> None:
    """La caja no se clava en un número: 10 a 12, o 5 a 7 si ya hay stock."""
    try:
        from src.proveedor_global.frontend.predictiva.consultar import cifra
        proy = cifra(modulo, db)
    except Exception:
        return
    if proy.get("pedir_max") is None:
        return
    bajo = int(proy.get("pedir_min") or 0)
    alto = int(proy.get("pedir_max") or 0)
    linea["porque"] = proy.get("porque") or linea.get("porque") or ""
    linea["rango"] = f"{bajo} a {alto}" if bajo != alto else str(alto)
    linea["cantidad_a_pedir"] = float(alto)
    linea["stock_maximo"] = float(alto)
    if alto <= 0:
        linea["motivo"] = "stock"
        linea["costo_estimado_total"] = 0
        linea["presupuesto_linea"] = 0
    else:
        costo = float(linea.get("costo_unitario") or 0)
        linea["costo_estimado_total"] = round(alto * costo, 2)
        linea["presupuesto_linea"] = round(alto * costo, 2)


def _explicar(lineas, modulo: str) -> None:
    try:
        from src.proveedor_global.frontend.predictiva.consultar import porque
        texto = porque(modulo)
    except Exception:
        return
    if not texto:
        return
    for linea in lineas:
        if float(linea.get("cantidad_a_pedir") or 0) > 0:
            linea["porque"] = texto


def _vista_pollo(dato, miembros) -> list:
    salida = []
    pedido = str(dato.get("corte") or "")
    marcas = {"plata": "rinde", "no_cuenta": "no cuenta", "caja": "va en la caja"}
    for fila in dato.get("filas") or []:
        nombre = str(fila.get("nombre") or "")
        cajas = float(fila.get("cajas") or 0)
        rol = marcas.get(fila.get("rol") or "", "va en la caja")
        if nombre == pedido:
            rol = "se pide"
        salida.append({
            "codigo": "",
            "nombre": f"{nombre} · {rol} · {cajas:.0f} cajas",
            "stock_actual": fila.get("stock") or 0,
        })
    vistos = {str(f.get("nombre") or "").split(" · ")[0].upper() for f in salida}
    for fila in miembros or []:
        nombre = str((fila or {}).get("nombre") or "").strip()
        if not nombre or nombre.upper() in vistos:
            continue
        salida.append({
            "codigo": (fila or {}).get("codigo") or "",
            "nombre": nombre,
            "stock_actual": (fila or {}).get("stock_actual", (fila or {}).get("stock", 0)),
        })
    if dato.get("texto"):
        salida.append({
            "codigo": "",
            "nombre": dato["texto"],
            "stock_actual": "",
        })
    return salida


def _sin_comprar(linea: dict) -> None:
    """El stock queda a la vista. Esta vuelta no se pide el bulto."""
    linea["cantidad_a_pedir"] = 0.0
    linea["stock_maximo"] = 0.0
    linea["costo_estimado_total"] = 0.0
    linea["presupuesto_linea"] = 0.0
    linea["motivo"] = "en_formula"


def _pedir_cajones(cajones: float) -> int:
    if cajones > 0:
        return 0
    return max(1, math.ceil(-float(cajones) - 1e-9))


def _armar(detector: bool, modulo: str, nombre: str, stock: float, pedir: int, costo: float, miembros=None) -> dict:
    ident = f"formula:{modulo}"
    base = {
        "id": ident,
        "codigo": "",
        "nombre": nombre,
        "departamento": nombre,
        "es_formula": True,
        "adentro": _adentro(miembros),
    }
    if detector:
        base.update({
            "stock_actual": stock,
            "stock_minimo": 0.0,
            "stock_maximo": float(pedir),
            "cantidad_a_pedir": float(pedir),
            "costo_unitario": costo,
            "precio_unitario": 0.0,
            "valor_unitario": costo,
            "costo_estimado_total": round(pedir * costo, 2),
            "presupuesto_linea": round(pedir * costo, 2),
            "motivo": "critico" if pedir else "sin_piso",
        })
        return base
    base.update({
        "stock": stock,
        "stock_minimo": stock,
        "stock_maximo": stock + pedir,
        "costo": costo,
        "precio": 0.0,
        "motivo": "critico" if pedir else "sin_piso",
    })
    return base


def _adentro(miembros) -> list:
    salida = []
    for fila in miembros or []:
        if str((fila or {}).get("id") or "").startswith("formula:"):
            continue
        salida.append({
            "codigo": (fila or {}).get("codigo") or "",
            "nombre": (fila or {}).get("nombre") or "",
            "stock_actual": (fila or {}).get("stock_actual", (fila or {}).get("stock", 0)),
        })
    return salida
