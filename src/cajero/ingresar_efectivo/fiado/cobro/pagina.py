"""Elige el medio del abono, pide el PIN y corre el motor en esta hoja."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout

from src.cajero.ingresar_efectivo.fiado.cobro.lienzo_efectivo import LienzoEfectivo
from src.cajero.ingresar_efectivo.fiado.cobro.lienzo_qr import LienzoQr
from src.cajero.ingresar_efectivo.fiado.cobro.lienzo_tarjeta import LienzoTarjeta
from src.cajero.ingresar_efectivo.fiado.cobro.lienzo_transferencia import LienzoTransferencia
from src.clientes_fiado.interfaz.cobro.medios.efectivo import cobrar as cobrar_efectivo
from src.clientes_fiado.interfaz.cobro.medios.resultado import ResultadoMedio


_ESTILO_BOTON = (
    "QPushButton { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;"
    " border-radius: 12px; font-size: 14px; font-weight: 800; padding: 8px 14px; }"
    "QPushButton:hover { background: #EFF6FF; border-color: #1D4ED8; }"
)


class PaginaCobroAbono(QFrame):
    def __init__(self, dialogo):
        super().__init__()
        self.dialogo = dialogo
        self.monto = 0.0
        self._quien = ""
        self._nombre = ""
        self._en_motor = False
        self._pendiente = None
        self._cola = []
        self._cerrando = False
        self.setObjectName("IngresoCobro")
        self.setStyleSheet(
            "QFrame#IngresoCobro { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 24px; }"
            "QLabel { background: transparent; border: none; color: #0F172A; }"
        )
        self._armar()

    def _armar(self):
        caja = QVBoxLayout(self)
        caja.setContentsMargins(28, 28, 28, 24)
        caja.setSpacing(14)
        self.zona = QVBoxLayout()
        self.titulo = QLabel("Hola")
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo.setStyleSheet(
            "color: #0F172A; font-size: 24px; font-weight: 800; background: transparent; border: none;"
        )
        self.zona.addWidget(self.titulo)
        self.pregunta = QLabel("¿Con qué paga?")
        self.pregunta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pregunta.setStyleSheet(
            "color: #0F172A; font-size: 18px; font-weight: 800; background: #FFFFFF;"
            " border: 2px solid #2563EB; border-radius: 16px; padding: 10px;"
        )
        self.zona.addWidget(self.pregunta)
        self.fila_medios = QHBoxLayout()
        self.fila_medios.setSpacing(8)
        self.botones_medio = []
        for nombre in ("Efectivo", "Transferencia", "Tarjeta", "QR"):
            boton = QPushButton(nombre)
            boton.setMinimumHeight(52)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setStyleSheet(_ESTILO_BOTON)
            boton.clicked.connect(lambda _=False, n=nombre: self._elegir(n))
            self.fila_medios.addWidget(boton)
            self.botones_medio.append(boton)
        self.zona.addLayout(self.fila_medios)
        self.btn_mixto = QPushButton("Mixto")
        self.btn_mixto.setMinimumHeight(52)
        self.btn_mixto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mixto.setStyleSheet(_ESTILO_BOTON)
        self.btn_mixto.clicked.connect(lambda: self._elegir("Mixto"))
        self.zona.addWidget(self.btn_mixto)
        self.botones_medio.append(self.btn_mixto)
        self.aviso = QLabel("")
        self.aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aviso.setWordWrap(True)
        self.aviso.setStyleSheet("color: #B91C1C; font-weight: 800; background: transparent; border: none;")
        self.zona.addWidget(self.aviso)
        caja.addLayout(self.zona)

        self.contenedor = QStackedWidget()
        self.efectivo = LienzoEfectivo()
        self.qr = LienzoQr()
        self.tarjeta = LienzoTarjeta()
        self.transferencia = LienzoTransferencia()
        self.contenedor.addWidget(self.efectivo)
        self.contenedor.addWidget(self.qr)
        self.contenedor.addWidget(self.tarjeta)
        self.contenedor.addWidget(self.transferencia)
        self.contenedor.hide()
        caja.addWidget(self.contenedor, 1)
        self.efectivo.listo.connect(self._efectivo_listo)
        self.efectivo.volver.connect(self._cancelar_motor)
        self.qr.listo.connect(lambda detalle: self._motor_listo("QR", detalle))
        self.qr.volver.connect(self._cancelar_motor)
        self.tarjeta.listo.connect(lambda detalle: self._motor_listo("Tarjeta", detalle))
        self.tarjeta.fallo.connect(self._motor_fallo)
        self.tarjeta.volver.connect(self._cancelar_motor)
        self.transferencia.listo.connect(lambda detalle: self._motor_listo("Transferencia", detalle))
        self.transferencia.volver.connect(self._cancelar_motor)

    def abrir(self, monto, quien, nombre=""):
        self.monto = float(monto or 0)
        self._quien = quien or ""
        self._nombre = (nombre or "").strip() or "cliente"
        self._pendiente = None
        self._cola = []
        self._cerrando = False
        self.aviso.setText("")
        self.titulo.setText(f"Hola {self._nombre}")
        self._mostrar_botones()

    def escape(self):
        if self._en_motor:
            self._cancelar_motor()
            return
        self.dialogo.volver_al_importe()

    def tecla(self, k):
        if not self._en_motor:
            return False
        actual = self.contenedor.currentWidget()
        for lienzo in (self.transferencia, self.tarjeta, self.qr, self.efectivo):
            if actual is lienzo and hasattr(lienzo, "tecla"):
                return bool(lienzo.tecla(k))
        return False

    def _elegir(self, nombre):
        try:
            if not self._pin():
                return
            if nombre == "Efectivo":
                self._pendiente = ResultadoMedio(True, "Efectivo", True, monto_caja=self.monto)
                self._cola = []
                self._abrir_motor("Efectivo", self.monto)
                return
            if nombre == "Mixto":
                self._mixto()
                return
            self._pendiente = ResultadoMedio(True, nombre, False)
            self._cola = []
            self._abrir_motor(nombre, self.monto)
        except Exception:
            self.aviso.setText("No se pudo cobrar. La venta sigue.")
            self._mostrar_botones()

    def _mixto(self):
        from src.clientes_fiado.interfaz.cobro.medios.hoja import HojaMixtoAbono
        from src.utils.qt_compat import qt_exec

        hoja = HojaMixtoAbono(self.monto, self)
        if not (qt_exec(hoja) and hoja.resultado and hoja.resultado.ok):
            return
        self._pendiente = hoja.resultado
        partes = hoja.partes or {}
        self._cola = [
            (clave, float(partes.get(clave) or 0))
            for clave in ("Transferencia", "Tarjeta", "QR")
            if float(partes.get(clave) or 0) > 0.009
        ]
        if float(partes.get("Efectivo") or 0) > 0.009:
            try:
                from src.hardware.cash_drawer import drawer_manager
                drawer_manager.set_authorized(True)
                drawer_manager.abrir(autorizada=True)
            except Exception:
                pass
        self._siguiente()

    def _siguiente(self):
        if not self._cola:
            self._terminar(self._pendiente)
            return
        clave, valor = self._cola.pop(0)
        self._abrir_motor(clave, valor)

    def _abrir_motor(self, nombre, monto):
        self._en_motor = True
        self._ocultar_botones()
        self.contenedor.show()
        if nombre == "Efectivo":
            self.contenedor.setCurrentWidget(self.efectivo)
            self.efectivo.arrancar(monto)
        elif nombre == "QR":
            self.contenedor.setCurrentWidget(self.qr)
            self.qr.arrancar(monto)
        elif nombre == "Tarjeta":
            self.contenedor.setCurrentWidget(self.tarjeta)
            self.tarjeta.arrancar(monto)
        else:
            self.contenedor.setCurrentWidget(self.transferencia)
            self.transferencia.arrancar(monto)

    def _efectivo_listo(self, monto):
        try:
            self._terminar(cobrar_efectivo(monto))
        except Exception:
            self._motor_fallo("No se pudo cobrar. La venta sigue.")

    def _motor_listo(self, nombre, detalle):
        try:
            if self._pendiente is not None and self._pendiente.medio == nombre and detalle:
                self._pendiente.detalle = str(detalle)
            elif self._pendiente is not None and self._pendiente.medio == "Mixto" and detalle:
                extra = f"{nombre} {detalle}"
                self._pendiente.detalle = (
                    f"{self._pendiente.detalle} ({extra})" if self._pendiente.detalle else extra
                )
            self._cerrar_lienzos()
            self._siguiente()
        except Exception:
            self._motor_fallo("No se pudo cobrar. La venta sigue.")

    def _motor_fallo(self, texto):
        self._cola = []
        self._pendiente = None
        self._cerrar_lienzos()
        self._mostrar_botones()
        self.aviso.setText(str(texto or "No se pudo cobrar. La venta sigue."))

    def _cancelar_motor(self):
        self._cola = []
        self._pendiente = None
        self._cerrar_lienzos()
        self._mostrar_botones()

    def _terminar(self, resultado):
        if self._cerrando:
            return
        self._cerrando = True
        self._cerrar_lienzos()
        if resultado is None or not getattr(resultado, "ok", False):
            self._cerrando = False
            self.aviso.setText("No se pudo cobrar. La venta sigue.")
            self._mostrar_botones()
            return
        self.dialogo.cerrar_con_medio(resultado)

    def _pin(self):
        try:
            from src.cajero.paso5_terminal.dialogos.pin.dialogo_pin import DialogoPIN
            from src.utils.qt_compat import qt_exec
            dlg = DialogoPIN(self._quien, self.dialogo)
            return bool(qt_exec(dlg) and dlg.ok)
        except Exception:
            self.aviso.setText("No se pudo pedir el PIN. La venta sigue.")
            return False

    def _mostrar_botones(self):
        self._en_motor = False
        self.contenedor.hide()
        for boton in self.botones_medio:
            boton.show()
        self.aviso.show()

    def _ocultar_botones(self):
        for boton in self.botones_medio:
            boton.hide()
        self.aviso.hide()
        self.titulo.show()
        self.pregunta.show()

    def _cerrar_lienzos(self):
        self._en_motor = False
        for lienzo in (self.efectivo, self.qr, self.tarjeta, self.transferencia):
            try:
                lienzo.cerrar()
            except Exception:
                pass
        self.contenedor.hide()
