from src.clientes_fiado.garante.cuenta_corriente.motor import MotorClienteExpress
from src.clientes_fiado.garante.fiado.motor import MotorFiadoExpress
from src.clientes_fiado.garante.orden.orden import OrdenCobro
from src.clientes_fiado.oficina.cartel.motor import MotorCartel
from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta


class CerebroClientesFiado:
    """Única puerta de las cuentas. Autoriza y, si corresponde, manda la orden ok al cobro."""

    def __init__(self):
        self.cuenta = MotorCuenta()
        self.fiado = MotorFiadoExpress()
        self.cliente = MotorClienteExpress()
        self.cartel_cobro = MotorCartel()

    def normalizar_dni(self, dni):
        return self.cuenta.normalizar_dni(dni)

    def identificar_dni(self, dni):
        return self.fiado.identificar(dni)

    def identificar_nombre(self, nombre):
        return self.cliente.identificar(nombre)

    def obtener(self, cliente_id):
        return self.cuenta.obtener(cliente_id)

    def credito_disponible(self, cliente):
        return self.cuenta.credito_disponible(cliente)

    def limite_excedido(self, cliente, monto):
        return self.cuenta.limite_excedido(cliente, monto)

    def buscar_por_dni(self, dni):
        return self.cuenta.buscar_por_dni(dni)

    def buscar_por_nombre(self, nombre):
        return self.cuenta.buscar_por_nombre(nombre)

    def sugerir(self, texto):
        return self.cuenta.sugerir_nombres(texto)

    def buscar(self, texto):
        return self.cuenta.buscar(texto)

    def listar(self):
        return self.cuenta.listar()

    def listar_con_deuda(self):
        return self.cuenta.listar_con_deuda()

    def ultimo_cargo(self, cliente_id):
        return self.cuenta.ultimo_cargo(cliente_id)

    def movimientos(self, cliente_id):
        return self.cuenta.movimientos(cliente_id)

    def alta_regular(self, nombre, telefono, limite, dni):
        return self.cuenta.alta_regular(nombre, telefono, limite, dni)

    def actualizar_existente(self, cliente_id, nombre, telefono, limite, dni):
        return self.cuenta.actualizar_existente(cliente_id, nombre, telefono, limite, dni)

    def actualizar_ficha(self, cliente_id, nombre, dni, telefono, direccion, tipo):
        return self.cuenta.actualizar_ficha(cliente_id, nombre, dni, telefono, direccion, tipo)

    def fijar_limite(self, cliente_id, limite):
        return self.cuenta.fijar_limite(cliente_id, limite)

    def abonar(self, cliente_id, monto, descripcion):
        return self.cuenta.abonar(cliente_id, monto, descripcion)

    def abonar_caja(self, cliente_id, monto, deuda_anterior):
        """El abono del Centro de Cobranzas. Lo usan F6 y el botón Abonar del admin."""
        exito, nuevo_saldo, nombre = self.abonar(cliente_id, monto, "Abono Fiado en Caja")
        if exito:
            try:
                from src.hardware.printer import printer_manager

                printer_manager.imprimir_saldo_fiado(nombre, deuda_anterior, monto, nuevo_saldo)
            except Exception:
                pass
        return exito, nuevo_saldo, nombre

    def cargar_manual(self, cliente_id, monto, descripcion):
        return self.cuenta.cargar_manual(cliente_id, monto, descripcion)

    def cartel(self, cliente):
        try:
            return self.cartel_cobro.armar(cliente)
        except Exception:
            return {"saludo": "Sin datos", "saldo": None, "disponible": None}

    def autorizar(self, metodo, cliente_id, monto):
        nombre = str(metodo or "")
        if nombre == "Fiado":
            return self.fiado.autorizar(cliente_id, monto)
        if nombre == "Clientes":
            return self.cliente.autorizar(cliente_id, monto)
        return OrdenCobro(False, nombre, motivo="Este medio no es una cuenta de fiado.")

    def cobrar(self, metodo, datos):
        datos = dict(datos or {})
        orden = self.autorizar(metodo, datos.get("cliente_id"), datos.get("total_final"))
        if not orden.ok:
            return False, orden.motivo
        from src.clientes_fiado.garante.despacho.despacho import entregar

        return entregar(orden, datos)


cerebro = CerebroClientesFiado()
