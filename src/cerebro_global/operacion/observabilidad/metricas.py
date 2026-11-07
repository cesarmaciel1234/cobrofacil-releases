"""Métricas puras para explicar cómo se comportan los planes."""


def cobertura(stock, ritmo) -> float:
    try:
        stock = max(0.0, float(stock or 0))
        ritmo = float(ritmo or 0)
    except (TypeError, ValueError):
        return 0.0
    return round(stock / ritmo, 2) if ritmo > 0 else 0.0


def resumen(plan: dict | None) -> dict:
    salida = {"total": 0, "por_estado": {}, "por_fuente": {}}
    for accion in (plan or {}).get("acciones") or []:
        salida["total"] += 1
        estado = str(accion.get("estado") or "sin_estado")
        salida["por_estado"][estado] = salida["por_estado"].get(estado, 0) + 1
        for fuente in accion.get("fuentes") or []:
            salida["por_fuente"][fuente] = salida["por_fuente"].get(fuente, 0) + 1
    return salida
