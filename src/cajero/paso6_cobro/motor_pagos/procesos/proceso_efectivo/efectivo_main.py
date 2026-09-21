from typing import Tuple, Optional
from PyQt6.QtWidgets import QDialog
from src.cajero.paso6_cobro.motor_pagos.dtos.orden_cobro import OrdenCobroDTO
from src.cajero.paso6_cobro.motor_pagos.procesos.base_proceso import BaseProcesoPago

class ProcesoEfectivo(BaseProcesoPago):
    """
    Subproceso independiente para manejar cobros en Efectivo.
    Se encarga de levantar su propia UI para pedir el monto recibido.
    """
    
    def ejecutar(self) -> Tuple[bool, Optional[str]]:
        # 1. Levantar la UI independiente para pedir el monto
        # from .ui.dialogo_monto_efectivo import DialogoMontoEfectivo
        # dlg = DialogoMontoEfectivo(self.orden)
        # if not dlg.exec():
        #     return False, "Cancelado por el cajero (volvió a selección de método)."
        
        # 2. Obtener monto ingresado y calcular vuelto
        # p1 = dlg.get_monto_recibido()
        
        # 3. Guardar en DB (delegando a controller de DB)
        
        # 4. Abrir cajón y ticket (delegando a periféricos)
        
        return True, "Efectivo cobrado con éxito."
