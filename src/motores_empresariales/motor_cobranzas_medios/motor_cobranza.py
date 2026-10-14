from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass

@dataclass
class ResultadoAbonoPrevio:
    ok: bool
    cliente_id: int
    monto: float
    nombre: str
    saldo: float
    deuda_anterior: float
    aviso: str = ''

class MotorCobranzaMedios(QObject):
    abono_registrado = pyqtSignal(ResultadoAbonoPrevio)
    pago_listo = pyqtSignal(int, float)
    error_cobranza = pyqtSignal(str)
    requiere_autorizacion = pyqtSignal()
    
    def __init__(self, parent=None, perfil="Cajero"):
        super().__init__(parent)
        self._pedir_pin_callback = None
        self._perfil = (perfil or "Cajero").strip() or "Cajero"

    def set_pedir_pin_callback(self, callback):
        self._pedir_pin_callback = callback

    def finalizar(self, cliente_id, monto, metodo, detalle):
        from src.clientes_fiado.interfaz.cobro.medios.resultado import ResultadoMedio
        from src.clientes_fiado.interfaz.cobro.medios.cerrar import asentar
        from src.cajero.cajero_activo import CajeroActivo
        from src.config import config
        from src.clientes_fiado.cerebro.cerebro import cerebro
        
        if metodo == "Mixto":
            from src.clientes_fiado.interfaz.cobro.medios.mixto import cobrar
            res = cobrar(monto, detalle if isinstance(detalle, dict) else {})
            if not res.ok:
                self.error_cobranza.emit(res.detalle or "Error en distribución mixta")
                return
        else:
            res = ResultadoMedio(True, metodo, (metodo == "Efectivo"), detalle)
        
        cliente = cerebro.obtener(cliente_id)
        if not cliente: 
            self.error_cobranza.emit("Cliente no encontrado")
            return
            
        try:
            cliente_dict = dict(cliente) if hasattr(cliente, 'keys') else cliente
            deuda_actual = float(cliente_dict.get('deuda_actual', 0) or 0)
        except:
            deuda_actual = 0.0
            
        quien = CajeroActivo.nombre
        if self._perfil == "Admin":
            quien = (config.current_user or {}).get("username") or quien or "Admin"
        hecho = asentar(
            cliente_id,
            monto,
            deuda_actual,
            self._perfil,
            quien,
            res,
            imprimir_saldo=False,
        )
        if not hecho.get('ok'):
            self.error_cobranza.emit(hecho.get('aviso') or "No se pudo asentar el pago")
            return
            
        res.monto = monto
        res.cliente_id = cliente_id
        res.nombre = hecho.get('nombre', 'Cliente')
            
        if hecho.get('entra_caja'):
            from src.cajero.paso5_terminal.logica.movimientos_caja_service import MovimientosCajaService
            MovimientosCajaService().registrar_ingreso_efectivo(
                hecho['monto_caja'],
                CajeroActivo.nombre,
                hecho['motivo'],
                config.get('caja_id', 1),
                abrir_cajon=True,
                imprimir=False,
            )

        try:
            from src.motor_cobros_digitales.veredicto.medios import clase
            from src.motor_auditoria_digital.libro_cobranzas.libro import fusionar
            from src.motor_auditoria_digital.consultas.ids import ticket_cobro
            from src.base_de_datos.database import db_manager
            from datetime import datetime as _dt

            if clase(metodo) == "digital":
                nota = ""
                if detalle is not None and not isinstance(detalle, dict):
                    nota = str(detalle)
                elif isinstance(detalle, dict):
                    nota = str(detalle.get("id") or detalle.get("payment_id") or "")
                cobro_id = ""
                try:
                    ultima = db_manager.execute_query(
                        "SELECT id FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'ABONO' "
                        "ORDER BY id DESC LIMIT 1",
                        (cliente_id,),
                    ) or []
                    if ultima:
                        fila = ultima[0]
                        cobro_id = str(fila["id"] if hasattr(fila, "keys") else fila[0])
                except Exception:
                    cobro_id = ""
                if cobro_id:
                    fusionar([{
                        "id": cobro_id,
                        "ticket_cobro": ticket_cobro(cobro_id),
                        "fecha": _dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "monto": float(monto or 0),
                        "nombre": str(hecho.get("nombre") or "Cliente"),
                        "metodo": metodo,
                        "pago_id": nota,
                    }], avisar=True)
        except Exception:
            pass

        self.abono_registrado.emit(ResultadoAbonoPrevio(
            ok=True,
            cliente_id=cliente_id,
            monto=monto,
            nombre=str(hecho.get('nombre') or cliente.get('nombre') or 'Cliente'),
            saldo=float(hecho.get('saldo') or 0.0),
            deuda_anterior=deuda_actual
        ))
        
        self.pago_listo.emit(cliente_id, 0.0)
