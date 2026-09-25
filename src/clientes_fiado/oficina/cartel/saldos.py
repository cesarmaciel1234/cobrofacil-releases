from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta


class SubmotorSaldos:
    """Lee deuda y disponible. Si un número no carga, ese lado queda vacío."""

    def leer(self, ficha):
        saldo = None
        disponible = None
        try:
            saldo = float((ficha or {}).get("deuda_actual") or 0)
        except Exception:
            saldo = None
        try:
            disponible = float(MotorCuenta().credito_disponible(ficha))
        except Exception:
            disponible = None
        return saldo, disponible
