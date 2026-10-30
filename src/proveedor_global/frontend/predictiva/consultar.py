"""Arma el texto que ve la pantalla y el que viaja en el WhatsApp."""

from datetime import date

from src.proveedor_global.frontend.predictiva.calendario.jornada import hasta_el_camion, leer as leer_local
from src.proveedor_global.frontend.predictiva.motor.calcular import definir, proyectar, rango, ritmo_de
from src.proveedor_global.frontend.predictiva.motor.memoria import anotar, leer, por_dia, reparto_de


def hoy_en_curso(db=None) -> dict:
    """Lee el stock de ahora, lo anota una vez por día y proyecta pollo y media res."""
    datos = leer()
    stock = _stock(db)
    if stock is not None:
        anotar(
            date.today().isoformat(),
            stock.get("pollo") or 0,
            stock.get("media") or 0,
            {k: stock[k] for k in ("cerdo", "congelado", "huevo") if k in stock},
        )
        datos = leer()
    return armar(datos, stock or {"pollo": 0.0, "media": 0.0}, date.today())


def armar(datos, stock, hoy) -> dict:
    historial = datos.get("historial") or []
    pollo = _uno(
        por_dia(historial, "pollo"), stock.get("pollo") or 0,
        reparto_de(datos, "Pollo"), hoy, "cajas",
    )
    media = _uno(
        por_dia(historial, "media"), stock.get("media") or 0,
        reparto_de(datos, "Carne"), hoy, "medias",
    )
    return {"pollo": pollo, "media": media, "historial": datos.get("historial") or []}


def cifra(modulo: str, db=None) -> dict:
    """La proyección de esa fórmula, con la banda 10 a 12 si corresponde."""
    try:
        from src.base_de_datos.database import db_manager
        proy = hoy_en_curso(db or db_manager)
    except Exception:
        proy = hoy_en_curso(db)
    clave = "media" if str(modulo).lower().startswith("media") else "pollo" if modulo == "Pollo" else ""
    if not clave:
        return {}
    return dict(proy.get(clave) or {})


def porque(modulo: str) -> str:
    try:
        from src.base_de_datos.database import db_manager
        proy = hoy_en_curso(db_manager)
    except Exception:
        proy = hoy_en_curso(None)
    clave = "media" if str(modulo).lower().startswith("media") else "pollo" if modulo == "Pollo" else ""
    if not clave:
        return ""
    return str((proy.get(clave) or {}).get("porque") or "")


def _uno(muestras, stock, reparto, hoy, unidad) -> dict:
    banda = definir(muestras)
    if not banda["listo"]:
        ritmo, origen = 0.0, "sin historial"
    else:
        ritmo, origen = ritmo_de(banda["maximo"], banda["minimo"], list(muestras or [])[-7:])
    proy = proyectar(hoy, reparto, ritmo, stock, unidad)
    proy["origen"] = origen
    proy["bandas"] = banda["listo"]
    proy["pico_n"] = banda["pico"]
    proy["minimo"] = banda["minimo"]
    proy["maximo"] = banda["maximo"]
    _poner_rango(proy, banda, unidad, stock)
    return proy


def _poner_rango(proy, banda, unidad, stock) -> None:
    """3 a 5 cajas por día si todavía no hay historial. El resultado es una banda, no un clavo."""
    if banda["listo"]:
        piso, techo = banda["minimo"], banda["maximo"]
    elif unidad == "cajas":
        piso, techo = 3.0, 5.0
    else:
        proy["porque"] += _banda(banda, unidad, stock)
        proy["pedir_min"] = proy.get("pedir") or 0
        proy["pedir_max"] = proy.get("pedir") or 0
        return
    if not proy.get("entrega") or not proy.get("hasta"):
        proy["pedir_min"] = 0
        proy["pedir_max"] = 0
        return
    from datetime import timedelta
    dias = hasta_el_camion(proy["entrega"], proy["hasta"] + timedelta(days=1), leer_local())
    bajo, alto = rango(dias, stock, piso, techo)
    proy["pedir_min"] = bajo
    proy["pedir_max"] = alto
    proy["pedir"] = alto
    proy["porque"] = _texto_rango(proy, unidad, stock, piso, techo, bajo, alto, dias, banda)


def _texto_rango(proy, unidad, stock, piso, techo, bajo, alto, dias, banda) -> str:
    desde = _txt(piso)
    hasta = _txt(techo)
    stock_txt = _txt(stock)
    dias_txt = _txt(dias)
    if bajo <= 0 and alto <= 0:
        pedido = f"Con {stock_txt} {unidad} alcanza."
    elif bajo == alto:
        pedido = f"Se piden {alto} {unidad}."
    else:
        pedido = f"Se piden {bajo} a {alto} {unidad}."
    historia = ""
    if banda["listo"]:
        historia = f" El pico viejo {_txt(banda['pico'])} no se compra."
    else:
        historia = " Todavía sin historial: se usa la venta de 3 a 5 por día."
    llegada = ""
    if proy.get("entrega"):
        llegada = f" Hasta el {_nombre_proy(proy.get('hasta'))}."
    return (
        f"Cubre {dias_txt} días, de {desde} a {hasta} {unidad} por día, "
        f"con {stock_txt} en stock. {pedido}{llegada}{historia}"
    )


def _nombre_proy(dia) -> str:
    if dia is None:
        return "el próximo reparto"
    return f"{('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo')[dia.weekday()]} {dia.strftime('%d/%m')}"


def _banda(banda, unidad, stock) -> str:
    if not banda["listo"]:
        if float(stock or 0) <= 0:
            return " Sin historial no hay pico, mínimo ni máximo. No se pide a ciegas."
        return " Pico, mínimo y máximo histórico: el sistema todavía no los definió."
    return (
        f" Pico viejo {_txt(banda['pico'])} {unidad} por día, no se compra."
        f" Mínimo histórico {_txt(banda['minimo'])}."
        f" Máximo histórico {_txt(banda['maximo'])}."
    )


def _txt(numero) -> str:
    return f"{float(numero):.2f}".rstrip("0").rstrip(".")


def _stock(db) -> dict | None:
    """Pollo en cajas, carne en medias, cerdo y congelado en kilos, huevo en cajones."""
    if db is None:
        return None
    salida = {}
    try:
        from src.proveedor_global.frontend.formula.motores.caja_pollo import consultar as pollo
        from src.proveedor_global.frontend.formula.motores.carne_stock import consultar as carne
        salida["pollo"] = float((pollo(db) or {}).get("enteras") or 0)
        kilos = float((carne(db, "Media res") or {}).get("stock") or 0)
        salida["media"] = round(kilos / 75, 2) if kilos else 0.0
    except Exception:
        return None
    for nombre, clave in (("Cerdo", "cerdo"), ("Congelado", "congelado")):
        try:
            from src.proveedor_global.frontend.formula.motores.carne_stock import consultar as carne
            salida[clave] = round(float((carne(db, nombre) or {}).get("stock") or 0), 2)
        except Exception:
            continue
    huevo = _huevo(db)
    if huevo is not None:
        salida["huevo"] = huevo
    return salida


def _huevo(db):
    """Lee los cajones si la tabla ya existe. No la crea."""
    try:
        filas = db.execute_query(
            "SELECT cajones FROM formula_verdad WHERE modulo = ? LIMIT 1",
            ("Huevo",),
        ) or []
    except Exception:
        return None
    if not filas:
        return 0.0
    fila = filas[0]
    try:
        if isinstance(fila, dict):
            return round(float(fila.get("cajones") or 0), 2)
        return round(float(fila[0] or 0), 2)
    except (TypeError, ValueError, IndexError, KeyError):
        return None
