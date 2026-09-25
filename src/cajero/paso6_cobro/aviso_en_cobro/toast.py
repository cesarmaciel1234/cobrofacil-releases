import threading

from PyQt6.QtCore import Qt, QEventLoop, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


class AvisoCobro(QFrame):
    """Cartel grande sobre la hoja. No es una ventana y no hay que cerrarlo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AvisoCobro")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setStyleSheet(
            "QFrame#AvisoCobro {"
            " background: #FEF3C7; border: 3px solid #F59E0B; border-radius: 18px;"
            "}"
            "QLabel { background: transparent; border: none; color: #92400E;"
            " font-size: 28px; font-weight: 900; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        self.texto = QLabel("")
        self.texto.setWordWrap(True)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.texto)
        self.boton = QPushButton("Asociar")
        self.boton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.boton.setStyleSheet(
            "QPushButton { background: #D97706; color: white; font-size: 22px;"
            " font-weight: 900; border: none; border-radius: 12px; padding: 10px 18px; }"
            "QPushButton:hover { background: #B45309; }"
        )
        self.boton.clicked.connect(self._pulsar)
        self.boton.hide()
        lay.addWidget(self.boton)
        self._accion = None
        self._reloj = QTimer(self)
        self._reloj.setSingleShot(True)
        self._reloj.timeout.connect(self.hide)
        self._pintar_estilo(False)
        self.hide()

    def _pintar_estilo(self, alarma):
        if alarma:
            self.setStyleSheet(
                "QFrame#AvisoCobro {"
                " background: #FEF2F2; border: 3px solid #DC2626; border-radius: 18px;"
                "}"
                "QLabel { background: transparent; border: none; color: #991B1B;"
                " font-size: 28px; font-weight: 900; }"
            )
            return
        self.setStyleSheet(
            "QFrame#AvisoCobro {"
            " background: #FEF3C7; border: 3px solid #F59E0B; border-radius: 18px;"
            "}"
            "QLabel { background: transparent; border: none; color: #92400E;"
            " font-size: 28px; font-weight: 900; }"
        )

    def mostrar(self, mensaje, accion=None, rotulo=None):
        self._pintar_estilo(False)
        self.texto.setText(mensaje)
        self._accion = accion
        if accion:
            self.boton.setText(rotulo or "Asociar")
            self.boton.show()
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self._reloj.stop()
        else:
            self.boton.hide()
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self._reloj.start(4500)
        self.show()
        self.raise_()
        QTimer.singleShot(0, self.ubicar)

    def alarma(self, mensaje):
        self._accion = None
        self.boton.hide()
        self._pintar_estilo(True)
        self.texto.setText(f"⚠  {mensaje}")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._reloj.start(8000)
        self.show()
        self.raise_()
        QTimer.singleShot(0, self.ubicar)

    def tiene_accion(self):
        return self.isVisible() and self._accion is not None

    def aceptar(self):
        if self.tiene_accion():
            self._pulsar()

    def cerrar(self):
        self._accion = None
        self._reloj.stop()
        self.boton.hide()
        self.hide()

    def _pulsar(self):
        accion = self._accion
        self._accion = None
        self.boton.hide()
        self.hide()
        if accion:
            accion()

    def ubicar(self):
        hoja = self.parentWidget()
        if hoja is None:
            return
        cobro = hoja
        while cobro is not None and not hasattr(cobro, "txt_desc"):
            cobro = cobro.parentWidget()
        if cobro is None:
            return
        ancla = cobro.txt_desc
        rotulo = cobro.lbl_desc
        recargo = cobro.txt_rec
        x = rotulo.mapTo(hoja, rotulo.rect().topLeft()).x()
        borde = recargo.mapTo(hoja, recargo.rect().bottomRight())
        base = ancla.mapTo(hoja, ancla.rect().bottomLeft()).y()
        ancho = max(360, min(borde.x() - x, hoja.width() - x - 8))
        self.setFixedWidth(ancho)
        self.adjustSize()
        alto = max(88, self.sizeHint().height())
        y = max(8, base - alto)
        self.setGeometry(max(8, x), y, ancho, alto)
        self.raise_()


class EsperaPoint(QFrame):
    """Cartel del Point sobre la hoja. Cancelar suelta el cobro en la terminal."""

    _llegada = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EsperaPoint")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setStyleSheet(
            "QFrame#EsperaPoint {"
            " background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 22px;"
            "}"
            "QLabel { background: transparent; border: none; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 36, 40, 36)
        lay.setSpacing(22)
        self.texto = QLabel("Pida al cliente que pase la tarjeta.")
        self.texto.setWordWrap(True)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto.setStyleSheet(
            "color: #1E3A8A; font-size: 28px; font-weight: 800;"
        )
        lay.addWidget(self.texto)
        self.monto = QLabel("")
        self.monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.monto.setStyleSheet(
            "color: #0F172A; font-size: 56px; font-weight: 900;"
        )
        lay.addWidget(self.monto)
        self.boton = QPushButton("Cancelar")
        self.boton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.boton.setMinimumHeight(72)
        self.boton.setStyleSheet(
            "QPushButton { background: #EF4444; color: white; font-size: 24px;"
            " font-weight: 900; border: none; border-radius: 16px; padding: 16px 28px; }"
            "QPushButton:hover { background: #DC2626; }"
        )
        self.boton.clicked.connect(self.soltar)
        lay.addWidget(self.boton)
        self._reloj = QTimer(self)
        self._reloj.setInterval(2500)
        self._reloj.timeout.connect(self._consultar)
        self._llegada.connect(self._pintar)
        self._loop = None
        self._generacion = 0
        self._abortado = False
        self._aprobado = False
        self.motivo = ""
        self._token = ""
        self._device = ""
        self._intent = ""
        self._monto = 0.0
        self.hide()

    def esperar(self, token, device, monto):
        self._generacion += 1
        self._abortado = False
        self._aprobado = False
        self.motivo = ""
        self._token = token
        self._device = device
        self._intent = ""
        self._monto = float(monto or 0)
        self.monto.setText(f"${self._monto:,.2f}")
        self.texto.setText("Enviando el monto al TPV…")
        self.boton.setEnabled(True)
        self.show()
        self.raise_()
        QTimer.singleShot(0, self.ubicar)
        self._loop = QEventLoop(self)
        QTimer.singleShot(0, self._enviar)
        self._loop.exec()
        self._reloj.stop()
        self.hide()
        self._loop = None
        return self._aprobado

    def soltar(self):
        if self._abortado or self._aprobado:
            return
        loop = self._loop
        if loop is None or not loop.isRunning():
            return
        self._abortado = True
        if not self.motivo:
            self.motivo = "usuario"
        self._generacion += 1
        self._reloj.stop()
        token, device, intent = self._token, self._device, self._intent
        self._intent = ""
        if intent:
            def _trabajo():
                from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import cancelar_intent
                cancelar_intent(token, device, intent, en_terminal=True)
            threading.Thread(target=_trabajo, daemon=True).start()
        loop.quit()

    def ubicar(self):
        hoja = self.parentWidget()
        if hoja is None:
            return
        margen = 36
        ancho = max(480, hoja.width() - margen * 2)
        self.setFixedWidth(ancho)
        self.adjustSize()
        alto = max(240, self.sizeHint().height())
        y = max(margen, (hoja.height() - alto) // 2)
        self.setGeometry(margen, y, ancho, alto)
        self.raise_()

    def _enviar(self):
        if self._abortado:
            return
        try:
            from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import enviar_monto
            generacion = self._generacion
            pedido = enviar_monto(self._token, self._device, self._monto)
        except Exception:
            pedido = {"ok": False, "motivo": "red"}
            generacion = self._generacion
        if generacion != self._generacion or self._abortado:
            intent = (pedido or {}).get("intent") or ""
            if intent:
                from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import cancelar_intent
                cancelar_intent(self._token, self._device, intent, en_terminal=True)
            return
        if not pedido.get("ok") or not pedido.get("intent"):
            self.motivo = pedido.get("motivo") or "rechazo"
            loop = self._loop
            if loop is not None and loop.isRunning():
                loop.quit()
            return
        self._intent = pedido.get("intent") or ""
        self.texto.setText("Pida al cliente que pase la tarjeta.")
        self.ubicar()
        self._reloj.start()

    def _consultar(self):
        if self._abortado or not self._intent:
            return
        token, intent, generacion = self._token, self._intent, self._generacion

        def _trabajo():
            from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import estado_intent
            self._llegada.emit({
                "generacion": generacion,
                "estado": estado_intent(token, intent),
            })

        threading.Thread(target=_trabajo, daemon=True).start()

    def _pintar(self, dato):
        if not dato or dato.get("generacion") != self._generacion or self._abortado:
            return
        estado = dato.get("estado")
        if estado == "FINISHED":
            self._aprobado = True
            self._reloj.stop()
            self._intent = ""
            loop = self._loop
            if loop is not None and loop.isRunning():
                loop.quit()
        elif estado in ("CANCELED", "ERROR", "ABANDONED"):
            self.motivo = "cancelo"
            self._generacion += 1
            self._reloj.stop()
            self._intent = ""
            loop = self._loop
            if loop is not None and loop.isRunning():
                loop.quit()
