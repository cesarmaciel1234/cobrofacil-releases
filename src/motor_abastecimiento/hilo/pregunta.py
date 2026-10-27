"""Mini motor. Solo le pregunta al inventario. No calcula el pedido."""

from src.logger import logger


def preguntar_alarma() -> list:
    """Lee la planilla del inventario. No la reescribe y no toca productos."""
    try:
        from src.motor_inventario.planilla.orquestador import MotorPlanilla

        return list(MotorPlanilla.leer() or [])
    except Exception as e:
        logger.error("Pedidos no pudo leer la planilla de reposición: %s", e)
        return []
