"""Ticket de volumen con el mismo corte que una venta. El ancho sale de la impresora."""

from __future__ import annotations

import textwrap
from datetime import datetime

ESC = b"\x1b"
GS = b"\x1d"
CUT_PAPER = GS + b"\x56\x41\x00"
ALIGN_CENTER = ESC + b"\x61\x01"
ALIGN_LEFT = ESC + b"\x61\x00"
BOLD_ON = ESC + b"\x45\x01"
BOLD_OFF = ESC + b"\x45\x00"
CHICO_ON = ESC + b"\x21\x01"
CHICO_OFF = ESC + b"\x21\x00"
MARCA_ON = ESC + b"\x21\x30"


def _campo(fila, clave, default=""):
    if isinstance(fila, dict):
        return fila.get(clave, default)
    try:
        return fila[clave]
    except Exception:
        return default


def periodo_mes(anio: int, mes: int) -> tuple[str, str, str]:
    import calendar

    ultimo = calendar.monthrange(anio, mes)[1]
    ini = f"{anio:04d}-{mes:02d}-01"
    fin = f"{anio:04d}-{mes:02d}-{ultimo:02d}"
    return ini, fin, f"01/{mes:02d}/{anio:04d} al {ultimo:02d}/{mes:02d}/{anio:04d}"


def columnas_configuradas() -> int:
    """58 mm son 32 columnas. 80 mm son 48. Cualquier otro ancho usa 58."""
    from src.config import config

    try:
        config._load_config()
    except Exception:
        pass
    try:
        ancho = int(config.get("printer_paper_width_mm", 58) or 58)
    except (TypeError, ValueError):
        ancho = 58
    return 48 if ancho == 80 else 32


def lineas_volumen(filas, periodo: str, tickets: int, columnas: int, empresa: str = "") -> list[str]:
    return [texto for _estilo, texto in _piezas(filas, periodo, tickets, columnas, empresa)]


def armar_ticket_volumen(filas, periodo: str, tickets: int, columnas: int | None = None, empresa: str = "") -> bytes:
    cols = columnas if columnas is not None else columnas_configuradas()
    piezas = _piezas(filas, periodo, tickets, cols, empresa)
    data = bytearray()
    data.extend(ESC + b"\x40")
    data.extend(ALIGN_CENTER)
    for estilo, texto in piezas:
        data.extend(_estilo(estilo))
        data.extend((texto + "\n").encode("cp850", errors="replace"))
    data.extend(CHICO_OFF)
    data.extend(BOLD_OFF)
    data.extend(ALIGN_LEFT)
    data.extend(b"\n\n\n\n")
    data.extend(CUT_PAPER)
    return bytes(data)


def _piezas(filas, periodo: str, tickets: int, columnas: int, empresa: str = "") -> list[tuple[str, str]]:
    cols = max(16, int(columnas))
    ficha = _ficha(empresa)
    kilos = 0.0
    unidades = 0.0
    plata = 0.0
    piezas: list[tuple[str, str]] = _marca(cols, ficha["empresa"])
    piezas.append(("saludo", _cabe(cols, _saludo())))
    for dato in (ficha["cuit"], ficha["direccion"], ficha["telefono"]):
        if dato:
            piezas.append(("texto", _cabe(cols, dato)))
    piezas.extend(
        [
            ("regla", "-" * cols),
            ("titulo", _cabe(cols, "VOLUMEN VENDIDO")),
            ("texto", _cabe(cols, f"Fecha: {periodo or 'Periodo'}")),
            ("texto", _cabe(cols, f"Clientes: {int(tickets or 0)}")),
            ("regla", "-" * cols),
        ]
    )
    for fila in filas or []:
        nombre = _nombre(str(_campo(fila, "nombre_producto", "") or ""))
        try:
            cant = float(_campo(fila, "total_cant", 0) or 0)
        except (TypeError, ValueError):
            cant = 0.0
        try:
            monto = float(_campo(fila, "total_monto", 0) or 0)
        except (TypeError, ValueError):
            monto = 0.0
        plata += monto
        medida = medida_de(fila)
        if medida == "kg":
            kilos += cant
        elif medida == "un":
            unidades += cant
        for pedazo in textwrap.wrap(nombre, cols) or ["Sin nombre"]:
            piezas.append(("producto", pedazo[:cols]))
        precio = (monto / cant) if cant else 0.0
        piezas.extend(_detalle(cols, cant, precio, monto, medida))
    cierre = [
        ("regla", "-" * cols),
        ("total", _par(cols, "TOTAL", f"${plata:.2f}")),
    ]
    if kilos:
        cierre.append(("pie", _par(cols, "Kilos", f"{kilos:g}")))
    if unidades:
        cierre.append(("pie", _par(cols, "Unidades", f"{unidades:g}")))
    cierre.append(("pie", _par(cols, "Articulos", str(len(filas or [])))))
    cierre.append(("regla", "-" * cols))
    piezas.extend(cierre)
    piezas.extend(_marca(cols, ficha["empresa"], chica=True))
    return piezas


def _marca(cols: int, empresa: str, chica: bool = False) -> list[tuple[str, str]]:
    nombre = _cabe(cols, empresa) or "Mi Comercio"
    if chica:
        return [("cierre", nombre)]
    ancho = max(8, cols // 2)
    return [("marca", pedazo) for pedazo in textwrap.wrap(nombre, ancho)]


def medida_de(fila) -> str:
    """Kilo si el producto se pesa. Si no, unidad."""
    from src.motor_inventario.unidad_medida.logica.formatear import etiqueta_unidad

    etiqueta = etiqueta_unidad(
        {
            "es_pesable": _campo(fila, "es_pesable", 0),
            "unidad": _campo(fila, "unidad", "") or _campo(fila, "unidad_medida", ""),
            "departamento": _campo(fila, "departamento", ""),
        }
    )
    return {"kilo": "kg", "unidad": "un", "litro": "lt", "metro": "m", "gramo": "g"}.get(etiqueta, "un")


def _detalle(cols: int, cant: float, unit: float, monto: float, medida: str = "kg") -> list[tuple[str, str]]:
    izquierda = f"  {cant:g} {medida} x ${unit:.2f}"
    derecha = f"${monto:.2f}"
    if len(izquierda) + 1 + len(derecha) <= cols:
        return [("detalle", _par(cols, izquierda, derecha))]
    return [
        ("detalle", izquierda[:cols]),
        ("detalle", derecha.rjust(cols)[:cols]),
    ]


def _estilo(estilo: str) -> bytes:
    if estilo == "marca":
        return ALIGN_CENTER + BOLD_ON + MARCA_ON
    if estilo == "cierre":
        return CHICO_OFF + ALIGN_CENTER + BOLD_ON
    if estilo == "titulo" or estilo == "producto" or estilo == "total":
        return CHICO_OFF + ALIGN_CENTER + BOLD_ON if estilo == "titulo" else CHICO_OFF + ALIGN_LEFT + BOLD_ON
    if estilo == "detalle":
        return BOLD_OFF + ALIGN_LEFT + CHICO_ON
    if estilo == "saludo" or estilo == "texto":
        return CHICO_OFF + BOLD_OFF + ALIGN_CENTER
    return CHICO_OFF + BOLD_OFF + ALIGN_LEFT


def _nombre(nombre: str) -> str:
    limpio = " ".join(nombre.replace("🏷️ ", "*OFER* ").replace("🔥 [OFERTA] ", "*OFER* ").split())
    return limpio or "Sin nombre"


def _ficha(empresa: str = "") -> dict:
    if empresa:
        return {"empresa": empresa, "cuit": "", "direccion": "", "telefono": ""}
    try:
        from src.config import config

        tel = str(config.get("business_phone") or config.get("phone") or "").strip()
        return {
            "empresa": str(config.get("business_name") or "Mi Comercio"),
            "cuit": str(config.get("business_cuit") or "").strip(),
            "direccion": str(config.get("business_address") or config.get("address") or "").strip(),
            "telefono": f"Tel: {tel}" if tel else "",
        }
    except Exception:
        return {"empresa": "Mi Comercio", "cuit": "", "direccion": "", "telefono": ""}


def _saludo() -> str:
    hora = datetime.now().hour
    if 5 <= hora < 13:
        return "Buenos dias!"
    if 13 <= hora < 20:
        return "Buenas tardes!"
    return "Buenas noches!"


def _cabe(columnas: int, texto: str) -> str:
    limpio = " ".join(str(texto or "").split())
    return limpio[:columnas]


def _par(columnas: int, izquierda: str, derecha: str) -> str:
    izq = str(izquierda or "")
    der = str(derecha or "")
    if len(izq) + 1 + len(der) > columnas:
        der = der[: max(0, columnas - len(izq) - 1)]
    hueco = columnas - len(izq) - len(der)
    if hueco < 1:
        return (izq + " " + der)[:columnas]
    return izq + (" " * hueco) + der
