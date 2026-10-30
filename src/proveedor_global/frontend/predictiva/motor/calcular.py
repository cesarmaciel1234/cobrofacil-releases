"""Cuánto pedir para los días que el proveedor no vuelve.

Se prepara el día anterior al reparto. Un feriado nacional no reparte.
El pico viejo no se compra: la venta de ahora manda.
"""

import math
from datetime import date, timedelta

from src.proveedor_global.frontend.predictiva.calendario.jornada import (
    dias_cubiertos, preparar as ultimo_abierto, turno,
)
from src.proveedor_global.frontend.predictiva.motor.feriados import es as es_feriado

_DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def proyectar(hoy, reparto, ritmo, stock, unidad: str, calendario=None) -> dict:
    """ritmo es la venta por día que se usa. stock es lo que ya hay, en la misma unidad."""
    marcados = set(int(d) for d in (reparto or []) if 0 <= int(d) <= 6)
    if not marcados:
        return {
            "pedir": 0,
            "dias": 0,
            "porque": "No hay días de reparto marcados.",
            "prepara": None,
            "entrega": None,
        }
    entrega = _siguiente(hoy, marcados)
    if entrega == hoy:
        entrega = _siguiente(hoy + timedelta(days=1), marcados)
    prepara = ultimo_abierto(entrega, calendario)
    otra = _siguiente(entrega + timedelta(days=1), marcados)
    dias = dias_cubiertos(entrega, otra, calendario)
    try:
        ritmo = float(ritmo or 0)
        stock = float(stock or 0)
    except (TypeError, ValueError):
        ritmo, stock = 0.0, 0.0
    if stock < 0:
        stock = 0.0
    falta = ritmo * dias - stock
    pedir = int(math.ceil(falta - 1e-9)) if falta > 0 else 0
    return {
        "pedir": pedir,
        "dias": dias,
        "ritmo": ritmo,
        "stock": stock,
        "prepara": prepara,
        "entrega": entrega,
        "hasta": otra - timedelta(days=1),
        "porque": _porque(unidad, pedir, dias, ritmo, stock, prepara, entrega, otra, hoy)
        + _llegada(entrega, calendario),
    }


def definir(muestras) -> dict:
    """Pico, mínimo y máximo salen de la venta medida. El pico es el día más alto y no se compra."""
    numeros = []
    for numero in muestras or []:
        try:
            numeros.append(float(numero))
        except (TypeError, ValueError):
            continue
    if len(numeros) < 2:
        return {"listo": False, "pico": None, "minimo": None, "maximo": None}
    pico = max(numeros)
    resto = list(numeros)
    resto.remove(pico)
    if not resto:
        return {"listo": True, "pico": pico, "minimo": pico, "maximo": pico}
    return {"listo": True, "pico": pico, "minimo": min(resto), "maximo": max(resto)}


def ritmo_de(maximo, minimo, ventas) -> tuple:
    """El máximo histórico, salvo que los días recientes vendan menos y no bajen del mínimo."""
    try:
        techo = float(maximo or 0)
        piso = float(minimo or 0)
    except (TypeError, ValueError):
        techo, piso = 0.0, 0.0
    if piso > techo:
        piso = techo
    muestras = []
    for numero in ventas or []:
        try:
            muestras.append(float(numero))
        except (TypeError, ValueError):
            continue
    if len(muestras) < 3:
        return techo, "máximo cargado"
    medio = sum(muestras) / len(muestras)
    if medio < piso:
        medio = piso
    if medio > techo:
        medio = techo
    if medio < techo:
        return medio, "venta reciente"
    return techo, "máximo cargado"


def _siguiente(desde: date, marcados: set) -> date:
    dia = desde
    for _ in range(21):
        if dia.weekday() in marcados and not es_feriado(dia):
            return dia
        dia += timedelta(days=1)
    return desde


def rango(dias, stock, piso, techo) -> tuple:
    """Banda para no clavar un solo número. El piso es el promedio y el techo es la venta alta."""
    try:
        piso = float(piso)
        techo = float(techo)
        dias = float(dias or 0)
        stock = float(stock or 0)
    except (TypeError, ValueError):
        return 0, 0
    if techo < piso:
        techo = piso
    if stock < 0:
        stock = 0.0
    media = (piso + techo) / 2
    bajo = max(0, int(round(media * dias - stock)))
    alto = max(bajo, int(techo * dias - stock))
    return bajo, alto


def _llegada(entrega, calendario) -> str:
    if turno(entrega, calendario) != "tarde":
        return ""
    return " Llega a la tarde: la mañana de ese día se cubre con lo que ya hay."


def _dias_txt(dias) -> str:
    return f"{float(dias):.1f}".rstrip("0").rstrip(".")


def _porque(unidad, pedir, dias, ritmo, stock, prepara, entrega, otra, hoy) -> str:
    cuando = "Hoy se prepara" if prepara == hoy else f"Se prepara el {_nombre(prepara)}"
    cubre = (
        f"para el {_nombre(entrega)}. Cubre {_dias_txt(dias)} "
        f"día{'s' if float(dias) != 1 else ''} hasta el {_nombre(otra - timedelta(days=1))}"
    )
    ritmo_txt = f"{ritmo:.1f}".rstrip("0").rstrip(".")
    stock_txt = f"{stock:.1f}".rstrip("0").rstrip(".")
    if pedir <= 0:
        return (
            f"{cuando} {cubre}. Con {stock_txt} {unidad} alcanza. "
            f"No se compra el pico viejo."
        )
    return (
        f"{cuando} {cubre}. Al ritmo de ahora ({ritmo_txt} {unidad} por día) "
        f"y con {stock_txt} en stock, se piden {pedir} {unidad}. "
        f"El pico viejo no se usa."
    )


def _nombre(dia: date) -> str:
    if dia is None:
        return ""
    return f"{_DIAS[dia.weekday()]} {dia.strftime('%d/%m')}"
