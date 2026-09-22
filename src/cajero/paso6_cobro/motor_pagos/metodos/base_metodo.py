from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional

class MetodoPagoBase(ABC):
    """
    Clase abstracta que define el contrato (interfaz) para cualquier método de pago.
    Cada método específico (Efectivo, Tarjeta, QR, etc.) DEBE implementar estos métodos.
    """

    def __init__(self, datos_transaccion: Dict[str, Any]):
        self.datos = datos_transaccion

    @abstractmethod
    def validar_datos(self) -> Tuple[bool, Optional[str]]:
        """Verifica que los datos ingresados sean suficientes para este método."""
        pass

    @abstractmethod
    def procesar_cobro(self) -> Tuple[bool, Optional[str]]:
        """
        Ejecuta la lógica central del cobro.
        (Ej: Consultar API de MercadoPago, validar límite de crédito del cliente).
        """
        pass

    @abstractmethod
    def guardar_en_db(self) -> Tuple[bool, Optional[str], Optional[int]]:
        """Guarda la venta en la base de datos y retorna (Éxito, Mensaje, ID_Venta)."""
        pass

    @abstractmethod
    def acciones_post_cobro(self, id_venta: int) -> None:
        """Acciones físicas o en segundo plano (Imprimir ticket, Abrir cajón)."""
        pass

    def ejecutar(self) -> Tuple[bool, Optional[str]]:
        """
        Orquesta el ciclo de vida completo del método.
        No se recomienda sobrescribir este método a menos que el flujo de pago cambie drásticamente.
        """
        exito_val, msg_val = self.validar_datos()
        if not exito_val:
            return False, msg_val

        exito_proc, msg_proc = self.procesar_cobro()
        if not exito_proc:
            return False, msg_proc

        exito_db, msg_db, id_venta = self.guardar_en_db()
        if not exito_db or not id_venta:
            return False, msg_db

        self.acciones_post_cobro(id_venta)

        return True, "Transacción completada con éxito."
