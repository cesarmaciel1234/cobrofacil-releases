# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent


def _fila_a_dict(fila):
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return fila
    if hasattr(fila, "keys"):
        try:
            return dict(fila)
        except Exception:
            pass
    return {}


class HojaVirtual:
    """Adaptador que Paso6Cobro sigue llamando hoja_cuenta."""

    def __init__(self, parent):
        self.parent = parent

    def _paso(self, *a, **k):
        pass

    def _cliente(self, *a, **k):
        pass

    def isVisible(self):
        return self.parent.isVisible()

    def isActiveWindow(self):
        return self.parent.isActiveWindow()

    def ubicar(self):
        pass

    def _cancelar(self):
        self.parent._esc()

    def confirmar(self):
        self.parent.procesar_enter()

    def borrar(self):
        caja = getattr(self.parent.via_buscador, "caja_busqueda", None)
        if caja is not None and self.parent.stack.currentWidget() == self.parent.via_buscador:
            caja.setText(caja.text()[:-1])
            return
        evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
        self.parent.keyPressEvent(evt)

    def escribir(self, key):
        caja = getattr(self.parent.via_buscador, "caja_busqueda", None)
        if caja is not None and self.parent.stack.currentWidget() == self.parent.via_buscador:
            caja.setText(caja.text() + str(key))
            return
        evt = QKeyEvent(QKeyEvent.Type.KeyPress, 0, Qt.KeyboardModifier.NoModifier, str(key))
        self.parent.keyPressEvent(evt)

    def fijar_monto(self, m):
        pass


class OrquestadorFiadoPiramidal(QFrame):
    pago_completado = pyqtSignal(dict)
    cancelado = pyqtSignal()
    abono_registrado = pyqtSignal(object)
    submetodo_cambiado = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hoja_cuenta = HojaVirtual(self)
        self._modo = "Fiado"
        self._monto_carrito = 0.0
        self._datos_cliente = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)

        from .ruta1_margen_aprobado.panel_aprobado import PanelMargenAprobado
        self.via_aprobado = PanelMargenAprobado(self)
        self.via_aprobado.confirmado.connect(self._emitir_aprobado_normal)

        from .ruta2_limite_superado.panel_bloqueo import PanelLimiteSuperado
        self.via_bloqueo = PanelLimiteSuperado(self)
        self.via_bloqueo.pin_validado.connect(self._emitir_aprobado_normal)

        from .modulo_cobranza.panel_cobranza import PanelCobranza
        self.via_cobranza = PanelCobranza(self)
        self.via_cobranza.abono_exitoso.connect(self._finalizar_desde_cobranza)
        self.via_cobranza.cancelado.connect(self._volver_de_cobranza)
        self.via_cobranza.submetodo_cambiado.connect(self.submetodo_cambiado.emit)

        from .ruta3_cliente_nuevo.panel_nuevo import PanelClienteNuevo
        self.via_nuevo = PanelClienteNuevo(self)
        self.via_nuevo.cliente_creado.connect(self._cliente_recien_creado)

        from src.cajero.paso6_cobro.fiado_en_cobro.ui.buscador_clientes.panel_buscador import PanelBuscadorClientes
        from src.motores_empresariales.motor_busqueda_clientes.motor_busqueda import MotorBusquedaClientes

        self.motor_busqueda = MotorBusquedaClientes(self)
        self.motor_busqueda.precargar()
        self.via_buscador = PanelBuscadorClientes(self)
        self.via_buscador.texto_cambiado.connect(self.motor_busqueda.buscar_texto)
        self.motor_busqueda.sugerencias_listas.connect(self.via_buscador.mostrar_sugerencias)
        self.via_buscador.cliente_elegido.connect(self._cliente_elegido)
        self.via_buscador.creacion_solicitada.connect(self._abrir_creacion)

        self.stack.addWidget(self.via_buscador)
        self.stack.addWidget(self.via_aprobado)
        self.stack.addWidget(self.via_bloqueo)
        self.stack.addWidget(self.via_nuevo)
        self.stack.addWidget(self.via_cobranza)
        self.hide()

    def mostrar(self, monto, modo="Fiado"):
        self.show()
        self._modo = modo or "Fiado"
        self._monto_carrito = float(monto or 0)
        self._datos_cliente = {}
        self.submetodo_cambiado.emit("")
        if hasattr(self.motor_busqueda, "set_monto_venta"):
            self.motor_busqueda.set_monto_venta(self._monto_carrito)
        if hasattr(self.motor_busqueda, "precargar"):
            self.motor_busqueda.precargar()
        self.via_buscador.aplicar_modo(self._modo)
        self.via_buscador.limpiar()
        self.stack.setCurrentWidget(self.via_buscador)
        self.via_buscador.focus_caja()

    def ocultar(self):
        self.hide()

    def reiniciar(self):
        """Cierra crédito/cobranza sin tocar la base. ESC usa esto."""
        self.submetodo_cambiado.emit("")
        self._datos_cliente = {}
        self._modo = "Fiado"
        self._monto_carrito = 0.0
        try:
            self.via_cobranza.soltar()
        except Exception:
            pass
        try:
            self.via_buscador.limpiar()
        except Exception:
            pass
        self.stack.setCurrentWidget(self.via_buscador)
        self.hide()

    def _cliente_elegido(self, dict_datos):
        self._evaluar_cliente(int(_fila_a_dict(dict_datos).get("id") or 0))

    def _abrir_creacion(self, nombre):
        self.stack.setCurrentWidget(self.via_nuevo)
        self.via_nuevo.poblar_inicial(nombre)

    def _evaluar_cliente(self, cliente_id):
        if not cliente_id:
            self.stack.setCurrentWidget(self.via_nuevo)
            self.via_nuevo.txt_input.setFocus()
            return

        c_dict = {}
        if hasattr(self.motor_busqueda, "ficha"):
            c_dict = _fila_a_dict(self.motor_busqueda.ficha(cliente_id) or {})
        if not c_dict.get("id"):
            from src.clientes_fiado.cerebro.cerebro import cerebro
            cli = cerebro.obtener(cliente_id)
            if not cli:
                return
            c_dict = _fila_a_dict(cli)
        datos = {
            "id": c_dict.get("id"),
            "nombre": c_dict.get("nombre"),
            "deuda": float(c_dict.get("deuda_actual", 0.0) or 0.0),
            "limite": float(c_dict.get("limite_credito", 0.0) or 0.0),
            "compra": self._monto_carrito,
        }
        self._datos_cliente = datos
        if getattr(self, "_modo", "") == "MasCredito":
            self._abrir_cobranza(datos)
        else:
            self._decidir_via_credito(datos)

    def _decidir_via_credito(self, datos):
        limite = float(datos.get("limite", 0) or 0)
        deuda = float(datos.get("deuda", 0) or 0)
        compra = float(datos.get("compra", 0) or 0)
        disponible = limite - deuda
        if compra <= disponible:
            self.via_aprobado.poblar(datos)
            self.stack.setCurrentWidget(self.via_aprobado)
        else:
            self.via_bloqueo.poblar(datos)
            self.stack.setCurrentWidget(self.via_bloqueo)

    def _emitir_aprobado_normal(self, cliente_id, _abono=0.0):
        monto_abono = float(_abono or 0.0)
        saldo_previo = float(self._datos_cliente.get("deuda", 0.0) or 0.0)
        saldo_final = saldo_previo + self._monto_carrito
        lineas = [
            "--------------------------------",
            ">>> CUENTA CORRIENTE <<<",
            f"CLIENTE: {self._datos_cliente.get('nombre') or ''}",
            f"SALDO PREVIO:   ${saldo_previo:,.2f}",
            f"ESTA COMPRA:    ${self._monto_carrito:,.2f}",
        ]
        if monto_abono > 0.009:
            lineas.append(f"ABONO COBRANZA: ${monto_abono:,.2f}")
        lineas.extend(
            [
                f"SALDO RESTANTE: ${saldo_final:,.2f}",
                "--------------------------------",
                "FIRMA: _________________________",
            ]
        )
        self.pago_completado.emit(
            {
                "estado": "APROBADO",
                "cliente_id": cliente_id,
                "monto_carrito": self._monto_carrito,
                "medio_pago": "CRÉDITO",
                "condiciones_ticket": {
                    "es_cuenta_corriente": True,
                    "cliente_nombre": self._datos_cliente.get("nombre") or "",
                    "lineas_extra": lineas,
                },
            }
        )

    def _finalizar_desde_cobranza(self):
        cliente_id = int(self._datos_cliente.get("id", 0) or 0)
        monto_abono = float(getattr(self.via_cobranza, "_monto_a_cobrar", 0.0) or 0.0)
        try:
            from src.clientes_fiado.cerebro.cerebro import cerebro
            from src.cajero.cajero_activo import CajeroActivo
            cerebro.conceder_excepcion(cliente_id, self._monto_carrito, CajeroActivo.nombre)
            cli = cerebro.obtener(cliente_id)
            if cli:
                c_dict = _fila_a_dict(cli)
                self._datos_cliente["deuda"] = float(c_dict.get("deuda_actual", 0.0) or 0.0)
        except Exception:
            pass
        self._emitir_aprobado_normal(cliente_id, monto_abono)

    def _refrescar_cliente(self):
        cid = self._datos_cliente.get("id")
        if not cid:
            return
        from src.clientes_fiado.cerebro.cerebro import cerebro

        cli = cerebro.obtener(cid)
        if not cli:
            return
        c_dict = _fila_a_dict(cli)
        self._datos_cliente["deuda"] = float(c_dict.get("deuda_actual", 0.0) or 0.0)
        self._datos_cliente["limite"] = float(c_dict.get("limite_credito", self._datos_cliente.get("limite", 0)) or 0.0)
        self._datos_cliente["nombre"] = c_dict.get("nombre") or self._datos_cliente.get("nombre")
        self._datos_cliente["compra"] = self._monto_carrito

    def _volver_de_cobranza(self):
        self.stack.setCurrentWidget(self.via_buscador)
        self.via_buscador.focus_caja()

    def _abrir_cobranza(self, datos):
        self._datos_cliente = datos or self._datos_cliente
        self.via_cobranza.poblar(self._datos_cliente)
        self.stack.setCurrentWidget(self.via_cobranza)

    def _cliente_recien_creado(self, dict_datos):
        self._datos_cliente = _fila_a_dict(dict_datos)
        self._datos_cliente["compra"] = self._monto_carrito
        if getattr(self, "_modo", "") == "MasCredito":
            self._abrir_cobranza(self._datos_cliente)
        else:
            self._decidir_via_credito(self._datos_cliente)

    def procesar_cobranza(self):
        return False

    def procesar_f9(self):
        if self.stack.currentWidget() == self.via_cobranza and hasattr(self.via_cobranza, "procesar_f9"):
            return self.via_cobranza.procesar_f9()
        return False

    def verificar_qr(self):
        if self.stack.currentWidget() == self.via_cobranza and hasattr(self.via_cobranza, "verificar_qr"):
            return self.via_cobranza.verificar_qr()
        return False

    def bloquea_enter(self):
        return self.isVisible()

    def procesar_enter(self):
        actual = self.stack.currentWidget()
        if actual == self.via_buscador:
            self.via_buscador.aceptar_actual()
            return
        if actual == self.via_nuevo:
            self.via_nuevo._procesar()
            return
        evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        self.keyPressEvent(evt)

    def navegar_buscador(self, direccion):
        if self.stack.currentWidget() == self.via_buscador:
            self.via_buscador.navegar(direccion)
            return True
        return False

    def _esc(self):
        self.cancelado.emit()

    def keyPressEvent(self, event):
        k = event.key()
        if k in (Qt.Key.Key_Down, Qt.Key.Key_Up) and self.stack.currentWidget() == self.via_buscador:
            if event.isAutoRepeat():
                return
            self.via_buscador.navegar("abajo" if k == Qt.Key.Key_Down else "arriba")
            return
        if k == Qt.Key.Key_Escape:
            self._esc()
            return
        actual = self.stack.currentWidget()
        if actual is not None:
            actual.keyPressEvent(event)
