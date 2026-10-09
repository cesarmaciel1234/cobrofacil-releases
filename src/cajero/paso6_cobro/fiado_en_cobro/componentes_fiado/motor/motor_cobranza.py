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

class MotorCobranza:
    def __init__(self, panel):
        self.panel = panel

    def finalizar(self, monto, metodo, detalle):
        from src.clientes_fiado.interfaz.cobro.medios.resultado import ResultadoMedio
        from src.clientes_fiado.interfaz.cobro.medios.cerrar import asentar
        from src.cajero.cajero_activo import CajeroActivo
        from src.config import config
        from src.clientes_fiado.cerebro.cerebro import cerebro
        
        if metodo == "Efectivo":
            if not self.panel._pin():
                self.panel._volver_de_lienzo()
                return
        res = ResultadoMedio(True, metodo, (metodo == "Efectivo"), detalle)
        
        cliente = cerebro.obtener(self.panel._cliente_id)
        if not cliente: 
            self.panel._volver_de_lienzo()
            return
            
        try:
            cliente_dict = dict(cliente) if hasattr(cliente, 'keys') else cliente
            deuda_actual = float(cliente_dict.get('deuda_actual', 0) or 0)
        except:
            deuda_actual = 0.0
            
        hecho = asentar(
            self.panel._cliente_id,
            monto,
            deuda_actual,
            "Cajero",
            CajeroActivo.nombre,
            res,
            imprimir_saldo=False,
        )
        if not hecho.get('ok'):
            self.panel._volver_de_lienzo()
            return
            
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

        self.panel.abono_registrado.emit(ResultadoAbonoPrevio(
            ok=True,
            cliente_id=self.panel._cliente_id,
            monto=monto,
            nombre=str(hecho.get('nombre') or cliente.get('nombre') or 'Cliente'),
            saldo=float(hecho.get('saldo') or 0.0),
            deuda_anterior=deuda_actual
        ))
        
        self.panel._cerrar_lienzos()
        self.panel._modo = "listo"
        self.panel.pago_listo.emit(self.panel._cliente_id, 0.0)
