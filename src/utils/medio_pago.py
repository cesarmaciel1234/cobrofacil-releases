"""Nombre del medio de pago para mostrar en pantalla.

En la base el medio queda como se guardó ("Clientes", "Fiado", "Mixto (Cliente)").
El fiscal, las métricas y los filtros SQL leen ese valor: no se cambia.
Acá solo se traduce lo que ve el usuario: la cuenta del cliente se llama "Crédito".
La tarjeta sigue siendo "Tarjeta".
"""

import re

_CUENTA = ("FIADO", "CLIENTES", "CLIENTE", "CUENTA CORRIENTE")
_PALABRA = re.compile(r"\b(clientes|cliente|fiado)\b", re.IGNORECASE)


def etiqueta_pago(metodo) -> str:
    """'Clientes' / 'Fiado' -> 'Crédito'. 'Mixto (Cliente)' -> 'Mixto (Crédito)'. El resto, igual."""
    texto = str(metodo or "").strip()
    if not texto:
        return texto
    if texto.upper() in _CUENTA:
        return "Crédito"
    if texto.upper().startswith("MIXTO"):
        return _PALABRA.sub("Crédito", texto)
    return texto


def es_filtro_credito(filtro) -> bool:
    """True si el filtro elegido en pantalla es la cuenta del cliente."""
    return str(filtro or "").strip().upper() in ("CRÉDITO", "CREDITO", "FIADO", "CLIENTES")
