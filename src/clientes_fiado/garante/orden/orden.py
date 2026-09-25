class OrdenCobro:
    """La orden que el cerebro entrega al motor de cobro. Si `ok` es falso, no se guarda la venta."""

    def __init__(self, ok, metodo, cliente_id=None, cliente=None, motivo=""):
        self.ok = bool(ok)
        self.metodo = metodo
        self.cliente_id = cliente_id
        self.cliente = cliente
        self.motivo = motivo or ""
