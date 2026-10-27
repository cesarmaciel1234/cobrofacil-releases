"""Hilo propio de la planilla. La venta no lo espera."""

import logging
import threading

logger = logging.getLogger("planilla_reposicion")

INTERVALO_SEG = 15
_hilo = None
_guardia = threading.Lock()
_primer_pase = threading.Event()
_despertar = threading.Event()


def arrancar_hilo():
    global _hilo
    with _guardia:
        if _hilo is not None and _hilo.is_alive():
            return
        _hilo = threading.Thread(target=_bucle, name="planilla-reposicion", daemon=True)
        _hilo.start()


def avisar_planilla():
    """Pide un pase pronto. No lee stock y no escribe la planilla."""
    arrancar_hilo()
    _despertar.set()


def esperar_primer_pase(segundos: float) -> bool:
    return _primer_pase.wait(segundos)


def _bucle():
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    while True:
        _despertar.clear()
        try:
            MotorPlanilla.actualizar()
        except Exception as e:
            logger.error("Pase de planilla falló: %s", e)
        _primer_pase.set()
        _despertar.wait(INTERVALO_SEG)
