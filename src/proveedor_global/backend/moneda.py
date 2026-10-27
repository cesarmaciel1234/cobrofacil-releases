"""Moneda del negocio para pedido, recepción y romaneo.

El símbolo y el código salen de la config de la tienda. Un símbolo que no es
peso (euro, real, sol) manda sobre un código ARS que nadie cambió.
"""

from __future__ import annotations

_SIMBOLO_A_CODIGO = {
    "€": "EUR",
    "S/": "PEN",
    "Q": "GTQ",
    "L": "HNL",
    "Bs": "BOB",
    "R$": "BRL",
    "¥": "JPY",
    "£": "GBP",
}

_MILES_PUNTO = {"ARS", "EUR", "BRL", "CLP", "COP", "UYU", "PYG", "BOB", "PEN"}
_SIN_CENTAVOS = {"CLP", "JPY", "PYG"}


def simbolo() -> str:
    from src.config import config

    return str(config.get("currency_symbol", "$") or "$").strip() or "$"


def codigo() -> str:
    from src.config import config

    marca = simbolo()
    guardado = str(config.get("currency_code", "ARS") or "ARS").strip().upper()
    forzado = _SIMBOLO_A_CODIGO.get(marca)
    if forzado and guardado in ("", "ARS"):
        return forzado
    return guardado or "ARS"


def contable():
    """El enum del asiento. Si el código no está en el plan, queda en la moneda local ARS."""
    from src.contabilidad.schema_fiscal import Moneda

    try:
        return Moneda(codigo())
    except ValueError:
        return Moneda.ARS


def texto(numero) -> str:
    try:
        valor = float(numero or 0)
    except (TypeError, ValueError):
        valor = 0.0
    negativo = valor < 0
    valor = abs(valor)
    cod = codigo()
    if cod in _SIN_CENTAVOS:
        cuerpo = _miles(int(round(valor)), cod)
        salida = f"{simbolo()} {cuerpo}"
    else:
        entero = int(valor)
        dec = int(round((valor - entero) * 100))
        if dec == 100:
            entero += 1
            dec = 0
        sep = "," if cod in _MILES_PUNTO else "."
        salida = f"{simbolo()} {_miles(entero, cod)}{sep}{dec:02d}"
    return f"-{salida}" if negativo else salida


def leer(crudo) -> float:
    """Lee $2.250,00 y también $2,250.00. El último separador es el decimal."""
    bruto = str(crudo or "").strip()
    negativo = bruto.startswith("-")
    digitos = "".join(ch for ch in bruto if ch.isdigit() or ch in ".,")
    if not digitos:
        return 0.0
    if "," in digitos and "." in digitos:
        if digitos.rfind(",") > digitos.rfind("."):
            digitos = digitos.replace(".", "").replace(",", ".")
        else:
            digitos = digitos.replace(",", "")
    elif "," in digitos:
        cola = digitos.split(",")[-1]
        digitos = digitos.replace(",", ".") if len(cola) == 2 else digitos.replace(",", "")
    elif "." in digitos and codigo() in _MILES_PUNTO:
        partes = digitos.split(".")
        if len(partes[-1]) == 3:
            digitos = "".join(partes)
    valor = float(digitos)
    return -valor if negativo else valor


def _miles(entero: int, cod: str) -> str:
    sep = "." if cod in _MILES_PUNTO else ","
    return f"{int(entero):,}".replace(",", sep)
