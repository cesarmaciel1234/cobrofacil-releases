"""Venta cruzada: productos que salen juntos en el mismo ticket."""

from __future__ import annotations

import logging

logger = logging.getLogger("VentaCruzada")

BASURA = ("articulo comun", "venta libre", "cobro rapido")


def _norm(nombre):
    texto = str(nombre or "").lower().strip()
    return texto.translate(str.maketrans("áéíóúüñ", "aeiouun"))


def _es_basura(nombre):
    texto = _norm(nombre)
    return any(marca in texto for marca in BASURA)


def _nombre_fila(row, *keys):
    if isinstance(row, dict):
        for key in keys:
            if row.get(key) not in (None, ""):
                return str(row.get(key)).strip()
        vals = list(row.values())
        return str(vals[0]).strip() if vals else ""
    return str(row[0] if row else "").strip()


def _titulo_pregunta(nombre):
    texto = str(nombre or "").strip()
    if texto.lower().startswith("oferta "):
        texto = texto[7:].strip()
    return texto.upper() if texto else "ESTO"


class VentaCruzadaInteligente:
    """Garantiza 3 acompañantes: primero co-ocurrencia de tickets, después catálogo."""

    @staticmethod
    def _buscar_catalogo(catalogo, nombre):
        clave = _norm(nombre)
        if not clave:
            return None
        if clave in catalogo:
            return catalogo[clave]
        for key, prod in catalogo.items():
            if len(clave) >= 4 and (clave in key or key in clave):
                return prod
        return None

    @staticmethod
    def obtener_relacionados_para_ticket(producto_base, limit=3, catalogo=None):
        nombres = VentaCruzadaInteligente._desde_tickets(producto_base, limit * 4)
        if catalogo:
            resueltos = []
            vistos = {_norm(producto_base)}
            for nom in nombres:
                prod = VentaCruzadaInteligente._buscar_catalogo(catalogo, nom)
                if not prod:
                    continue
                clave = _norm(prod.get("nombre"))
                if clave in vistos:
                    continue
                vistos.add(clave)
                resueltos.append(prod.get("nombre") or nom)
            nombres = resueltos
        if len(nombres) < limit:
            extra = VentaCruzadaInteligente._desde_catalogo(producto_base, catalogo or {}, limit * 3)
            vistos = {_norm(n) for n in nombres}
            vistos.add(_norm(producto_base))
            for nom in extra:
                if _norm(nom) in vistos:
                    continue
                nombres.append(nom)
                vistos.add(_norm(nom))
                if len(nombres) >= limit:
                    break
        while len(nombres) < limit:
            extra = VentaCruzadaInteligente._desde_catalogo(producto_base, catalogo or {}, limit * 6)
            usados = {_norm(n) for n in nombres}
            usados.add(_norm(producto_base))
            agregado = False
            for nom in extra:
                if _norm(nom) in usados:
                    continue
                nombres.append(nom)
                usados.add(_norm(nom))
                agregado = True
                if len(nombres) >= limit:
                    break
            if not agregado:
                break
        return nombres[:limit]

    @staticmethod
    def _desde_tickets(producto_base, limit=8):
        nombre = str(producto_base or "").strip()
        if not nombre or _es_basura(nombre):
            return []
        try:
            from src.base_de_datos.database import db_manager
            query = """
                SELECT dv2.nombre_producto, COUNT(*) AS veces
                FROM detalles_ventas dv1
                JOIN detalles_ventas dv2 ON dv1.id_venta = dv2.id_venta
                JOIN ventas v ON dv1.id_venta = v.id
                WHERE LOWER(dv1.nombre_producto) = LOWER(?)
                  AND LOWER(dv2.nombre_producto) != LOWER(?)
                  AND COALESCE(v.estado, '') != 'CANCELADA'
                GROUP BY dv2.nombre_producto
                ORDER BY veces DESC
                LIMIT ?
            """
            rows = db_manager.execute_query(query, (nombre, nombre, limit)) or []
        except Exception as exc:
            logger.debug("Tickets de venta cruzada no disponibles: %s", exc)
            return []
        out = []
        vistos = set()
        for row in rows:
            nom = _nombre_fila(row, "nombre_producto", "nombre")
            clave = _norm(nom)
            if not nom or _es_basura(nom) or clave in vistos:
                continue
            vistos.add(clave)
            out.append(nom)
        return out

    @staticmethod
    def _desde_catalogo(producto_base, catalogo, limit=6):
        base = catalogo.get(_norm(producto_base)) if catalogo else None
        depto = _norm((base or {}).get("departamento") or (base or {}).get("categoria") or "")
        mismos = []
        otros = []
        for clave, prod in (catalogo or {}).items():
            if clave == _norm(producto_base) or _es_basura(prod.get("nombre")):
                continue
            nom = prod.get("nombre") or ""
            if not nom:
                continue
            rubro = _norm(prod.get("departamento") or prod.get("categoria") or "")
            if depto and rubro == depto:
                mismos.append(nom)
            else:
                otros.append(nom)
        return (mismos + otros)[:limit]

    @staticmethod
    def armar_slides(productos, limite=4):
        catalogo = {}
        for item in productos or []:
            clave = _norm(item.get("nombre"))
            if clave and not _es_basura(item.get("nombre")):
                catalogo[clave] = item

        bases = []
        try:
            from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import MotorVentas
            ranking = MotorVentas.get_top_ventas(limit=limite + 6, periodo="hoy", modo="frecuencia") or []
            if not ranking:
                ranking = MotorVentas.get_top_ventas(limit=limite + 6, periodo="semana", modo="frecuencia") or []
            for item in ranking:
                nom = str(item.get("nombre") or "").strip()
                prod = catalogo.get(_norm(nom))
                if prod:
                    bases.append(prod)
        except Exception as exc:
            logger.debug("MotorVentas no disponible para cruzada: %s", exc)

        if len(bases) < limite:
            for item in productos or []:
                if _es_basura(item.get("nombre")):
                    continue
                if item not in bases:
                    bases.append(item)
                if len(bases) >= limite:
                    break

        slides = []
        vistos = set()
        for prod in bases:
            nombre = prod.get("nombre") or ""
            clave = _norm(nombre)
            if not clave or clave in vistos:
                continue
            relacionados = VentaCruzadaInteligente.obtener_relacionados_para_ticket(
                nombre, limit=3, catalogo=catalogo,
            )
            if not relacionados:
                continue
            while len(relacionados) < 3:
                extra = VentaCruzadaInteligente._desde_catalogo(nombre, catalogo, 8)
                usados = {_norm(nombre), *(_norm(n) for n in relacionados)}
                mas = [n for n in extra if _norm(n) not in usados]
                if not mas:
                    break
                relacionados.append(mas[0])
            if not relacionados:
                continue
            vistos.add(clave)
            slides.append({
                "tipo": "cruzada",
                "nombre": nombre,
                "pregunta": f"¿LLEVÁS {_titulo_pregunta(nombre)}?",
                "relacionados": [str(n).upper() for n in relacionados[:3]],
            })
            if len(slides) >= limite:
                break
        return slides
