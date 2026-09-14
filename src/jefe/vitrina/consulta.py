"""Ofertas de vitrina. Precio real + uno menor = oferta. No inventa."""

from __future__ import annotations


def _num(v) -> float:
    try:
        if v is None or v == "":
            return 0.0
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def leer_precios(row) -> tuple[float, float, bool]:
    get = row.get if hasattr(row, "get") else row.__getitem__

    def g(k):
        try:
            return get(k)
        except Exception:
            return None

    lista_guardada = _num(g("precio_original") or g("precio_anterior"))
    precio = _num(g("precio"))
    cands = [
        _num(g("precio_oferta")),
        _num(g("precio_oferta_relampago")),
        _num(g("precio_oferta_promedio")),
    ]
    cands = [x for x in cands if x > 0]
    max_c = max(cands) if cands else 0.0
    lista = precio
    if max_c > 0 and precio > 0 and max_c > precio:
        lista = max_c
    original = lista_guardada if lista_guardada > lista else (lista or lista_guardada)
    menores = [x for x in cands if original > 0 and x < original]
    vigente = precio or original
    if menores:
        vigente = min(menores)
    elif precio > 0 and original > precio:
        vigente = precio
    hay = original > 0 and vigente > 0 and vigente < original
    return original, vigente, hay


def listar(limite: int = 12) -> list[dict]:
    try:
        from src.base_de_datos.database import db_manager

        try:
            db_manager.asegurar_lectura_tienda()
        except Exception:
            pass
        rows = db_manager.execute_query(
            "SELECT nombre, precio, precio_oferta, "
            "precio_oferta_relampago, precio_oferta_promedio "
            "FROM productos WHERE precio > 0"
        ) or []
    except Exception:
        return []
    out = []
    for r in rows:
        lista, oferta, hay = leer_precios(r)
        if not hay:
            continue
        ahorro = lista - oferta
        pct = int(round((ahorro / lista) * 100)) if lista > 0 else 0
        out.append({
            "nombre": str(r["nombre"] or "").strip(),
            "lista": lista,
            "oferta": oferta,
            "ahorro": ahorro,
            "pct": pct,
        })
    out.sort(key=lambda x: x["ahorro"], reverse=True)
    return out[:limite]
