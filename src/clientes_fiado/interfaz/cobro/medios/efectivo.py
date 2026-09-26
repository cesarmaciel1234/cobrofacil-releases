"""Efectivo de un abono. Entra al cajón. No abre la venta."""
from src.clientes_fiado.interfaz.cobro.medios.resultado import ResultadoMedio


def cobrar(monto):
    if float(monto or 0) <= 0:
        return ResultadoMedio(False, "Efectivo", False, "Sin monto")
    return ResultadoMedio(True, "Efectivo", True, monto_caja=float(monto))
