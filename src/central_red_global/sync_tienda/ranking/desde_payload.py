"""Arma el ranking de la maestra (API nueva o top10 viejo)."""

from __future__ import annotations

import json
import urllib.request


def _nombre_fila(row) -> str:
    if isinstance(row, dict):
        return str(row.get("nombre") or row.get("nombre_producto") or "").strip()
    if isinstance(row, (list, tuple)) and row:
        return str(row[0] or "").strip()
    return ""


def _num_clave(row, claves) -> float | None:
    if not isinstance(row, dict):
        return None
    for key in claves:
        if key not in row or row.get(key) in (None, ""):
            continue
        try:
            return float(row.get(key) or 0)
        except (TypeError, ValueError):
            continue
    return None


def _cant_fila(row, fallback: float) -> float:
    hallado = _num_clave(row, ("cantidad", "total_cant", "cant"))
    if hallado is not None:
        return hallado
    # (nombre, cantidad, recaudacion). Una fila de producto trae el precio en [1]: no es una venta.
    if isinstance(row, (list, tuple)) and len(row) == 3:
        try:
            return float(row[1] or 0)
        except (TypeError, ValueError):
            pass
    return fallback


def _rec_fila(row) -> float:
    hallado = _num_clave(row, ("recaudacion", "total_recaudacion"))
    if hallado is not None:
        return hallado
    if isinstance(row, (list, tuple)) and len(row) == 3:
        try:
            return float(row[2] or 0)
        except (TypeError, ValueError):
            pass
    return 0.0


def ranking_desde_filas(rows) -> list[dict]:
    out = []
    for row in rows or []:
        nombre = _nombre_fila(row)
        if not nombre:
            continue
        cant = _cant_fila(row, 0.0)
        rec = _rec_fila(row)
        if cant <= 0 and rec <= 0:
            continue
        out.append({
            "nombre": nombre,
            "cantidad": cant,
            "recaudacion": rec,
        })
    return out


def ranking_desde_top10(top10: dict | None) -> dict:
    """El top10 viejo no trae ayer ni separa tickets de kilos. No se copia un período en otro."""
    top10 = top10 or {}
    hoy = ranking_desde_filas(top10.get("hoy"))
    semana = ranking_desde_filas(top10.get("semana"))
    mes = ranking_desde_filas(top10.get("mes"))
    return {
        "hoy_frecuencia": hoy,
        "hoy_volumen": hoy,
        "ayer_frecuencia": [],
        "ayer_volumen": [],
        "semana_frecuencia": semana or mes,
        "semana_volumen": semana or mes,
    }


def ranking_tiene_datos(ranking: dict | None) -> bool:
    if not ranking:
        return False
    return any(ranking.get(k) for k in ranking)


def bajar_ranking_http(host: str) -> dict:
    if not host:
        return {}
    for path in ("/api/carteleria/ranking", "/api/carteleria/data"):
        try:
            req = urllib.request.Request(
                f"http://{host}:8000{path}",
                headers={"User-Agent": "CobroFacil-Esclava"},
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if path.endswith("ranking"):
                ranking = data.get("ranking") if isinstance(data, dict) and "ranking" in data else data
            else:
                ranking = (data or {}).get("ranking") if isinstance(data, dict) else {}
                if not ranking_tiene_datos(ranking):
                    ranking = ranking_desde_top10((data or {}).get("top10"))
            if ranking_tiene_datos(ranking):
                return ranking
        except Exception:
            continue
    return {}


def asegurar_ranking(data: dict, host: str = "") -> dict:
    data = data or {}
    ranking = data.get("ranking")
    if ranking_tiene_datos(ranking):
        return data
    if host:
        ranking = bajar_ranking_http(host)
    if not ranking_tiene_datos(ranking):
        ranking = ranking_desde_top10(data.get("top10"))
    data["ranking"] = ranking or {}
    return data


def completar_ranking_local(data: dict) -> dict:
    """La maestra no pide HTTP: el ranking sale de sus propias ventas."""
    data = data or {}
    if ranking_tiene_datos(data.get("ranking")):
        return data
    try:
        from src.central_red_global.sync_tienda.ranking.motor import ranking_carteleria

        local = ranking_carteleria()
    except Exception:
        local = {}
    if ranking_tiene_datos(local):
        data["ranking"] = local
    return data
