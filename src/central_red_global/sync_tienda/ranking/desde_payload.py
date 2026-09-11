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


def _cant_fila(row, fallback: float) -> float:
    if isinstance(row, dict):
        for key in ("cantidad", "total_cant", "cant"):
            if row.get(key) not in (None, ""):
                try:
                    return float(row.get(key) or 0)
                except (TypeError, ValueError):
                    pass
    elif isinstance(row, (list, tuple)) and len(row) > 1:
        try:
            return float(row[1] or 0)
        except (TypeError, ValueError):
            pass
    return fallback


def _rec_fila(row) -> float:
    if isinstance(row, dict):
        for key in ("recaudacion", "total_recaudacion"):
            if row.get(key) not in (None, ""):
                try:
                    return float(row.get(key) or 0)
                except (TypeError, ValueError):
                    pass
    elif isinstance(row, (list, tuple)) and len(row) > 2:
        try:
            return float(row[2] or 0)
        except (TypeError, ValueError):
            pass
    return 0.0


def ranking_desde_filas(rows) -> list[dict]:
    out = []
    total = len(rows or [])
    for i, row in enumerate(rows or []):
        nombre = _nombre_fila(row)
        if not nombre:
            continue
        peso = float(total - i)
        out.append({
            "nombre": nombre,
            "cantidad": _cant_fila(row, peso) or peso,
            "recaudacion": _rec_fila(row) or peso * 1000,
        })
    return out


def ranking_desde_top10(top10: dict | None) -> dict:
    top10 = top10 or {}
    hoy = ranking_desde_filas(top10.get("hoy"))
    semana = ranking_desde_filas(top10.get("semana")) or hoy
    mes = ranking_desde_filas(top10.get("mes")) or semana
    return {
        "hoy_frecuencia": hoy,
        "hoy_volumen": hoy,
        "ayer_frecuencia": semana,
        "ayer_volumen": semana,
        "semana_frecuencia": mes,
        "semana_volumen": mes,
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
