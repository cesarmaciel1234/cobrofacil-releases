"""QR de un abono. No entra al cajón y no abre la venta."""
from src.clientes_fiado.interfaz.cobro.medios.resultado import ResultadoMedio


def cobrar(monto):
    if float(monto or 0) <= 0:
        return ResultadoMedio(False, "QR", False, "Sin monto")
    return ResultadoMedio(True, "QR", False)
