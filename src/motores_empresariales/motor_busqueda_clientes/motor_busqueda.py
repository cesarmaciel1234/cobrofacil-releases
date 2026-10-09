from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from src.clientes_fiado.cerebro.cerebro import cerebro
import logging

class MotorBusquedaClientes(QObject):
    sugerencias_listas = pyqtSignal(list)
    limite_aprobado = pyqtSignal(dict) # Emite el cartel con nombre, limite, compra
    error_busqueda = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('PunPro')
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._buscar_real)
        self._ultimo_texto = ""
        self._monto_venta = 0.0

    def set_monto_venta(self, monto):
        self._monto_venta = float(monto or 0.0)

    def buscar_texto(self, texto):
        self._ultimo_texto = texto.strip()
        if len(self._ultimo_texto) >= 2:
            self._timer.start(300)
        else:
            self.sugerencias_listas.emit([])

    def _buscar_real(self):
        try:
            clientes = cerebro.buscar(self._ultimo_texto)
            self.sugerencias_listas.emit(clientes)
        except Exception as e:
            self.logger.error(f"Error en MotorBusquedaClientes: {e}")
            self.error_busqueda.emit("Error al consultar la base de clientes")
            self.sugerencias_listas.emit([])

    def identificar_o_crear(self, texto):
        try:
            texto_limpio = texto.replace(".", "").replace("-", "").replace(" ", "")
            es_dni = texto_limpio.isdigit() and len(texto_limpio) >= 7
            
            if texto_limpio.isdigit() and not es_dni:
                self.error_busqueda.emit("DNI invalido. Minimo 7 digitos.")
                return
            
            if es_dni:
                cliente, estado, msg = cerebro.identificar_dni(texto)
            else:
                cliente, estado, msg = cerebro.identificar_nombre(texto)
                
            if estado == "error" or not cliente:
                self.error_busqueda.emit(msg or "No se pudo identificar al cliente.")
                return
                
            c = dict(cliente) if hasattr(cliente, "keys") else (cliente if isinstance(cliente, dict) else {})
            self.aprobar_credito(c)
        except Exception as e:
            self.logger.error(f"Error identificar_o_crear: {e}")
            self.error_busqueda.emit("Error de base de datos al crear cliente.")

    def aprobar_credito(self, cliente):
        try:
            cartel = cerebro.cartel(cliente)
            disp = cartel.get("disponible") or 0.0
            saludo = str(cartel.get("saludo") or "").replace("Hola, ", "")
            
            datos = {
                'id': cliente.get('id'),
                'nombre': saludo,
                'limite': disp,
                'compra': self._monto_venta
            }
            self.limite_aprobado.emit(datos)
        except Exception as e:
            self.logger.error(f"Error aprobando credito: {e}")
            self.error_busqueda.emit("No se pudo calcular el cr\u00e9dito del cliente")
