"""Qué hace la esclava apenas entra a la maestra."""

from __future__ import annotations

import logging

from src.central_red_global.sync_tienda.png.esclava import bajar_pngs_de_maestra

logger = logging.getLogger("PunPro")


def _traer_publicidad_maestra():
    try:
        from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad

        motor_publicidad.cargar_configuracion(forzar=True)
        lista = motor_publicidad.as_dict()
        logger.info(
            "Esclava: publicidad de la maestra (%s nombres, %s ids)",
            len(lista.get("promocionados") or []),
            len(lista.get("ids") or []),
        )
    except Exception as exc:
        logger.warning("Sync publicidad al conectar esclava: %s", exc)


def _patear_tv():
    try:
        from PyQt6.QtCore import QTimer
        from src.carteleria.lanzador_tv import lanzador_directo as ld

        inst = getattr(ld, "_lanzador_directo", None)
        if inst is not None and getattr(inst, "_vivo", False):
            QTimer.singleShot(0, inst._sincronizar)
    except Exception:
        pass


def al_conectar_esclava() -> int:
    n_png = 0
    try:
        n_png = bajar_pngs_de_maestra()
        if n_png:
            logger.info("Esclava: %s PNG copiados desde la maestra", n_png)
    except Exception as exc:
        logger.warning("Sync PNG al conectar esclava: %s", exc)
    _traer_publicidad_maestra()
    _patear_tv()
    return n_png
