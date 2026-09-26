"""Despacha el medio del abono. No importa el paso 6."""
from src.clientes_fiado.interfaz.cobro.medios.efectivo import cobrar as cobrar_efectivo
from src.clientes_fiado.interfaz.cobro.medios.mixto import cobrar as cobrar_mixto
from src.clientes_fiado.interfaz.cobro.medios.qr import cobrar as cobrar_qr
from src.clientes_fiado.interfaz.cobro.medios.resultado import ResultadoMedio
from src.clientes_fiado.interfaz.cobro.medios.tarjeta import cobrar as cobrar_tarjeta
from src.clientes_fiado.interfaz.cobro.medios.transferencia import cobrar as cobrar_transferencia

REGISTRO = {
    "Efectivo": cobrar_efectivo,
    "Transferencia": cobrar_transferencia,
    "Tarjeta": cobrar_tarjeta,
    "QR": cobrar_qr,
    "Mixto": cobrar_mixto,
}


def cobrar(medio, monto, partes=None):
    nombre = str(medio or "")
    if nombre == "Mixto":
        return cobrar_mixto(monto, partes)
    funcion = REGISTRO.get(nombre)
    if funcion is None:
        return ResultadoMedio(False, medio, False, "Medio desconocido")
    return funcion(monto)
