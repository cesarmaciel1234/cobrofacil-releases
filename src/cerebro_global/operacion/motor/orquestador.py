"""Coordina pedidos y pronósticos sin escribir ni despachar nada."""

from __future__ import annotations

from datetime import date


_PREDICTIVAS = {
    "pollo": ("Pollo", "cajas"),
    "media": ("Carne", "medias"),
}


def analizar(db=None) -> dict:
    """Consulta las fuentes existentes. Un error de una no apaga la otra."""
    fallas = []
    try:
        from src.proveedor_global.frontend.predictiva.consultar import hoy_en_curso
        if db is None:
            from src.base_de_datos.database import db_manager
            db = db_manager
        predictiva = hoy_en_curso(db)
    except Exception as error:
        predictiva = {}
        fallas.append(f"Compra predictiva: {error}")
    try:
        from src.motor_abastecimiento.motor_abastecimiento import MotorAbastecimiento
        resumen = MotorAbastecimiento.obtener_resumen_reposicion()
    except Exception as error:
        resumen = {}
        fallas.append(f"Abastecimiento: {error}")
    panorama = evaluar(predictiva, resumen)
    panorama["fuentes_fallidas"] = fallas
    return panorama


def preparar_plan(db=None) -> dict | None:
    """Persiste un borrador central; no aprueba, despacha ni modifica stock."""
    if db is None:
        from src.base_de_datos.database import db_manager
        db = db_manager
    from src.cerebro_global.operacion.ejecucion import crear_borrador
    from src.cerebro_global.operacion.planificacion import construir
    from src.cerebro_global.operacion.politicas import obtener

    plan = construir(analizar(db), obtener(db))
    return plan if crear_borrador(db, plan) else None


def evaluar(predictiva: dict | None, resumen: dict | None, hoy: date | None = None) -> dict:
    """Une propuestas equivalentes sin sumar compras ni cambiar sus reglas."""
    hoy = hoy or date.today()
    acciones = {}
    for clave, (formula, unidad) in _PREDICTIVAS.items():
        proyeccion = (predictiva or {}).get(clave) or {}
        cantidad = _numero(proyeccion.get("pedir"))
        if cantidad <= 0:
            continue
        _sumar(
            acciones, formula, unidad, cantidad, "predictiva",
            proyeccion.get("porque") or "Cobertura hasta el próximo reparto.",
            proyeccion.get("prepara"), proyeccion.get("stock"), hoy,
        )
    for proveedor, datos in ((resumen or {}).get("pedidos") or {}).items():
        for item in (datos or {}).get("items") or []:
            if not item.get("es_formula"):
                continue
            cantidad = _numero(item.get("cantidad_a_pedir"))
            if cantidad <= 0:
                continue
            formula = _formula(item)
            if not formula:
                continue
            unidad = _unidad(item, formula)
            _sumar(
                acciones, formula, unidad, cantidad, "abastecimiento",
                item.get("porque") or "Regla de reposición de la fórmula.",
                None, item.get("stock_actual"), hoy, proveedor,
            )
    ordenadas = sorted(acciones.values(), key=_orden)
    return {
        "acciones": ordenadas,
        "total": len(ordenadas),
        "modo": "borrador",
    }


def _sumar(acciones, formula, unidad, cantidad, fuente, porque, prepara, stock, hoy, proveedor=""):
    clave = (formula.lower(), unidad.lower())
    existente = acciones.get(clave)
    if existente is None:
        existente = {
            "formula": formula,
            "unidad": unidad,
            "cantidad": cantidad,
            "fuentes": [fuente],
            "explicaciones": [str(porque)],
            "proveedor": proveedor or "",
            "estado": _estado(prepara, stock, hoy),
            "modo": "borrador",
            "requiere_revision": True,
        }
        acciones[clave] = existente
        return
    existente["cantidad"] = max(existente["cantidad"], cantidad)
    if fuente not in existente["fuentes"]:
        existente["fuentes"].append(fuente)
    if porque and str(porque) not in existente["explicaciones"]:
        existente["explicaciones"].append(str(porque))
    if proveedor and not existente["proveedor"]:
        existente["proveedor"] = proveedor
    if _peso_estado(_estado(prepara, stock, hoy)) < _peso_estado(existente["estado"]):
        existente["estado"] = _estado(prepara, stock, hoy)


def _formula(item) -> str:
    ident = str(item.get("id") or "")
    if ident.startswith("formula:"):
        parte = ident.split(":", 2)[1].strip()
        return "Carne" if parte == "Media res" else parte
    nombre = str(item.get("nombre") or "").lower()
    if "pollo" in nombre or "suprema" in nombre or "pata" in nombre:
        return "Pollo"
    if "media res" in nombre:
        return "Carne"
    return ""


def _unidad(item, formula) -> str:
    nombre = str(item.get("nombre") or "").lower()
    if "(kg)" in nombre:
        return "kg"
    if formula == "Pollo":
        return "cajas"
    if formula == "Carne":
        return "medias"
    return "unidades"


def _estado(prepara, stock, hoy) -> str:
    if _numero(stock) <= 0:
        return "crítico"
    if prepara and prepara <= hoy:
        return "preparar_hoy"
    return "programado"


def _peso_estado(estado) -> int:
    return {"crítico": 0, "preparar_hoy": 1, "programado": 2}.get(estado, 3)


def _orden(accion) -> tuple:
    return _peso_estado(accion["estado"]), accion["formula"], accion["unidad"]


def _numero(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0
