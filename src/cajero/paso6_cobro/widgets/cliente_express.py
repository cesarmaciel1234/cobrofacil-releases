"""El diálogo vive en el cerebro de cuentas. Acá queda el nombre viejo."""
from src.clientes_fiado.interfaz.cobro.cliente_express import (
    DialogoClienteExpressPaso1,
    DialogoClienteExpressPaso2,
    abrir_cliente_express,
    sonar_alarma_limite_fiado,
    sonar_dni_no_coincide,
)

__all__ = [
    "DialogoClienteExpressPaso1",
    "DialogoClienteExpressPaso2",
    "abrir_cliente_express",
    "sonar_alarma_limite_fiado",
    "sonar_dni_no_coincide",
]
