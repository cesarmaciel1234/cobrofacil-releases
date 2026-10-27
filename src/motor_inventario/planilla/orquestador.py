"""Orquestador de la planilla. El stock no lo conoce. Pedidos no lo escriben."""

import logging
import threading

logger = logging.getLogger("planilla_reposicion")

_datos = threading.Lock()


def _cantidad(stock: float, piso: float, techo: float) -> float:
    """Hasta el techo si está cargado. Hasta el piso si no hay techo. Si no hay ninguno, cero."""
    if techo > piso and techo > stock:
        return techo - stock
    if piso > 0:
        falta = piso - stock
        return falta if falta > 0 else 0.0
    return 0.0


def _motivo(stock: float, piso: float, techo: float, cantidad: float) -> str:
    if cantidad <= 0 and piso <= 0 and techo <= stock:
        return "sin_piso"
    if piso > 0 and stock <= piso:
        return "reposicion"
    if stock <= 0:
        return "critico"
    return "reposicion"


class MotorPlanilla:
    """Mira mínimo y máximo, y deja el resultado en su planilla."""

    @staticmethod
    def actualizar() -> int:
        """Lee el stock ya guardado y reescribe la planilla. No corre dentro de la venta."""
        from src.motor_inventario.alarma.consulta import productos_con_alarma_reposicion
        from src.motor_inventario.planilla import repo

        try:
            crudas = productos_con_alarma_reposicion()
            filas = []
            for r in crudas or []:
                stock = float(r.get("stock") or 0)
                piso = float(r.get("stock_minimo") or 0)
                techo = float(r.get("stock_maximo") or 0)
                cantidad = _cantidad(stock, piso, techo)
                filas.append({
                    **r,
                    "cantidad_sugerida": cantidad,
                    "motivo": _motivo(stock, piso, techo, cantidad),
                })
            with _datos:
                repo.reemplazar(filas)
            logger.info("Planilla de reposición: %s productos.", len(filas))
            return len(filas)
        except Exception as e:
            logger.error("La planilla no se pudo actualizar: %s", e)
            return 0

    @staticmethod
    def leer() -> list:
        """Lo que pedidos puede mirar. Solo la planilla."""
        from src.motor_inventario.planilla import repo

        try:
            with _datos:
                return repo.leer()
        except Exception as e:
            logger.error("No se pudo leer la planilla de reposición: %s", e)
            return []

    @staticmethod
    def avisar():
        """Despierta el hilo de la planilla. No escribe la hoja desde acá."""
        from src.motor_inventario.planilla.hilo import avisar_planilla

        avisar_planilla()

    @staticmethod
    def arrancar():
        from src.motor_inventario.planilla.hilo import arrancar_hilo

        arrancar_hilo()

    @staticmethod
    def esperar(segundos: float = 8) -> bool:
        from src.motor_inventario.planilla.hilo import esperar_primer_pase

        return esperar_primer_pase(segundos)
