"""Cada fórmula acepta los kilos del jefe y le manda el stock al inventario.

Mocho, pecho y media res usan los mismos kilos. Pollo, cerdo y congelado tienen los suyos.
La merma no entra al stock. El pedido sale al 60%. Si mocho y pecho llegan juntos, pide una media res.
"""

_UMBRAL = 0.60
_FORMULAS = ("Mocho", "Pecho", "Media res")
_POLLO = ("Pollo",)
_CERDO = ("Cerdo",)
_CONGELADO = ("Congelado",)
_TIPO = {
    "Mocho": "Mocho",
    "Pecho": "Pecho",
    "Media res": "Media res",
    "Pollo": "Pollo",
    "Cerdo": "Cerdo",
    "Congelado": "Congelado",
}
_TABLA = "formula_carne"
_CORTE = "formula_carne_corte"


def entrar(cursor, db, modulo: str, bultos, precio=0, cortes=None) -> float:
    """Suma los kilos útiles de ese bulto y le manda al inventario el stock y el costo.

    Si faltan cortes, esos kilos ya son merma y no entran. El costo es el precio
    del cajón dividido por los kilos que quedaron.
    """
    modulo = _nombre(modulo)
    if modulo not in _FORMULAS and modulo not in _POLLO and modulo not in _CERDO and modulo not in _CONGELADO:
        return 0.0
    try:
        bultos = float(bultos or 0)
    except (TypeError, ValueError):
        bultos = 0.0
    if bultos == 0:
        return 0.0
    lista = _lista_cortes(db, modulo, cortes)
    kilos = abs(bultos) * sum(valor for _corte, valor in lista)
    if bultos < 0:
        kilos = -kilos
    _entregar(cursor, db, modulo, bultos, precio, lista)
    try:
        _asegurar_cursor(cursor)
        existe, actual = _fila(cursor, modulo)
        queda = actual + kilos
        if queda < 0:
            queda = 0.0
        if not existe:
            try:
                cursor.execute(
                    f"INSERT INTO {_TABLA} (modulo, kilos, ultima) VALUES (?, ?, ?)",
                    (modulo, queda, kilos if kilos > 0 else 0),
                )
            except Exception:
                cursor.execute(
                    f"UPDATE {_TABLA} SET kilos = ? WHERE modulo = ?",
                    (queda, modulo),
                )
        elif kilos > 0:
            cursor.execute(
                f"UPDATE {_TABLA} SET kilos = ?, ultima = ? WHERE modulo = ?",
                (queda, kilos, modulo),
            )
        else:
            cursor.execute(
                f"UPDATE {_TABLA} SET kilos = ? WHERE modulo = ?",
                (queda, modulo),
            )
        if kilos > 0:
            _abrir_reloj(cursor, _familia(modulo))
    except Exception:
        return 0.0
    return queda


def salir(cursor, db, modulo: str, bultos, cortes=None) -> float:
    """La anulación resta los kilos de esa carga. El registro de la fórmula sigue."""
    try:
        bultos = float(bultos or 0)
    except (TypeError, ValueError):
        return 0.0
    return entrar(cursor, db, modulo, -abs(bultos), 0, cortes)


def consultar(db, formula: str = "Mocho") -> dict:
    """Lee la carga, el stock del inventario y los kilos vendidos. No escribe."""
    formula = _nombre(formula)
    grupo = _grupo(formula)
    cargado = _cargado(db, grupo)
    ultima = _ultima(db, grupo)
    desde = _ultimo(db, _familia(formula))
    ventas = _ventas(db, desde) if desde is not None else []
    cortes = {nombre: _cortes(db, nombre) for nombre in grupo}
    piezas = _piezas(db, formula)
    ventas, extra, por_pieza = _apartar(ventas, piezas)
    vendido_corte = _por_corte(ventas, cortes)
    for corte, cantidad in extra.items():
        vendido_corte[corte] = vendido_corte.get(corte, 0.0) + cantidad
    vendido = {
        nombre: round(sum(vendido_corte.get(corte.upper(), 0.0) for corte, _k in lista), 2)
        for nombre, lista in cortes.items()
    }
    unico = round(sum(vendido_corte.values()), 2)
    stock = round(sum(cargado.values()) - unico, 2)
    porcentaje = {}
    for nombre in grupo:
        base = cargado.get(nombre) or 0.0
        porcentaje[nombre] = (vendido[nombre] / base) if base > 0 else 0.0
    inventario = _inventario(db, cortes.get(formula) or [], piezas, formula)
    pedido_txt = _texto_pedido(_decidir(porcentaje, cargado), porcentaje, grupo)
    filas = []
    for corte, kilos in cortes.get(formula) or []:
        grupo_pieza = piezas.get(corte.upper()) or {}
        base = grupo_pieza.get("base") or {}
        stock_corte = inventario.get(corte.upper()) or {}
        if not isinstance(stock_corte, dict):
            stock_corte = {"stock": stock_corte, "codigo": ""}
        codigo = str(stock_corte.get("codigo") or base.get("codigo") or "")
        numero = stock_corte.get("stock")
        anexos = []
        for pieza in grupo_pieza.get("piezas") or []:
            anexos.append({
                "id": pieza.get("id") or "",
                "codigo": pieza.get("codigo") or "",
                "nombre": pieza.get("nombre") or "",
                "vendido": round(por_pieza.get(str(pieza.get("nombre") or "").upper(), 0.0), 2),
            })
        filas.append({
            "nombre": corte,
            "codigo": codigo,
            "kilos": kilos,
            "stock": numero if isinstance(stock_corte, dict) else stock_corte,
            "vendido": round(vendido_corte.get(corte.upper(), 0.0), 2),
            "propio": round(
                vendido_corte.get(corte.upper(), 0.0)
                - sum(item["vendido"] for item in anexos),
                2,
            ),
            "anexos": anexos,
        })
    if formula == "Pollo":
        stock = round(sum(float(f.get("stock") or 0) for f in filas), 2)
        try:
            from src.proveedor_global.frontend.formula.motores.caja_pollo import desde
            from src.proveedor_global.frontend.formula.motores.orden import costo_de, merma_de
            decision = desde(filas, merma_de(db, "Pollo"), costo_de(db, "Pollo"))
            if decision.get("texto"):
                pedido_txt = decision["texto"]
        except Exception:
            pass
    return {
        "formula": formula,
        "stock": stock,
        "cargado": cargado,
        "ultima": ultima,
        "vendido": vendido,
        "porcentaje": porcentaje,
        "pedir": _decidir(porcentaje, cargado),
        "cortes": filas,
        "texto": _texto(stock, ultima, vendido, porcentaje, grupo),
        "pedido": pedido_txt,
    }


def decidir(db) -> list:
    """Qué bulto de carne pedir. Vacío si nadie llegó al 60%."""
    return decidir_de(db, "Mocho")


def decidir_de(db, formula: str) -> list:
    """Qué bulto pedir de esa familia. Vacío si no llegó al 60%."""
    try:
        return list(consultar(db, formula).get("pedir") or [])
    except Exception:
        return []


def _decidir(porcentaje, cargado) -> list:
    mocho = porcentaje.get("Mocho") or 0.0
    pecho = porcentaje.get("Pecho") or 0.0
    if (cargado.get("Mocho") or 0) > 0 and (cargado.get("Pecho") or 0) > 0 and mocho >= _UMBRAL and pecho >= _UMBRAL:
        return ["Media res"]
    salida = []
    for nombre in porcentaje:
        if (cargado.get(nombre) or 0) > 0 and (porcentaje.get(nombre) or 0) >= _UMBRAL:
            salida.append(nombre)
    return salida


def _texto(stock, ultima, vendido, porcentaje, grupo=_FORMULAS) -> str:
    if len(grupo) == 1 and stock == 0 and not (ultima.get(grupo[0]) or 0):
        return "Espera los kilos del jefe. La merma no entra al stock. El pedido sale al 60%."
    if stock == 0 and not any((ultima.get(nombre) or 0) > 0 for nombre in grupo):
        return "Todavía no hay una carga. Mocho, pecho y media res van a usar el mismo stock."
    partes = []
    for nombre in grupo:
        if (ultima.get(nombre) or 0) <= 0 and (vendido.get(nombre) or 0) <= 0:
            continue
        carga = ultima.get(nombre) or 0
        if carga > 0:
            partes.append(f"última carga de {nombre} {_kg(carga)}")
    if len(grupo) == 1:
        cabeza = f"Stock de {grupo[0].lower()} " + _kg(stock)
    else:
        cabeza = "Stock compartido " + _kg(stock)
    if partes:
        cabeza += ". " + ", ".join(partes)
    cuerpo = []
    for nombre in grupo:
        vend = vendido.get(nombre) or 0
        porc = porcentaje.get(nombre) or 0
        if porc > 0:
            cuerpo.append(f"{nombre} vendió {_kg(vend)} ({porc * 100:.0f}%)")
        elif vend > 0:
            cuerpo.append(f"{nombre} vendió {_kg(vend)}")
    if cuerpo:
        cabeza += ". " + ". ".join(cuerpo) + "."
    else:
        cabeza += ". Todavía no se vendió de esta carga."
    return cabeza


def _texto_pedido(nombres, porcentaje, grupo=_FORMULAS) -> str:
    if not nombres and len(grupo) == 1:
        return f"El pedido de {grupo[0].lower()} espera al 60% vendido de ese bulto."
    if not nombres:
        return "El pedido espera al 60% vendido de mocho, de pecho o de media res."
    if nombres == ["Media res"] and (porcentaje.get("Mocho") or 0) >= _UMBRAL and (porcentaje.get("Pecho") or 0) >= _UMBRAL:
        return "Mocho y pecho pasaron el 60%. Se pide una media res."
    return "Se pide " + " y ".join(nombres) + "."


def _kilos_bulto(db, modulo: str) -> float:
    return sum(kilos for _nombre, kilos in _cortes(db, modulo))


def _cortes(db, modulo: str) -> list:
    tipo = _TIPO.get(modulo, modulo)
    pares = []
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
    if not pares and modulo == "Pollo":
        try:
            from src.jefe.promedios.pollo.motor_pollo import MotorPollo
            pares = list(MotorPollo.get_cortes())
        except Exception:
            pares = []
    elif not pares and modulo == "Cerdo":
        try:
            from src.jefe.promedios.cerdo.motor_cerdo import MotorCerdo
            pares = list(MotorCerdo.get_cortes())
        except Exception:
            pares = []
    elif not pares and modulo in _FORMULAS:
        try:
            from src.jefe.promedios.carne.motor_carne import MotorCarne
            pares = list(MotorCarne.get_cortes("Media Res" if modulo == "Media res" else modulo))
        except Exception:
            pares = []
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


def _grupo(formula: str):
    nombre = _nombre(formula)
    if nombre == "Pollo":
        return _POLLO
    if nombre == "Cerdo":
        return _CERDO
    if nombre == "Congelado":
        return _CONGELADO
    return _FORMULAS


def _familia(modulo: str) -> str:
    nombre = _nombre(modulo)
    if nombre in ("Pollo", "Cerdo", "Congelado"):
        return nombre
    return "Carne"


def _lista_cortes(db, modulo, cortes) -> list:
    """Los kilos que sí se venden. La merma no está en esta lista."""
    if not cortes:
        return _cortes(db, modulo)
    salida = []
    for nombre, kilos in cortes:
        try:
            kilos = float(kilos or 0)
        except (TypeError, ValueError):
            continue
        nombre = str(nombre or "").strip()
        if nombre and kilos > 0:
            salida.append((nombre, kilos))
    return salida


def _entregar(cursor, db, modulo: str, bultos, precio, cortes=None) -> None:
    """Manda stock y costo. El precio del cajón se divide por los kilos sin merma."""
    cortes = _lista_cortes(db, modulo, cortes)
    if not cortes:
        return
    try:
        bultos = float(bultos or 0)
    except (TypeError, ValueError):
        return
    if bultos == 0:
        return
    utiles = sum(kilos for _nombre_corte, kilos in cortes)
    try:
        precio = float(precio or 0)
    except (TypeError, ValueError):
        precio = 0.0
    costo = 0.0
    if bultos > 0 and precio > 0 and utiles > 0:
        costo = precio / utiles
    elif bultos > 0:
        try:
            from src.proveedor_global.frontend.formula.motores.orden import costo_de
            costo = costo_de(db, modulo)
        except Exception:
            costo = 0.0
    signo = 1 if bultos > 0 else -1
    try:
        from src.proveedor_global.frontend.formula.motores.orden import codigos
        mapa = codigos(db, modulo) or {}
    except Exception:
        mapa = {}
    lineas = [
        {
            "nombre": nombre,
            "kilos": signo * kilos * abs(bultos),
            "costo": costo,
            "codigo": str(mapa.get(str(nombre).strip().upper()) or ""),
        }
        for nombre, kilos in cortes
    ]
    try:
        from src.proveedor_global.frontend.formula.motores.inventario import aceptar
        aceptar(cursor, lineas)
    except Exception:
        return


def _cargado(db, grupo=_FORMULAS) -> dict:
    filas = _leer_tabla(db)
    return {nombre: float(filas.get(nombre, {}).get("kilos") or 0) for nombre in grupo}


def _ultima(db, grupo=_FORMULAS) -> dict:
    filas = _leer_tabla(db)
    return {nombre: float(filas.get(nombre, {}).get("ultima") or 0) for nombre in grupo}


def _leer_tabla(db) -> dict:
    try:
        _asegurar(db)
        crudas = db.execute_query(f"SELECT modulo, kilos, ultima FROM {_TABLA}") or []
    except Exception:
        return {}
    salida = {}
    for cruda in crudas:
        fila = _dict(cruda)
        nombre = _nombre(fila.get("modulo"))
        if nombre:
            salida[nombre] = fila
    return salida


def _ventas(db, desde) -> list:
    where = [
        "(v.estado IS NULL OR UPPER(TRIM(v.estado)) NOT IN "
        "('CANCELADA','ANULADA','CANCELADO','ANULADO'))"
    ]
    params = []
    if desde is not None:
        where.append("dv.id > ?")
        params.append(int(desde))
    sql = (
        "SELECT dv.nombre_producto AS nombre, dv.cantidad AS cantidad, p.nombre AS producto "
        "FROM detalles_ventas dv "
        "JOIN ventas v ON v.id = dv.id_venta "
        "LEFT JOIN productos p ON p.id = dv.id_producto "
        "WHERE " + " AND ".join(where)
    )
    try:
        crudas = db.execute_query(sql, tuple(params)) or []
    except Exception:
        return []
    salida = []
    for cruda in crudas:
        fila = _dict(cruda)
        try:
            cantidad = float(fila.get("cantidad") or 0)
        except (TypeError, ValueError):
            cantidad = 0.0
        if cantidad <= 0:
            continue
        salida.append((str(fila.get("nombre") or fila.get("producto") or ""), cantidad))
    return salida


def _por_corte(ventas, cortes) -> dict:
    indice = []
    for lista in cortes.values():
        for nombre, _kilos in lista:
            clave = nombre.upper()
            if clave not in [item[0] for item in indice]:
                indice.append((clave, nombre))
    indice.sort(key=lambda item: len(item[0]), reverse=True)
    suma = {}
    for nombre, cantidad in ventas:
        alto = nombre.upper()
        elegido = ""
        for clave, original in indice:
            if clave == alto or clave in alto:
                elegido = clave
                break
        if elegido:
            suma[elegido] = suma.get(elegido, 0.0) + cantidad
    return suma


def _piezas(db, formula) -> dict:
    try:
        from src.proveedor_global.frontend.formula.motores.pieza import listar
        return listar(db, formula) or {}
    except Exception:
        return {}


def _apartar(ventas, piezas):
    """La oferta y el trozado se cuentan en su corte, no como otro producto."""
    exactos = {}
    for grupo in (piezas or {}).values():
        corte = str(grupo.get("corte") or "").upper()
        if not corte:
            continue
        for pieza in grupo.get("piezas") or []:
            nombre = str(pieza.get("nombre") or "").strip().upper()
            if nombre:
                exactos[nombre] = corte
        base = grupo.get("base") or {}
        propio = str(base.get("nombre") or "").strip().upper()
        if propio and propio != corte:
            exactos[propio] = corte
    resto = []
    extra = {}
    por_pieza = {}
    for nombre, cantidad in ventas or []:
        alto = str(nombre or "").strip().upper()
        corte = exactos.get(alto)
        if not corte:
            resto.append((nombre, cantidad))
            continue
        extra[corte] = extra.get(corte, 0.0) + cantidad
        por_pieza[alto] = por_pieza.get(alto, 0.0) + cantidad
    return resto, extra, por_pieza


def _inventario(db, cortes, piezas=None, modulo: str = "") -> dict:
    piezas = piezas or {}
    try:
        from src.proveedor_global.frontend.formula.motores.orden import codigos
        mapa = codigos(db, modulo) or {}
    except Exception:
        mapa = {}
    salida = {}
    for nombre, _kilos in cortes:
        grupo = piezas.get(nombre.upper()) or {}
        base = grupo.get("base") or {}
        codigo_jefe = str(mapa.get(str(nombre).strip().upper()) or "").strip()
        ident = str(base.get("id") or "")
        try:
            if codigo_jefe:
                filas = db.execute_query(
                    "SELECT id, codigo, stock FROM productos WHERE codigo = ? OR CAST(id AS CHAR) = ? LIMIT 1",
                    (codigo_jefe, codigo_jefe),
                ) or []
            elif ident:
                filas = db.execute_query(
                    "SELECT id, codigo, stock FROM productos WHERE id = ? LIMIT 1",
                    (ident,),
                ) or []
            else:
                filas = db.execute_query(
                    "SELECT id, codigo, stock FROM productos WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(?)) LIMIT 1",
                    (nombre,),
                ) or []
        except Exception:
            filas = []
        if not filas:
            salida[nombre.upper()] = {
                "codigo": codigo_jefe or str(base.get("codigo") or ""),
                "stock": None,
            }
            continue
        fila = _dict(filas[0])
        try:
            numero = float(fila.get("stock") or 0)
        except (TypeError, ValueError):
            numero = None
        crudo = numero
        numero = _stock_casa(fila.get("id"), numero)
        if crudo is not None and numero is not None and float(crudo) != float(numero):
            try:
                from src.proveedor_global.frontend.formula.motores.extension import seguir
                seguir(db, fila.get("id"))
            except Exception:
                pass
        codigo = str(base.get("codigo") or "").strip() or str(fila.get("codigo") or "").strip()
        if not codigo:
            codigo = str(fila.get("id") or "").strip()
        salida[nombre.upper()] = {
            "codigo": codigo,
            "stock": numero,
        }
    return salida


def _stock_casa(ident, stock):
    """En casa el inventario deja el número en la cola. La copia de la tienda no lo tapa."""
    if ident in (None, ""):
        return stock
    try:
        from src.base_de_datos.offline_nutricion import offline_nutricion_manager
        pendientes = offline_nutricion_manager.productos_pendientes() or []
    except Exception:
        return stock
    for registro in pendientes:
        datos = registro.get("datos") or {}
        pid = datos.get("id") if datos.get("id") not in (None, "") else registro.get("id")
        if str(pid) != str(ident):
            continue
        if datos.get("stock") is None:
            return stock
        try:
            return float(datos.get("stock"))
        except (TypeError, ValueError):
            return stock
    return stock


_TABLAS = set()


def _abrir_reloj(cursor, familia: str = "Carne") -> None:
    """La primera carga marca el último ticket. Lo anterior no cuenta como vendido de este stock."""
    if _CORTE not in _TABLAS:
        try:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {_CORTE} (modulo VARCHAR(40) PRIMARY KEY, ultimo INT)"
            )
            _TABLAS.add(_CORTE)
        except Exception:
            try:
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {_CORTE} (modulo TEXT PRIMARY KEY, ultimo INTEGER)"
                )
                _TABLAS.add(_CORTE)
            except Exception:
                return
    try:
        cursor.execute(f"SELECT ultimo FROM {_CORTE} WHERE modulo = ?", (familia,))
        if cursor.fetchone():
            return
    except Exception:
        return
    try:
        cursor.execute("SELECT MAX(id) FROM detalles_ventas")
        fila = cursor.fetchone()
        ultimo = int((fila[0] if not isinstance(fila, dict) else fila.get("id") or fila.get("MAX(id)")) or 0)
    except Exception:
        ultimo = 0
    try:
        cursor.execute(
            f"INSERT INTO {_CORTE} (modulo, ultimo) VALUES (?, ?)",
            (familia, ultimo),
        )
    except Exception:
        return


def _ultimo(db, familia: str = "Carne"):
    try:
        _asegurar(db)
        filas = db.execute_query(
            f"SELECT ultimo FROM {_CORTE} WHERE modulo = ? LIMIT 1",
            (familia,),
        ) or []
    except Exception:
        return None
    if not filas:
        return None
    fila = _dict(filas[0])
    try:
        return int(fila.get("ultimo") or 0)
    except (TypeError, ValueError):
        return None


def _asegurar(db) -> None:
    if _TABLA in _TABLAS:
        return
    hecho = db.execute_non_query(
        f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
        "modulo VARCHAR(40) PRIMARY KEY, kilos DOUBLE NOT NULL DEFAULT 0, ultima DOUBLE NOT NULL DEFAULT 0)"
    )
    if hecho:
        _TABLAS.add(_TABLA)
        return
    if db.execute_non_query(
        f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
        "modulo TEXT PRIMARY KEY, kilos REAL NOT NULL DEFAULT 0, ultima REAL NOT NULL DEFAULT 0)"
    ):
        _TABLAS.add(_TABLA)


def _asegurar_cursor(cursor) -> None:
    if _TABLA in _TABLAS:
        return
    try:
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
            "modulo VARCHAR(40) PRIMARY KEY, kilos DOUBLE NOT NULL DEFAULT 0, ultima DOUBLE NOT NULL DEFAULT 0)"
        )
        _TABLAS.add(_TABLA)
    except Exception:
        try:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
                "modulo TEXT PRIMARY KEY, kilos REAL NOT NULL DEFAULT 0, ultima REAL NOT NULL DEFAULT 0)"
            )
            _TABLAS.add(_TABLA)
        except Exception:
            pass


def _fila(cursor, modulo: str):
    try:
        cursor.execute(f"SELECT kilos FROM {_TABLA} WHERE modulo = ? LIMIT 1", (modulo,))
        cruda = cursor.fetchone()
    except Exception:
        return False, 0.0
    if not cruda:
        return False, 0.0
    fila = _dict(cruda, cursor)
    try:
        return True, float(fila.get("kilos") or 0)
    except (TypeError, ValueError):
        return True, 0.0


def _nombre(modulo) -> str:
    texto = str(modulo or "").strip()
    bajo = texto.lower()
    if bajo == "mocho":
        return "Mocho"
    if bajo == "pecho":
        return "Pecho"
    if bajo in ("media res", "mediares"):
        return "Media res"
    if bajo == "pollo":
        return "Pollo"
    if bajo == "cerdo":
        return "Cerdo"
    if bajo == "congelado":
        return "Congelado"
    return texto


def _kg(numero) -> str:
    try:
        numero = float(numero or 0)
    except (TypeError, ValueError):
        return "0 kg"
    if abs(numero - round(numero)) < 1e-4:
        return f"{int(round(numero))} kg"
    return f"{numero:.2f} kg"


def _dict(fila, cursor=None) -> dict:
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return {str(k).lower(): v for k, v in fila.items()}
    if hasattr(fila, "keys"):
        return {str(k).lower(): fila[k] for k in fila.keys()}
    if cursor is not None:
        try:
            cols = [d[0] for d in (cursor.description or [])]
            return {str(cols[i]).lower(): fila[i] for i in range(min(len(cols), len(fila)))}
        except Exception:
            pass
    try:
        return {"kilos": fila[0]}
    except Exception:
        return {}
