from typing import Tuple, Optional

from src.cajero.paso6_cobro.motor_pagos.dtos.orden_cobro import OrdenCobroDTO
from src.cajero.paso6_cobro.motor_pagos.procesos.base_proceso import BaseProcesoPago
from src.cajero.paso6_cobro.motor_pagos.motores.efectivo.motor import MotorEfectivo


class ProcesoEfectivo(BaseProcesoPago):
    def ejecutar(self) -> Tuple[bool, Optional[str]]:
        o: OrdenCobroDTO = self.orden
        return MotorEfectivo().ejecutar({
            "total_final": o.total_final,
            "p1": getattr(o, "legacy_p1", None),
            "p2": getattr(o, "legacy_p2", None),
            "items_carrito": o.items_carrito,
            "cajero": o.cajero_actual,
            "cajero_sec": o.cajero_secundario,
            "descuento": o.monto_descuento,
            "recargo": o.monto_recargo,
            "oferta": o.descuentaso_oferta,
            "imprimir": o.imprimir_ticket,
            "force_fiscal": o.forzar_fiscal,
            "cliente_id": getattr(o, "legacy_cliente_id", None),
            "nombre_pendiente": getattr(o, "legacy_nombre_pendiente", None),
        })
