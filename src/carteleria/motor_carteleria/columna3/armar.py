"""Arma los slides de la columna 3. No toca la pantalla."""

from __future__ import annotations

import logging

logger = logging.getLogger("EstadoTV")


def armar_columna3(productos, ranking_remoto=None):
    """Pares del mismo ticket, intercalados con ofertas relámpago.

    El ranking de lo más vendido no reemplaza esta cuenta. El rubro
    del catálogo solo aparece si todavía no hay ningún ticket.
    """
    del ranking_remoto
    cruzadas = []
    sin_historia = True
    try:
        from src.carteleria.motor_carteleria.venta_cruzada import VentaCruzadaInteligente

        cruzadas = VentaCruzadaInteligente.armar_slides(productos, limite=4)
        sin_historia = VentaCruzadaInteligente.usar_relleno_catalogo()
    except Exception as exc:
        logger.debug("Venta cruzada no disponible: %s", exc)
        cruzadas = []
        sin_historia = True
    if not cruzadas and sin_historia:
        cruzadas = cruzadas_desde_catalogo(productos, limite=4)
    from src.carteleria.motor_carteleria.estado_tv import _ofertas_flash

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


def cruzadas_desde_catalogo(productos, limite=4):
    """Solo el rubro cargado. No es la cuenta de tickets."""
    from src.carteleria.motor_carteleria.estado_tv import _nombre_basura, _tiene_foto

    grupos = {}
    for item in productos or []:
        nombre = str(item.get("nombre") or "").strip()
        if not nombre or _nombre_basura(nombre):
            continue
        depto = str(item.get("departamento") or item.get("categoria") or "").strip().upper()
        if not depto:
            continue
        grupos.setdefault(depto, []).append(item)
    slides = []
    vistos = set()
    for depto, items in grupos.items():
        if len(items) < 3:
            continue
        items = sorted(items, key=lambda p: (0 if _tiene_foto(p) else 1, str(p.get("nombre") or "")))
        for item in items:
            nombre = str(item.get("nombre") or "").strip()
            if nombre in vistos:
                continue
            mates = [
                str(p.get("nombre") or "").strip()
                for p in items
                if str(p.get("nombre") or "").strip() and str(p.get("nombre") or "").strip() != nombre
            ][:3]
            if len(mates) < 2:
                continue
            vistos.add(nombre)
            titulo = nombre[7:].strip() if nombre.lower().startswith("oferta ") else nombre
            slides.append({
                "tipo": "cruzada",
                "nombre": nombre,
                "pregunta": f"¿LLEVÁS {titulo.upper()}?",
                "relacionados": [n.upper() for n in mates],
                "icono": item.get("icono") or "",
                "icono_url": item.get("icono_url") or "",
                "departamento": depto,
                "fuente": "inventario",
            })
            if len(slides) >= limite:
                return slides
    return slides
