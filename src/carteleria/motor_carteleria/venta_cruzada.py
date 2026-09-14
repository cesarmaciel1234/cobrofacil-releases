"""Venta cruzada: co-ocurrencia real en tickets, con recencia y confianza."""

from __future__ import annotations

import logging
import time
from collections import defaultdict

logger = logging.getLogger("VentaCruzada")

BASURA = ("articulo comun", "venta libre", "cobro rapido")
CACHE_TTL_S = 15 * 60
PESO_30D = 4.0
PESO_90D = 2.0
PESO_365D = 1.0
PESO_VIEJO = 0.35
MIN_VECES_FIRME = 2

_CACHE = {"firma": None, "expira": 0.0, "pares": {}, "conteo": {}, "tickets": 0}


def _norm(nombre):
    texto = str(nombre or "").lower().strip()
    texto = texto.translate(str.maketrans("áéíóúüñ", "aeiouun"))
    if texto.startswith("oferta "):
        texto = texto[7:].strip()
    return " ".join(texto.split())


def _es_basura(nombre):
    texto = _norm(nombre)
    return not texto or any(marca in texto for marca in BASURA)


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


def _peso_fecha(fecha, ahora_ts):
    try:
        from datetime import datetime
        if hasattr(fecha, "timestamp"):
            ts = fecha.timestamp()
        else:
            raw = str(fecha or "")[:19]
            ts = datetime.fromisoformat(raw.replace(" ", "T")).timestamp()
    except Exception:
        return PESO_365D
    dias = max(0.0, (ahora_ts - ts) / 86400.0)
    if dias <= 30:
        return PESO_30D
    if dias <= 90:
        return PESO_90D
    if dias <= 365:
        return PESO_365D
    return PESO_VIEJO


class VentaCruzadaInteligente:
    """Acompañantes por estadística de tickets. El catálogo solo rellena si aún no hay historia."""

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
    def _firma_db():
        try:
            from src.base_de_datos.database import db_manager
            rows = db_manager.execute_query(
                "SELECT COUNT(*), COALESCE(MAX(id), 0) FROM ventas WHERE COALESCE(estado, '') != 'CANCELADA'"
            ) or []
            row = rows[0]
            if isinstance(row, dict):
                vals = list(row.values())
                return (int(vals[0] or 0), int(vals[1] or 0))
            return (int(row[0] or 0), int(row[1] or 0))
        except Exception:
            return (0, 0)

    @staticmethod
    def _matriz():
        ahora = time.time()
        firma = VentaCruzadaInteligente._firma_db()
        if _CACHE["pares"] and _CACHE["firma"] == firma and ahora < _CACHE["expira"]:
            return _CACHE
        pares = defaultdict(lambda: defaultdict(float))
        conteo = defaultdict(float)
        tickets_ok = 0
        try:
            from src.base_de_datos.database import db_manager
            rows = db_manager.execute_query(
                """
                SELECT dv.id_venta, dv.nombre_producto, v.fecha
                FROM detalles_ventas dv
                JOIN ventas v ON v.id = dv.id_venta
                WHERE COALESCE(v.estado, '') != 'CANCELADA'
                ORDER BY dv.id_venta
                """
            ) or []
        except Exception as exc:
            logger.debug("Tickets de venta cruzada no disponibles: %s", exc)
            rows = []

        por_ticket = defaultdict(list)
        fechas = {}
        for row in rows:
            if isinstance(row, dict):
                vid = row.get("id_venta")
                nom = row.get("nombre_producto")
                fecha = row.get("fecha")
            else:
                vid = row[0] if len(row) > 0 else None
                nom = row[1] if len(row) > 1 else ""
                fecha = row[2] if len(row) > 2 else None
            clave = _norm(nom)
            if vid is None or _es_basura(nom) or not clave:
                continue
            por_ticket[vid].append(clave)
            fechas[vid] = fecha

        for vid, claves in por_ticket.items():
            unicos = list(dict.fromkeys(claves))
            if len(unicos) < 2:
                continue
            tickets_ok += 1
            peso = _peso_fecha(fechas.get(vid), ahora)
            for a in unicos:
                conteo[a] += peso
            for i, a in enumerate(unicos):
                for b in unicos[i + 1:]:
                    pares[a][b] += peso
                    pares[b][a] += peso

        _CACHE.update({
            "firma": firma,
            "expira": ahora + CACHE_TTL_S,
            "pares": {k: dict(v) for k, v in pares.items()},
            "conteo": dict(conteo),
            "tickets": tickets_ok,
        })
        logger.info(
            "Cruzada: %s tickets con 2+ productos, %s ítems en matriz",
            tickets_ok,
            len(conteo),
        )
        return _CACHE

    @staticmethod
    def _claves_base(nombre, claves_matriz):
        n = _norm(nombre)
        if not n:
            return []
        hits = []
        if n in claves_matriz:
            hits.append(n)
        for k in claves_matriz:
            if k == n:
                continue
            if len(n) >= 4 and (n in k or k in n):
                hits.append(k)
        return hits or ([n] if n else [])

    @staticmethod
    def _desde_tickets(producto_base, limit=8):
        mat = VentaCruzadaInteligente._matriz()
        pares = mat["pares"]
        conteo = mat["conteo"]
        scores = defaultdict(float)
        for clave in VentaCruzadaInteligente._claves_base(producto_base, pares.keys()):
            for otro, peso in (pares.get(clave) or {}).items():
                scores[otro] += peso
        if not scores:
            return []
        min_peso = MIN_VECES_FIRME if mat["tickets"] >= 20 else 0.3
        ranked = []
        for otro, peso in scores.items():
            if peso < min_peso:
                continue
            base_c = max(
                (conteo.get(c, 0.0) for c in VentaCruzadaInteligente._claves_base(producto_base, conteo.keys())),
                default=0.0,
            )
            lift = peso / base_c if base_c else 0.0
            ranked.append((peso, lift, otro))
        ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [nom for _p, _l, nom in ranked[:limit]]

    @staticmethod
    def hay_ventas_reales():
        """True en cuanto existe al menos un ticket no cancelado."""
        count, _max_id = VentaCruzadaInteligente._firma_db()
        return count > 0

    @staticmethod
    def usar_relleno_catalogo():
        """PC nueva / sin ventas: completar con catálogo. Se apaga al primer ticket."""
        return not VentaCruzadaInteligente.hay_ventas_reales()

    @staticmethod
    def obtener_relacionados_para_ticket(producto_base, limit=3, catalogo=None):
        nombres_raw = VentaCruzadaInteligente._desde_tickets(producto_base, limit * 6)
        nombres = []
        vistos = {_norm(producto_base)}
        for nom in nombres_raw:
            etiqueta = nom
            if catalogo:
                prod = VentaCruzadaInteligente._buscar_catalogo(catalogo, nom)
                if not prod:
                    continue
                etiqueta = prod.get("nombre") or nom
            clave = _norm(etiqueta)
            if clave in vistos:
                continue
            vistos.add(clave)
            nombres.append(etiqueta)
            if len(nombres) >= limit:
                break
        if len(nombres) < limit and VentaCruzadaInteligente.usar_relleno_catalogo():
            extra = VentaCruzadaInteligente._desde_catalogo(producto_base, catalogo or {}, limit * 3)
            for nom in extra:
                if _norm(nom) in vistos:
                    continue
                nombres.append(nom)
                vistos.add(_norm(nom))
                if len(nombres) >= limit:
                    break
        return nombres[:limit]

    @staticmethod
    def _tiene_foto(prod):
        return bool((prod or {}).get("icono") or (prod or {}).get("icono_url"))

    @staticmethod
    def _desde_catalogo(producto_base, catalogo, limit=6):
        """Solo ítems reales del inventario, mismo rubro, con foto primero."""
        base = catalogo.get(_norm(producto_base)) if catalogo else None
        if not base:
            base = VentaCruzadaInteligente._buscar_catalogo(catalogo, producto_base)
        depto = _norm((base or {}).get("departamento") or (base or {}).get("categoria") or "")
        if not depto:
            return []
        mismos = []
        for clave, prod in (catalogo or {}).items():
            if clave == _norm(producto_base) or _es_basura(prod.get("nombre")):
                continue
            nom = str(prod.get("nombre") or "").strip()
            if not nom:
                continue
            rubro = _norm(prod.get("departamento") or prod.get("categoria") or "")
            if rubro != depto:
                continue
            mismos.append(prod)
        mismos.sort(key=lambda p: (0 if VentaCruzadaInteligente._tiene_foto(p) else 1, _norm(p.get("nombre"))))
        return [p.get("nombre") for p in mismos if p.get("nombre")][:limit]

    @staticmethod
    def armar_slides(productos, limite=4):
        catalogo = {}
        for item in productos or []:
            clave = _norm(item.get("nombre"))
            if clave and not _es_basura(item.get("nombre")):
                catalogo[clave] = item

        VentaCruzadaInteligente._matriz()
        relleno = VentaCruzadaInteligente.usar_relleno_catalogo()

        bases = []
        try:
            from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import MotorVentas
            ranking = MotorVentas.get_top_ventas(limit=limite + 8, periodo="semana", modo="frecuencia") or []
            if not ranking:
                ranking = MotorVentas.get_top_ventas(limit=limite + 8, periodo="hoy", modo="frecuencia") or []
            for item in ranking:
                nom = str(item.get("nombre") or "").strip()
                prod = catalogo.get(_norm(nom)) or VentaCruzadaInteligente._buscar_catalogo(catalogo, nom)
                if prod and prod not in bases:
                    bases.append(prod)
        except Exception as exc:
            logger.debug("MotorVentas no disponible para cruzada: %s", exc)

        if len(bases) < limite and relleno:
            con_foto = []
            resto = []
            for item in productos or []:
                if _es_basura(item.get("nombre")):
                    continue
                if item in bases:
                    continue
                (con_foto if VentaCruzadaInteligente._tiene_foto(item) else resto).append(item)
            for item in con_foto + resto:
                bases.append(item)
                if len(bases) >= limite + 4:
                    break

        slides = []
        vistos = set()
        min_rel = 2 if relleno else 1
        for prod in bases:
            nombre = prod.get("nombre") or ""
            clave = _norm(nombre)
            if not clave or clave in vistos:
                continue
            relacionados = VentaCruzadaInteligente.obtener_relacionados_para_ticket(
                nombre, limit=3, catalogo=catalogo,
            )
            if len(relacionados) < min_rel:
                continue
            vistos.add(clave)
            slides.append({
                "tipo": "cruzada",
                "nombre": nombre,
                "pregunta": f"¿LLEVÁS {_titulo_pregunta(nombre)}?",
                "relacionados": [str(n).upper() for n in relacionados[:3]],
                "fuente": "catalogo" if relleno else "tickets",
            })
            if len(slides) >= limite:
                break
        return slides
