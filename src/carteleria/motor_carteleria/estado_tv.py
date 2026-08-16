"""Arma el estado de la TV con los motores reales del TPV.

No inventa precios, combos ni scores: solo traduce lo que ya existe
en publicidad, ofertas, combos, ventas e IA local.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger("EstadoTV")


def num(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def es_oferta(producto):
    precio = num(producto.get("precio"))
    oferta = num(producto.get("precio_oferta"))
    return precio > 0 and oferta > 0 and oferta < precio


def precio_vigente(producto):
    if es_oferta(producto):
        return num(producto.get("precio_oferta"))
    relampago = num(producto.get("precio_oferta_relampago"))
    precio = num(producto.get("precio"))
    if relampago > 0 and (precio <= 0 or relampago < precio):
        return relampago
    return precio


def _as_dict(row, keys):
    if isinstance(row, dict):
        return row
    if isinstance(row, (list, tuple)):
        return {key: row[i] if i < len(row) else None for i, key in enumerate(keys)}
    return {}


def _norm_nombre(nombre):
    texto = str(nombre or "").lower().strip()
    return texto.translate(str.maketrans("áéíóúüñ", "aeiouun"))


def _nombre_basura(nombre):
    texto = _norm_nombre(nombre)
    return any(marca in texto for marca in ("articulo comun", "venta libre", "cobro rapido"))


def _catalogo_por_nombre(productos):
    out = {}
    for item in productos:
        clave = _norm_nombre(item.get("nombre"))
        if clave:
            out[clave] = item
    return out


def _buscar_en_catalogo(catalogo, nombre):
    clave = _norm_nombre(nombre)
    if not clave:
        return None
    if clave in catalogo:
        return catalogo[clave]
    for key, prod in catalogo.items():
        if len(clave) >= 4 and (clave in key or key in clave):
            return prod
    return None


def _fmt_cantidad(valor):
    n = num(valor)
    if n <= 0:
        return ""
    if abs(n - round(n)) < 0.05:
        return str(int(round(n)))
    return f"{n:.1f}".replace(".", ",")


def _fmt_plata(valor):
    n = num(valor)
    if n <= 0:
        return ""
    return f"${int(round(n)):,}".replace(",", ".")


def _mapa_ventas(modo="volumen", limite=400):
    """Ranking real de la tabla ventas. Hoy, y si no hay, la semana."""
    periodo = "hoy"
    ranking = []
    try:
        from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import MotorVentas
        ranking = MotorVentas.get_top_ventas(limit=limite, periodo="hoy", modo=modo) or []
        if not ranking:
            ranking = MotorVentas.get_top_ventas(limit=limite, periodo="semana", modo=modo) or []
            periodo = "semana"
    except Exception as exc:
        logger.debug("MotorVentas (%s) no disponible: %s", modo, exc)
    mapa = {}
    for item in ranking:
        clave = _norm_nombre(item.get("nombre"))
        if not clave or _nombre_basura(item.get("nombre")):
            continue
        mapa[clave] = {
            "cantidad": num(item.get("cantidad")),
            "recaudacion": num(item.get("recaudacion")),
            "periodo": periodo,
        }
    return mapa, periodo


def _enriquecer_con_ventas(productos):
    """Pega kilos/unidades vendidas en cada producto del catálogo."""
    vol, periodo = _mapa_ventas("volumen")
    for item in productos or []:
        data = vol.get(_norm_nombre(item.get("nombre"))) or {}
        item["cantidad"] = data.get("cantidad") or 0
        item["recaudacion"] = data.get("recaudacion") or 0
        item["periodo_ventas"] = data.get("periodo") or periodo
    return productos


def _card_desde_catalogo(prod, badge, detalle="", puesto=0, cantidad=0, periodo="hoy", recaudacion=0):
    return {
        "id": prod.get("id"),
        "nombre": prod.get("nombre") or "",
        "precio": num(prod.get("precio")),
        "precio_oferta": num(prod.get("precio_oferta")),
        "precio_oferta_relampago": num(prod.get("precio_oferta_relampago")),
        "cant_oferta": num(prod.get("cant_oferta")),
        "tipo_unidad_oferta": prod.get("tipo_unidad_oferta") or "",
        "unidad": prod.get("unidad") or "",
        "es_pesable": prod.get("es_pesable") or 0,
        "departamento": prod.get("departamento") or prod.get("categoria") or "",
        "categoria": prod.get("categoria") or "",
        "es_publicidad": bool(prod.get("es_publicidad")),
        "icono": prod.get("icono") or "",
        "icono_url": prod.get("icono_url") or "",
        "badge": badge,
        "detalle": detalle,
        "puesto": puesto,
        "cantidad": num(cantidad),
        "recaudacion": num(recaudacion),
        "periodo": periodo,
    }


def _top_con_precios(productos, modo, badge, detalle_hoy, detalle_semana, limite=5, orden="cantidad"):
    """Solo productos que aparecen en ventas reales, cruzados con el catálogo."""
    periodo = "hoy"
    try:
        from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import MotorVentas
        ranking = MotorVentas.get_top_ventas(limit=max(limite * 4, 20), periodo="hoy", modo=modo) or []
        if not ranking:
            ranking = MotorVentas.get_top_ventas(limit=max(limite * 4, 20), periodo="semana", modo=modo) or []
            periodo = "semana"
    except Exception as exc:
        logger.debug("MotorVentas (%s) no disponible: %s", modo, exc)
        ranking = []

    ranking = sorted(ranking, key=lambda item: num(item.get(orden)), reverse=True)
    catalogo = _catalogo_por_nombre(productos)
    plantilla = detalle_hoy if periodo == "hoy" else detalle_semana
    cards = []
    vistos = set()
    for item in ranking:
        nombre = str(item.get("nombre") or "").strip()
        if not nombre or _nombre_basura(nombre):
            continue
        prod = _buscar_en_catalogo(catalogo, nombre)
        if not prod:
            continue
        clave = _norm_nombre(prod.get("nombre"))
        if clave in vistos:
            continue
        vistos.add(clave)
        cantidad = num(item.get("cantidad"))
        recaudacion = num(item.get("recaudacion"))
        valor = recaudacion if orden == "recaudacion" else cantidad
        if valor <= 0:
            continue
        dato = _fmt_plata(recaudacion) if orden == "recaudacion" else _fmt_cantidad(cantidad)
        cards.append(_card_desde_catalogo(
            prod, badge, plantilla.format(n=dato),
            puesto=len(cards) + 1, cantidad=cantidad, periodo=periodo, recaudacion=recaudacion,
        ))
        if len(cards) >= limite:
            break
    return cards, periodo


def armar_destacados(productos):
    """Top real de tickets para el hero."""
    cards, _ = _top_con_precios(
        productos, "frecuencia", "ELEGIDO",
        "{n} tickets hoy", "{n} tickets esta semana",
        limite=8,
    )
    return cards


def armar_rotacion_destacados(productos):
    """Tres tandas reales: tickets, kilos y recaudación."""
    paneles = []
    elegidos, periodo_e = _top_con_precios(
        productos, "frecuencia", "ELEGIDO",
        "{n} tickets hoy", "{n} tickets esta semana",
        limite=5,
    )
    if elegidos:
        paneles.append({
            "id": "elegidos",
            "titulo": "Más vendidos",
            "subtitulo": "En tickets" if periodo_e == "hoy" else "Tickets semana",
            "items": elegidos,
        })

    volumen, periodo_v = _top_con_precios(
        productos, "volumen", "VOLUMEN",
        "{n} vendidos hoy", "{n} vendidos esta semana",
        limite=5,
    )
    if volumen:
        paneles.append({
            "id": "volumen",
            "titulo": "Mega volumen",
            "subtitulo": "En kilos" if periodo_v == "hoy" else "Kilos semana",
            "items": volumen,
        })

    plata, periodo_p = _top_con_precios(
        productos, "volumen", "PLATA",
        "{n} hoy", "{n} esta semana",
        limite=5, orden="recaudacion",
    )
    if plata:
        paneles.append({
            "id": "plata",
            "titulo": "Más plata",
            "subtitulo": "En ventas" if periodo_p == "hoy" else "Ventas semana",
            "items": plata,
        })
    return paneles


def armar_combos(productos):
    """Combos cargados en el TPV. Si no hay, muestra ofertas reales (2x / precio oferta)."""
    combos = _combos_del_motor(productos)
    if combos:
        return combos
    return _ofertas_como_combo(productos)


def _ofertas_flash(productos, limite=4):
    cards = []
    for item in productos or []:
        if not es_oferta(item):
            continue
        cards.append({
            "tipo": "oferta",
            "nombre": item.get("nombre") or "Oferta",
            "precio": num(item.get("precio_oferta")),
            "precio_original": num(item.get("precio")),
            "ahorro": num(item.get("precio")) - num(item.get("precio_oferta")),
            "cant_oferta": num(item.get("cant_oferta")),
            "tipo_unidad_oferta": item.get("tipo_unidad_oferta") or "",
            "unidad": item.get("unidad") or "",
            "es_pesable": item.get("es_pesable") or 0,
            "departamento": item.get("departamento") or item.get("categoria") or "",
            "icono": item.get("icono") or "",
            "icono_url": item.get("icono_url") or "",
        })
        if len(cards) >= limite:
            break
    return cards


def armar_columna3(productos):
    """TV3: venta cruzada del motor intercalada con ofertas relámpago."""
    try:
        from src.carteleria.motor_carteleria.venta_cruzada import VentaCruzadaInteligente
        cruzadas = VentaCruzadaInteligente.armar_slides(productos, limite=4)
    except Exception as exc:
        logger.debug("Venta cruzada no disponible: %s", exc)
        cruzadas = []
    if not cruzadas:
        cruzadas = _cruzadas_desde_catalogo(productos, limite=4)
    ofertas = _ofertas_flash(productos, limite=4)
    slides = []
    n = max(len(cruzadas), len(ofertas), 1)
    for i in range(n):
        if cruzadas:
            slides.append(cruzadas[i % len(cruzadas)])
        if ofertas:
            slides.append(ofertas[i % len(ofertas)])
        if not cruzadas and not ofertas:
            break
        if len(slides) >= 8:
            break
    return slides


def _cruzadas_desde_catalogo(productos, limite=4):
    grupos = {}
    for item in productos or []:
        nombre = str(item.get("nombre") or "").strip()
        if not nombre:
            continue
        depto = str(item.get("departamento") or item.get("categoria") or "GENERAL").upper()
        grupos.setdefault(depto, []).append(nombre)
    slides = []
    vistos = set()
    for item in productos or []:
        nombre = str(item.get("nombre") or "").strip()
        if not nombre or nombre in vistos:
            continue
        depto = str(item.get("departamento") or item.get("categoria") or "GENERAL").upper()
        mates = [n for n in grupos.get(depto, []) if n != nombre][:3]
        if len(mates) < 2:
            continue
        vistos.add(nombre)
        titulo = nombre[7:].strip() if nombre.lower().startswith("oferta ") else nombre
        slides.append({
            "tipo": "cruzada",
            "nombre": nombre,
            "pregunta": f"¿LLEVÁS {titulo.upper()}?",
            "relacionados": [str(n).upper() for n in mates],
            "icono": item.get("icono") or "",
            "icono_url": item.get("icono_url") or "",
            "departamento": item.get("departamento") or item.get("categoria") or "",
        })
        if len(slides) >= limite:
            break
    return slides


def _combos_del_motor(productos):
    try:
        from src.motor_descuentos.cerebro.motor_combos import MotorCombos
        motor = MotorCombos()
        motor.inicializar_tabla()
        filas = motor.obtener_combos() or []
    except Exception as exc:
        logger.debug("MotorCombos no disponible: %s", exc)
        return []

    catalogo = _catalogo_por_nombre(productos)
    resultado = []
    for fila in filas:
        row = _as_dict(fila, ("id", "nombre", "precio_combo", "productos_json"))
        nombre = str(row.get("nombre") or "").strip()
        precio = num(row.get("precio_combo"))
        if not nombre or precio <= 0:
            continue
        piezas = _parsear_productos_combo(row.get("productos_json"))
        original = 0.0
        etiquetas = []
        for pieza in piezas:
            cant = num(pieza.get("cantidad"), 1) or 1
            nom = str(pieza.get("nombre") or "").strip()
            if nom:
                etiquetas.append(f"{int(cant) if cant == int(cant) else cant}x {nom}")
            prod = catalogo.get(nom.lower()) or _buscar_en_catalogo(catalogo, nom)
            if prod:
                original += num(prod.get("precio")) * cant
        ahorro = original - precio if original > precio else 0.0
        resultado.append({
            "nombre": nombre,
            "precio": precio,
            "precio_original": original if original > precio else 0.0,
            "ahorro": ahorro,
            "productos": " + ".join(etiquetas) if etiquetas else nombre,
            "origen": "combo",
        })
        if len(resultado) >= 4:
            break
    return resultado


def _parsear_productos_combo(raw):
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if not raw:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def _ofertas_como_combo(productos):
    cards = []
    for item in productos:
        if not es_oferta(item):
            continue
        cant = num(item.get("cant_oferta"))
        precio = num(item.get("precio_oferta"))
        original = num(item.get("precio"))
        if cant > 1:
            detalle = f"Llevá {int(cant)} · {item.get('nombre')}"
        else:
            detalle = item.get("nombre") or "Oferta"
        cards.append({
            "nombre": item.get("nombre") or "Oferta",
            "precio": precio,
            "precio_original": original,
            "ahorro": original - precio if original > precio else 0.0,
            "productos": detalle,
            "cant_oferta": cant,
            "tipo_unidad_oferta": item.get("tipo_unidad_oferta") or "",
            "unidad": item.get("unidad") or "",
            "es_pesable": item.get("es_pesable") or 0,
            "departamento": item.get("departamento") or item.get("categoria") or "",
            "icono": item.get("icono") or "",
            "icono_url": item.get("icono_url") or "",
            "origen": "oferta",
        })
        if len(cards) >= 4:
            break
    return cards


def armar_ia(productos, clima_icon="sol", clima_text=""):
    """IA Chef: top de ventas de hoy + recomendación del motor local."""
    cards = []
    vistos = set()
    catalogo = _catalogo_por_nombre(productos)

    try:
        from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import MotorVentas
        for item in MotorVentas.get_top_ventas(limit=4, periodo="hoy") or []:
            nombre = str(item.get("nombre") or "").strip()
            prod = _buscar_en_catalogo(catalogo, nombre)
            if not prod:
                continue
            vistos.add(_norm_nombre(nombre))
            cards.append({
                "nombre": prod["nombre"],
                "precio": precio_vigente(prod),
                "precio_lista": num(prod.get("precio")),
                "razon": "Más vendido hoy",
                "icono": prod.get("icono") or "",
                "icono_url": prod.get("icono_url") or "",
                "departamento": prod.get("departamento") or "",
            })
    except Exception as exc:
        logger.debug("MotorVentas no disponible: %s", exc)

    try:
        from src.cerebro_global.carteleria_cerebro.motor_ia_local import MotorIALocal
        muestra = [(p.get("nombre"), p.get("precio"), p.get("precio_oferta")) for p in productos[:30]]
        mensaje, estrella, precio, poferta = MotorIALocal.generar_recomendacion_lobo(
            (clima_icon or "sol", clima_text or ""),
            muestra,
        )
        clave = _norm_nombre(estrella)
        if clave and clave not in vistos and estrella:
            prod = _buscar_en_catalogo(catalogo, estrella)
            cards.insert(0, {
                "nombre": prod["nombre"] if prod else str(estrella),
                "precio": precio_vigente(prod) if prod else num(poferta) or num(precio),
                "precio_lista": num(prod.get("precio")) if prod else num(precio),
                "razon": str(mensaje or "Recomendado ahora"),
                "icono": (prod or {}).get("icono") or "",
                "icono_url": (prod or {}).get("icono_url") or "",
                "departamento": (prod or {}).get("departamento") or "",
            })
            vistos.add(clave)
    except Exception as exc:
        logger.debug("MotorIALocal no disponible: %s", exc)

    if not cards:
        for item in productos:
            if not es_oferta(item):
                continue
            cards.append({
                "nombre": item.get("nombre") or "Oferta",
                "precio": precio_vigente(item),
                "precio_lista": num(item.get("precio")),
                "razon": "En oferta ahora",
                "icono": item.get("icono") or "",
                "icono_url": item.get("icono_url") or "",
                "departamento": item.get("departamento") or "",
            })
            if len(cards) >= 4:
                break

    return cards[:4]


def armar_hero(destacados, productos):
    if destacados:
        return destacados[0]
    if productos:
        return productos[0]
    return None


def armar_paneles(productos, clima_icon="sol", clima_text=""):
    from src.carteleria.motor_carteleria.iconos_tv import enriquecer_iconos
    productos = enriquecer_iconos(_enriquecer_con_ventas(productos))
    rotacion = armar_rotacion_destacados(productos)
    destacados = rotacion[0]["items"] if rotacion else armar_destacados(productos)
    hero = armar_hero(destacados, productos)
    return {
        "hero": hero,
        "destacados": destacados[:4],
        "rotacion": rotacion,
        "combos": armar_combos(productos),
        "columna3": armar_columna3(productos),
        "ia": armar_ia(productos, clima_icon, clima_text),
        "precios": productos,
    }
