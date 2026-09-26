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
        self._excepcion = None

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

    def abonar(self, cliente_id, monto, descripcion, medio="", perfil="", quien=""):
        return self.cuenta.abonar(cliente_id, monto, descripcion, medio, perfil, quien)

    def abonar_caja(self, cliente_id, monto, deuda_anterior, medio="Efectivo", perfil="Cajero", quien="", nota=""):
        """El abono del Centro de Cobranzas. Lo usan F6 y el botón Abonar del admin."""
        quien_limpio = " ".join(str(quien or "").split())
        medio_limpio = str(medio or "Efectivo").strip() or "Efectivo"
        perfil_limpio = str(perfil or "").strip() or "Cajero"
        firma = f"{perfil_limpio} {quien_limpio}".strip()
        extra = f": {nota}" if str(nota or "").strip() else ""
        descripcion = f"{firma} ({medio_limpio}{extra})"
        exito, nuevo_saldo, nombre = self.abonar(
            cliente_id, monto, descripcion, medio_limpio, perfil_limpio, quien_limpio
        )
        if exito:
            try:
                from src.hardware.printer import printer_manager

                printer_manager.imprimir_saldo_fiado(nombre, deuda_anterior, monto, nuevo_saldo)
            except Exception:
                pass
        return exito, nuevo_saldo, nombre

    def resumen_cuentas(self):
        return self.cuenta.pagos_del_dia(), self.cuenta.deuda_total()

    def total_cobros(self):
        return self.cuenta.total_cobros()

    def listar_cobros(self):
        return self.cuenta.listar_cobros()

    def cargar_manual(self, cliente_id, monto, descripcion):
        return self.cuenta.cargar_manual(cliente_id, monto, descripcion)

    def ventas_sin_cargo(self):
        return self.cuenta.ventas_sin_cargo()

    def anotar_faltante(self, venta_id):
        return self.cuenta.anotar_faltante(venta_id)

    def cartel(self, cliente):
        try:
            return self.cartel_cobro.armar(cliente)
        except Exception:
            return {"saludo": "Sin datos", "saldo": None, "disponible": None}

    def conceder_excepcion(self, cliente_id, monto, quien):
        from src.utils.dinero import redondear_dinero

        self._excepcion = {
            "cliente_id": int(cliente_id),
            "monto": redondear_dinero(monto),
            "quien": str(quien or "Admin").strip() or "Admin",
        }

    def soltar_excepcion(self):
        self._excepcion = None

    def excepcion_vigente(self, cliente_id, monto):
        return bool(self._mirar_excepcion(cliente_id, monto))

    def _mirar_excepcion(self, cliente_id, monto):
        from src.utils.dinero import redondear_dinero

        marca = self._excepcion
        if not marca:
            return ""
        try:
            mismo = int(marca.get("cliente_id")) == int(cliente_id)
            mismo = mismo and marca.get("monto") == redondear_dinero(monto)
        except (TypeError, ValueError):
            mismo = False
        if not mismo:
            return ""
        return str(marca.get("quien") or "Admin")

    def autorizar(self, metodo, cliente_id, monto):
        nombre = str(metodo or "")
        if nombre not in ("Fiado", "Clientes"):
            return OrdenCobro(False, nombre, motivo="Este medio no es una cuenta de fiado.")
        quien = self._mirar_excepcion(cliente_id, monto)
        if quien:
            cliente = self.cuenta.obtener(cliente_id)
            if cliente:
                self._excepcion = None
                return OrdenCobro(
                    True,
                    nombre,
                    cliente_id=dict(cliente).get("id"),
                    cliente=cliente,
                    excepcion=quien,
                )
        if nombre == "Fiado":
            return self.fiado.autorizar(cliente_id, monto)
        return self.cliente.autorizar(cliente_id, monto)

    def cobrar(self, metodo, datos):
        datos = dict(datos or {})
        orden = self.autorizar(metodo, datos.get("cliente_id"), datos.get("total_final"))
        if not orden.ok:
            return False, orden.motivo
        from src.clientes_fiado.garante.despacho.despacho import entregar

        return entregar(orden, datos)


cerebro = CerebroClientesFiado()
