"""Mixto de un abono: dos medios. Solo el efectivo entra al cajón. No abre la venta."""
from src.clientes_fiado.interfaz.cobro.medios.resultado import ResultadoMedio
from src.utils.dinero import redondear_dinero

CLAVES = ("Efectivo", "Transferencia", "Tarjeta", "QR")


def cobrar(monto, partes=None):
    datos = partes or {}
    limpios = {clave: redondear_dinero(datos.get(clave) or 0) for clave in CLAVES}
    activos = {clave: valor for clave, valor in limpios.items() if valor > 0.009}
    if len(activos) != 2:
        return ResultadoMedio(False, "Mixto", False, "El mixto admite solo dos medios.")
    total = redondear_dinero(monto)
    suma = redondear_dinero(sum(activos.values()))
    if abs(suma - total) > 0.02:
        return ResultadoMedio(False, "Mixto", False, "La suma no cubre el abono.")
    efectivo = limpios["Efectivo"]
    detalle = " + ".join(f"{clave} {valor:.2f}" for clave, valor in activos.items())
    return ResultadoMedio(
        True, "Mixto", efectivo > 0.009, detalle, monto_caja=efectivo,
    )
