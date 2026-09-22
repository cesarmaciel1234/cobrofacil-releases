from abc import ABC, abstractmethod
from typing import Tuple, Optional
from src.cajero.paso6_cobro.motor_pagos.dtos.orden_cobro import OrdenCobroDTO

class BaseProcesoPago(ABC):
    """
    Contrato estricto para cualquier subproceso de pago.
    Ningún proceso interactúa con el orquestador más allá de retornar (Éxito, Mensaje).
    """

    def __init__(self, orden: OrdenCobroDTO):
        self.orden = orden

    @abstractmethod
    def ejecutar(self) -> Tuple[bool, Optional[str]]:
        """
        Punto de entrada único del subproceso.
        Aquí adentro, el método puede abrir ventanas, consultar APIs,
        abrir cajones de dinero, o guardar en la base de datos.

        Al final, solo puede responder:
        - True, "Mensaje de éxito"
        - False, "Mensaje de error o cancelación"
        """
        pass
