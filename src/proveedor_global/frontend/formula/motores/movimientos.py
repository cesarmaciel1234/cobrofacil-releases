"""Ventas y reajustes del cajón. El filtro solo elige qué filas se ven."""

import datetime

_TABLA = "formula_movimiento"
PERIODOS = ("Hoy", "Ayer", "Semana", "Semana pasada", "Mes", "Mes pasado", "Año", "Todo")


def anotar(db, tipo: str, formula: str, huevos_unidad: int, cantidad: float) -> bool:
    """Resta esos huevos del cajón y deja el renglón. Falso si no alcanza."""
    try:
        unidades = float(cantidad or 0)
        huevos_unidad = int(huevos_unidad or 0)
    except (TypeError, ValueError):
        return False
    if unidades == 0 or huevos_unidad <= 0:
        return False
    huevos = int(round(abs(unidades) * huevos_unidad))
    from src.proveedor_global.frontend.formula.motores.verdad import leer

    dato = leer(db, "Huevo")
    if dato["cajones"] * 360 + 1e-6 < huevos:
        return False
    from src.proveedor_global.frontend.formula.motores.verdad import bajar_huevos

    bajar_huevos(db, huevos)
    _asegurar(db)
    marca = abs(unidades) if tipo == "venta" else -abs(unidades)
    db.execute_non_query(
        f"INSERT INTO {_TABLA} (fecha, tipo, formula, cantidad, huevos) VALUES (?, ?, ?, ?, ?)",
        (datetime.datetime.now().isoformat(timespec="seconds"), tipo, formula, marca, huevos),
    )
    return True


def listar(db, tipo: str, periodo: str) -> list:
    _asegurar(db)
    try:
        filas = db.execute_query(
            f"SELECT fecha, formula, cantidad, huevos FROM {_TABLA} WHERE tipo = ? ORDER BY fecha DESC",
            (tipo,),
        ) or []
    except Exception:
        return []
    desde, hasta = _rango(periodo)
    salida = []
    for cruda in filas:
        fila = _dict(cruda)
        dia = _dia(fila.get("fecha"))
        if desde and (dia is None or dia < desde or dia > hasta):
            continue
        salida.append(fila)
    return salida


def _rango(periodo, hoy=None):
    hoy = hoy or datetime.date.today()
    if periodo == "Hoy":
        return hoy, hoy
    if periodo == "Ayer":
        ayer = hoy - datetime.timedelta(days=1)
        return ayer, ayer
    if periodo == "Semana":
        inicio = hoy - datetime.timedelta(days=hoy.weekday())
        return inicio, inicio + datetime.timedelta(days=6)
    if periodo == "Semana pasada":
        inicio = hoy - datetime.timedelta(days=hoy.weekday() + 7)
        return inicio, inicio + datetime.timedelta(days=6)
    if periodo == "Mes":
        return hoy.replace(day=1), hoy
    if periodo == "Mes pasado":
        primero = hoy.replace(day=1) - datetime.timedelta(days=1)
        return primero.replace(day=1), primero
    if periodo == "Año":
        return hoy.replace(month=1, day=1), hoy
    return None, None


def _asegurar(db) -> None:
    try:
        db.execute_non_query(
            f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, tipo TEXT, formula TEXT, "
            "cantidad REAL, huevos INTEGER)"
        )
    except Exception:
        try:
            db.execute_non_query(
                f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
                "id INT AUTO_INCREMENT PRIMARY KEY, fecha VARCHAR(32), tipo VARCHAR(20), "
                "formula VARCHAR(80), cantidad DOUBLE, huevos INT)"
            )
        except Exception:
            pass


def _dia(fecha):
    try:
        return datetime.date.fromisoformat(str(fecha or "")[:10])
    except ValueError:
        return None


def _dict(fila) -> dict:
    if isinstance(fila, dict):
        return {str(k).lower(): v for k, v in fila.items()}
    try:
        return {str(k).lower(): fila[k] for k in fila.keys()}
    except Exception:
        try:
            return {"fecha": fila[0], "formula": fila[1], "cantidad": fila[2], "huevos": fila[3]}
        except Exception:
            return {}
