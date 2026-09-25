class MotorFiado:
    """Recibe la venta de fiado y le pide la orden ok al cerebro. No mira los otros medios."""

    def ejecutar(self, datos):
        from src.clientes_fiado.cerebro.cerebro import cerebro

        return cerebro.cobrar("Fiado", datos)
