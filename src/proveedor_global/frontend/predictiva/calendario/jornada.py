"""Días que el local abre, horario y si la mercadería llega a la mañana o a la tarde.

Cada negocio tiene el suyo. El feriado nacional no se abre ni se usa como día de venta.
"""

import json
import os
from datetime import date, timedelta

from src.proveedor_global.frontend.predictiva.motor.feriados import es as es_feriado
from src.utils.paths import get_base_path

_ARCHIVO = os.path.join(get_base_path(), "reportes", "calendario_local.json")


def base() -> dict:
    """Abre toda la semana, de 8 a 20, y la carga llega a la mañana."""
    return {
        "abiertos": [0, 1, 2, 3, 4, 5, 6],
        "modo": "corrido",
        "abre": "08:00",
        "cierra": "20:00",
        "turno2_abre": "17:00",
        "turno2_cierra": "21:00",
        "turno": "manana",
        "turnos": {},
        "horarios": {},
        "cierres": [],
    }


def leer() -> dict:
    datos = base()
    if not os.path.isfile(_ARCHIVO):
        return datos
    try:
        crudo = json.load(open(_ARCHIVO, encoding="utf-8"))
    except (OSError, ValueError):
        return datos
    if not isinstance(crudo, dict):
        return datos
    if isinstance(crudo.get("abiertos"), list):
        datos["abiertos"] = _dias(crudo.get("abiertos"))
    datos["modo"] = _modo(crudo.get("modo"))
    datos["abre"] = _hora(crudo.get("abre"), datos["abre"])
    datos["cierra"] = _hora(crudo.get("cierra"), datos["cierra"])
    datos["turno2_abre"] = _hora(crudo.get("turno2_abre"), datos["turno2_abre"])
    datos["turno2_cierra"] = _hora(crudo.get("turno2_cierra"), datos["turno2_cierra"])
    datos["turno"] = _turno(crudo.get("turno"))
    turnos = crudo.get("turnos") if isinstance(crudo.get("turnos"), dict) else {}
    datos["turnos"] = {str(dia): _turno(valor) for dia, valor in turnos.items()}
    datos["horarios"] = _horarios(crudo.get("horarios"), datos)
    datos["cierres"] = [str(dia)[:10] for dia in (crudo.get("cierres") or []) if str(dia)[:10]]
    return datos


def guardar(datos: dict) -> None:
    limpio = base()
    limpio["abiertos"] = _dias((datos or {}).get("abiertos"))
    limpio["modo"] = _modo((datos or {}).get("modo"))
    limpio["abre"] = _hora((datos or {}).get("abre"), limpio["abre"])
    limpio["cierra"] = _hora((datos or {}).get("cierra"), limpio["cierra"])
    limpio["turno2_abre"] = _hora((datos or {}).get("turno2_abre"), limpio["turno2_abre"])
    limpio["turno2_cierra"] = _hora((datos or {}).get("turno2_cierra"), limpio["turno2_cierra"])
    limpio["turno"] = _turno((datos or {}).get("turno"))
    turnos = (datos or {}).get("turnos") if isinstance((datos or {}).get("turnos"), dict) else {}
    limpio["turnos"] = {str(dia): _turno(valor) for dia, valor in turnos.items()}
    limpio["horarios"] = _horarios((datos or {}).get("horarios"), limpio)
    limpio["cierres"] = [str(dia)[:10] for dia in ((datos or {}).get("cierres") or [])]
    os.makedirs(os.path.dirname(_ARCHIVO), exist_ok=True)
    with open(_ARCHIVO, "w", encoding="utf-8") as salida:
        json.dump(limpio, salida, ensure_ascii=False, indent=2)


def abierto(dia: date, datos=None) -> bool:
    """Un feriado o un cierre del local no es día de venta."""
    datos = leer() if datos is None else datos
    if es_feriado(dia):
        return False
    if dia.isoformat() in set(datos.get("cierres") or []):
        return False
    return dia.weekday() in set(_dias(datos.get("abiertos")))


def turno(dia: date, datos=None) -> str:
    """manana: se vende ese día. tarde: la mañana sigue con el stock viejo."""
    datos = leer() if datos is None else datos
    propio = (datos.get("turnos") or {}).get(str(dia.weekday()))
    return _turno(propio or datos.get("turno"))


def preparar(entrega: date, datos=None) -> date:
    """El último día abierto antes de que llegue la mercadería."""
    datos = leer() if datos is None else datos
    dia = entrega - timedelta(days=1)
    for _ in range(14):
        if abierto(dia, datos):
            return dia
        dia -= timedelta(days=1)
    return entrega - timedelta(days=1)


def hasta_el_camion(entrega: date, proxima: date, datos=None) -> float:
    """Días de venta de esta carga. Si el próximo llega tarde, suma esa mañana."""
    datos = leer() if datos is None else datos
    total = dias_cubiertos(entrega, proxima, datos)
    if proxima <= entrega:
        return total
    if datos.get("modo") == "doble" or turno(proxima, datos) == "tarde":
        if turno(proxima, datos) != "tarde" and abierto(proxima, datos):
            total += 0.5
    return total


def dias_cubiertos(entrega: date, proxima: date, datos=None) -> float:
    """Jornadas que cubre esta carga. Un día corto o el segundo turno pesan menos."""
    datos = leer() if datos is None else datos
    total = 0.0
    dia = entrega
    while dia < proxima:
        parte = "tarde" if dia == entrega and turno(dia, datos) == "tarde" else "completa"
        total += fraccion(dia, datos, parte)
        dia += timedelta(days=1)
    if proxima > entrega and turno(proxima, datos) == "tarde":
        total += fraccion(proxima, datos, "manana")
    return total


def fraccion(dia: date, datos=None, parte: str = "completa") -> float:
    """1 es la jornada patrón. Un sábado corto o solo el turno de la tarde es una parte."""
    datos = leer() if datos is None else datos
    if not abierto(dia, datos):
        return 0.0
    contados = _minutos_parte(_ficha(dia, datos), parte)
    patron = _minutos_patron(datos)
    if patron <= 0 or contados <= 0:
        return 0.0
    return min(1.0, contados / patron)


def texto(datos=None) -> str:
    """Una línea para el centro de la pantalla."""
    datos = leer() if datos is None else datos
    if datos.get("modo") == "doble":
        horas = (
            f"Doble turno {datos['abre']}–{datos['cierra']}"
            f" y {datos['turno2_abre']}–{datos['turno2_cierra']}"
        )
    else:
        horas = f"Horario corrido {datos['abre']}–{datos['cierra']}"
    llega = "la tarde" if datos.get("turno") == "tarde" else "la mañana"
    cuantos = len(datos.get("horarios") or {})
    extra = ""
    if cuantos == 1:
        extra = " · 1 día con otro horario"
    elif cuantos > 1:
        extra = f" · {cuantos} días con otro horario"
    return f"{horas} · Llega a {llega}{extra}"


def _dias(valores) -> list:
    salida = []
    for dia in valores or []:
        try:
            numero = int(dia)
        except (TypeError, ValueError):
            continue
        if 0 <= numero <= 6 and numero not in salida:
            salida.append(numero)
    return salida


def _turno(valor) -> str:
    return "tarde" if str(valor or "").lower().startswith("t") else "manana"


def _modo(valor) -> str:
    return "doble" if str(valor or "").lower().startswith("d") else "corrido"


def _ficha(dia: date, datos) -> dict:
    propio = (datos.get("horarios") or {}).get(str(dia.weekday())) or {}
    return _horario(propio, datos)


def _horario(propio, general) -> dict:
    return {
        "modo": _modo(propio.get("modo") or general.get("modo")),
        "abre": _hora(propio.get("abre"), general.get("abre") or "08:00"),
        "cierra": _hora(propio.get("cierra"), general.get("cierra") or "20:00"),
        "turno2_abre": _hora(propio.get("turno2_abre"), general.get("turno2_abre") or "17:00"),
        "turno2_cierra": _hora(propio.get("turno2_cierra"), general.get("turno2_cierra") or "21:00"),
    }


def _horarios(crudo, general) -> dict:
    if not isinstance(crudo, dict):
        return {}
    salida = {}
    for clave, valor in crudo.items():
        try:
            dia = int(clave)
        except (TypeError, ValueError):
            continue
        if isinstance(valor, dict) and 0 <= dia <= 6:
            salida[str(dia)] = _horario(valor, general)
    return salida


def _minutos(texto) -> int:
    hora, minuto = str(texto or "00:00").split(":", 1)
    return int(hora) * 60 + int(minuto)


def _duracion(inicio, fin) -> int:
    return max(0, int(fin) - int(inicio))


def _minutos_patron(datos) -> int:
    ficha = _horario({}, datos)
    return _minutos_parte(ficha, "completa") or (12 * 60)


def _minutos_parte(ficha, parte: str) -> int:
    inicio = _minutos(ficha["abre"])
    fin = _minutos(ficha["cierra"])
    if ficha["modo"] == "doble":
        manana = _duracion(inicio, fin)
        tarde = _duracion(_minutos(ficha["turno2_abre"]), _minutos(ficha["turno2_cierra"]))
        if parte == "manana":
            return manana
        if parte == "tarde":
            return tarde
        return manana + tarde
    if parte == "completa":
        return _duracion(inicio, fin)
    medio = inicio + _duracion(inicio, fin) // 2
    if parte == "manana":
        return _duracion(inicio, medio)
    return _duracion(medio, fin)


def _hora(texto, respaldo: str) -> str:
    partes = str(texto or "").strip().split(":")
    if len(partes) != 2:
        return respaldo
    try:
        hora, minuto = int(partes[0]), int(partes[1])
    except ValueError:
        return respaldo
    if 0 <= hora <= 23 and 0 <= minuto <= 59:
        return f"{hora:02d}:{minuto:02d}"
    return respaldo
