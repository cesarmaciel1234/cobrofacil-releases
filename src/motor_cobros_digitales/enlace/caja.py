"""Los tickets que firmó el cajero en esta PC (`reportes/mp_vinculos.json`) suben a la tienda."""

from __future__ import annotations

from src.logger import logger
from src.motor_cobros_digitales.libro import tabla


def subir_vinculos() -> bool:
    """Lee el libro local del cobro (solo lectura) y pasa cada par pago→ticket a `mp_pagos` como enlace 'caja'."""
    try:
        from src.cajero.paso6_cobro.vinculo_mp.libro import _leer

        pares = []
        for mes in _leer().values():
            if not isinstance(mes, dict):
                continue
            for id_pago, dato in mes.items():
                if isinstance(dato, dict) and dato.get("ticket"):
                    pares.append((id_pago, dato["ticket"]))
        return tabla.firmar_caja(pares)
    except Exception as error:
        logger.warning(f"[Cobros digitales] No se pudieron subir los vínculos de caja: {error}")
        return False
