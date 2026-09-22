from typing import Any, Dict, Tuple

from src.cajero.paso6_cobro.motor_pagos.motores import REGISTRO


class MotorPrincipalCobros:
    """Despacha al motor del medio. No cobra ni escribe en BD."""

    @classmethod
    def iniciar_transaccion(cls, metodo: str, datos_ui: Dict[str, Any]) -> Tuple[bool, str]:
        datos = dict(datos_ui or {})
        datos["metodo"] = metodo
        clave = str(metodo or "").lower().strip()
        motor_cls = REGISTRO.get(clave)
        if not motor_cls:
            return False, f"Metodo de pago no registrado: {metodo}"
        return motor_cls().ejecutar(datos)
