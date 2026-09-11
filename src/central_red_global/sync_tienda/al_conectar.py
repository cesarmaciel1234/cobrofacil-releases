"""Qué hace la esclava apenas entra a la maestra."""

from __future__ import annotations

import logging

from src.central_red_global.sync_tienda.png.esclava import bajar_pngs_de_maestra

logger = logging.getLogger("PunPro")


def al_conectar_esclava() -> int:
    try:
        n_png = bajar_pngs_de_maestra()
        if n_png:
            logger.info("Esclava: %s PNG copiados desde la maestra", n_png)
        return n_png
    except Exception as exc:
        logger.warning("Sync PNG al conectar esclava: %s", exc)
        return 0
