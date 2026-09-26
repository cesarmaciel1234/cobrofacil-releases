"""Lo que devuelve un medio cuando el pago no es una venta."""


class ResultadoMedio:
    def __init__(self, ok, medio, entra_caja=False, detalle="", monto_caja=0):
        self.ok = bool(ok)
        self.medio = str(medio or "")
        self.entra_caja = bool(entra_caja)
        self.detalle = str(detalle or "")
        self.monto_caja = float(monto_caja or 0)
