"""El diálogo vive en el cerebro de cuentas. Acá queda el nombre viejo."""
from src.clientes_fiado.interfaz.cobro.fiado_express import (
    DialogoFiadoExpress,
    DialogoFiadoExpressConfirmacion,
    DialogoFiadoExpressPaso1,
    sonar_alarma_limite_fiado,
    sonar_dni_no_coincide,
)

__all__ = [
    "DialogoFiadoExpress",
    "DialogoFiadoExpressPaso1",
    "DialogoFiadoExpressConfirmacion",
    "sonar_alarma_limite_fiado",
    "sonar_dni_no_coincide",
]
