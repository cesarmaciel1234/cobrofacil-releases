from src.clientes_fiado.garante.orden.orden import OrdenCobro
from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta


class MotorClienteExpress:
    """Identifica por nombre y autoriza el cupo. No guarda la venta."""

    def __init__(self):
        self.cuenta = MotorCuenta()

    def identificar(self, nombre):
        return self.cuenta.identificar_nombre(nombre)

    def autorizar(self, cliente_id, monto):
        if not cliente_id:
            return OrdenCobro(False, "Clientes", motivo="No se pudo identificar al cliente.")
        cliente = self.cuenta.obtener(cliente_id)
        if not cliente:
            return OrdenCobro(False, "Clientes", motivo="Cliente no encontrado en la base de datos.")
        if self.cuenta.limite_excedido(cliente, monto):
            disp = self.cuenta.credito_disponible(cliente)
            return OrdenCobro(
                False,
                "Clientes",
                cliente_id=cliente_id,
                cliente=cliente,
                motivo=f"Crédito insuficiente. Disp: ${disp:.2f}",
            )
        return OrdenCobro(True, "Clientes", cliente_id=dict(cliente).get("id"), cliente=cliente)
