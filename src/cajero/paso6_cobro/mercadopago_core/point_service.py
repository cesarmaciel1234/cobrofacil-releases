from PyQt6.QtWidgets import QMessageBox
from src.config import config
from src.utils.parser import parse_float_regional

class PointService:
    def __init__(self, parent_cobro):
        self.parent = parent_cobro

    def procesar_pago_mercadopago_point(self, cerrar=True):
        if getattr(self.parent, "_point_en_curso", False):
            return None
        self.parent._point_en_curso = True
        try:
            return self._cobrar(cerrar)
        finally:
            self.parent._point_en_curso = False

    def _cobrar(self, cerrar):
        config._load_config()
        token = config.get("mp_access_token", "")
        device_id = config.get("mp_device_id", "")

        if not token or not device_id:
            self._avisar("Falta el token o la terminal Point en la configuración del TPV.")
            return False

        # Validar que el terminal esté en modo PDV y pertenezca a esta cuenta
        from src.cajero.paso6_cobro.mercadopago_core.terminal_validator import validar_terminal_point
        valido, motivo = validar_terminal_point(token, device_id)
        if not valido:
            if motivo == "sin_terminal":
                self._avisar("El terminal Point no está vinculado a esta cuenta de Mercado Pago. Verificá el Device ID en Admin → Terminales TPV.")
            elif motivo == "standalone":
                self._avisar("El terminal Point está en modo STANDALONE. Cambialo a modo PDV desde Mercado Pago para que reciba montos.")
            elif motivo == "red":
                self._avisar("No se pudo conectar con Mercado Pago para validar el terminal. Verificá tu conexión a internet.")
            else:
                self._avisar("Error al validar el terminal Point.")
            return None

        if self.parent.current_metodo not in ["Tarjeta", "Mixto"]:
            self.parent.set_metodo("Tarjeta")

        if self.parent.current_metodo == "Mixto":
            if getattr(self.parent, 'valores_mixtos', None):
                monto = self.parent.valores_mixtos.get("tarjeta", 0.0)
            else:
                monto = 0.0
        else:
            monto_str = self.parent.txt_pago.text().replace("$", "").replace(" ", "").strip()
            try:
                monto = parse_float_regional(monto_str)
            except Exception:
                monto = self.parent.total_final

        if monto <= 0:
            msg = "El monto de Tarjeta (Point) en pago Mixto es cero." if self.parent.current_metodo == "Mixto" else "Ingrese un monto a cobrar válido."
            if cerrar:
                QMessageBox.warning(self.parent, "Monto inválido", msg)
            else:
                self._avisar(msg)
            return None

        espera = getattr(self.parent, "espera_point", None)
        if espera is None:
            self._avisar("La terminal no recibió el monto.")
            return None
        if not espera.esperar(token, device_id, monto):
            self._avisar_motivo(espera.motivo)
            return None
        if self.parent.current_metodo not in ("Tarjeta", "Mixto"):
            return None
        if cerrar:
            self.parent._point_en_curso = False
            self.parent.txt_pago.setText(str(monto))
            self.parent._es_autonomo = True
            self.parent.finalizar(True)
        return True

    def _avisar_motivo(self, motivo):
        if motivo in ("usuario", "cancelo"):
            return
        if motivo == "ocupada":
            self._avisar("La terminal ya tiene un cobro. Cancelalo en el Point y reenviá.")
        elif motivo == "minimo":
            self._avisar("El Point cobra desde $15.")
        elif motivo == "sin_terminal":
            self._avisar("Falta el token o la terminal Point en la configuración del TPV.")
        elif motivo == "otra_cuenta":
            self._avisar("El Point está abierto con otra cuenta de Mercado Pago que el token de la caja. Logueá la misma cuenta en el terminal o actualizá el token en Admin -> Terminales TPV.")
        elif motivo == "cancelo":
            self._avisar("La terminal canceló el cobro. Enter registra la venta.")
        elif motivo:
            self._avisar("La terminal no recibió el monto.")

    def _avisar(self, texto):
        aviso = getattr(self.parent, "_avisar", None)
        if aviso:
            aviso(texto)
            return
        QMessageBox.critical(self.parent, "Error MP", texto)
