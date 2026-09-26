"""La cuenta se pide en la misma hoja del cobro que la tarjeta."""
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRegularExpression, QEvent
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QFrame, QLabel, QLineEdit, QVBoxLayout

from src.clientes_fiado.cerebro.cerebro import cerebro
from src.clientes_fiado.interfaz.cobro.fiado_express import (
    sonar_alarma_limite_fiado,
    sonar_dni_no_coincide,
)
from src.clientes_fiado.interfaz.cobro.pin_admin import quien_autoriza


class _FilaNombre(QFrame):
    """Una fila del listado: el nombre arriba y el DNI abajo."""

    def __init__(self, hoja, indice, ficha):
        super().__init__()
        self._hoja = hoja
        self._indice = indice
        self.setMinimumHeight(62)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(14, 8, 14, 8)
        caja.setSpacing(0)
        nombre = QLabel(str(ficha.get("nombre") or ""))
        nombre.setStyleSheet(
            "color: #0F172A; font-size: 18px; font-weight: 800; background: transparent; border: none;"
        )
        caja.addWidget(nombre)
        dni = str(ficha.get("dni") or "").strip()
        linea = QLabel(f"DNI {dni}" if dni else "Sin DNI")
        linea.setStyleSheet(
            "color: #1E293B; font-size: 14px; font-weight: 700; background: transparent; border: none;"
        )
        caja.addWidget(linea)
        for etiqueta in (nombre, linea):
            etiqueta.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def mousePressEvent(self, evento):
        self._hoja._tocar(self._indice)


class HojaCuentaCobro(QFrame):
    """Cartel de fiado o cuenta corriente. Misma hoja que la espera de la tarjeta."""

    listo = pyqtSignal(int)
    cancelado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HojaCuenta")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(
            "QFrame#HojaCuenta {"
            " background: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 22px;"
            "}"
            "QLabel { background: transparent; border: none; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 36, 40, 36)
        lay.setSpacing(16)
        self.texto = QLabel("Pida el nombre del cliente.")
        self.texto.setWordWrap(True)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto.setMinimumHeight(44)
        self.texto.setStyleSheet("color: #1E3A8A; font-size: 28px; font-weight: 800;")
        lay.addWidget(self.texto)
        self.subtitulo = QLabel("")
        self.subtitulo.setWordWrap(True)
        self.subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitulo.setStyleSheet("color: #1E3A8A; font-size: 22px; font-weight: 700;")
        self.subtitulo.hide()
        lay.addWidget(self.subtitulo)
        self.caja = QLineEdit()
        self.caja.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caja.setMinimumHeight(64)
        self.caja.setStyleSheet(
            "QLineEdit { background: #FFFFFF; color: #0F172A; border: 2px solid #CBD5E1;"
            " border-radius: 16px; padding: 8px 16px; font-size: 28px; font-weight: 800; }"
            "QLineEdit:focus { border: 2px solid #1D4ED8; }"
        )
        self.caja.returnPressed.connect(self.confirmar)
        self.caja.textChanged.connect(self._al_escribir)
        self.caja.installEventFilter(self)
        lay.addWidget(self.caja)
        self.lista = QFrame()
        self.lista.setObjectName("ListaNombres")
        self.lista.setStyleSheet(
            "QFrame#ListaNombres { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 12px; }"
        )
        self._caja_lista = QVBoxLayout(self.lista)
        self._caja_lista.setContentsMargins(0, 0, 0, 0)
        self._caja_lista.setSpacing(0)
        self.lista.hide()
        lay.addWidget(self.lista)
        self.aviso = QLabel("")
        self.aviso.setWordWrap(True)
        self.aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aviso.setStyleSheet("color: #EF4444; font-size: 18px; font-weight: 800;")
        lay.addWidget(self.aviso)
        self.saldo = QLabel("")
        self.saldo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.saldo.setStyleSheet("color: #0F172A; font-size: 28px; font-weight: 900;")
        lay.addWidget(self.saldo)
        self.disponible = QLabel("")
        self.disponible.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.disponible.setStyleSheet("color: #047857; font-size: 28px; font-weight: 900;")
        lay.addWidget(self.disponible)
        self._val_dni = QRegularExpressionValidator(QRegularExpression(r"\d{0,11}"))
        self._val_nombre = QRegularExpressionValidator(QRegularExpression(r"[^\d]{0,80}"))
        self._modo = "Clientes"
        self._paso = 1
        self._monto = 0.0
        self._ref = ""
        self._cliente = None
        self._filas = []
        self._marca = -1
        self._ignorar = False
        self._silencio = False
        self._pidiendo_pin = False
        self._pin = ""
        self.hide()

    def abrir(self, modo, monto):
        self._modo = "Fiado" if modo == "Fiado" else "Clientes"
        self._paso = 1
        self._monto = float(monto or 0)
        self._ref = ""
        self._cliente = None
        self._filas = []
        self._soltar_pin()
        cerebro.soltar_excepcion()
        self._pintar_paso()
        self.show()
        self.raise_()
        self.ubicar()
        self.caja.setFocus()

    def fijar_monto(self, monto):
        self._monto = float(monto or 0)

    def ocultar(self):
        self._cerrar_lista()
        self.hide()

    def escribir(self, texto):
        if self._pidiendo_pin:
            for cifra in str(texto or ""):
                if cifra.isdigit() and len(self._pin) < 4:
                    self._pin += cifra
            self._pintar_pin()
            if len(self._pin) == 4:
                self._cerrar_pin()
            return
        pieza = str(texto or "")
        if self._modo == "Fiado":
            pieza = "".join(c for c in pieza if c.isdigit())
        else:
            pieza = "".join(c for c in pieza if not c.isdigit())
        if not pieza:
            return
        self.caja.setFocus()
        self.caja.insert(pieza)

    def borrar(self):
        if self._pidiendo_pin:
            self._pin = self._pin[:-1]
            self._pintar_pin()
            return
        self.caja.setFocus()
        self.caja.backspace()

    def confirmar(self):
        if self._pidiendo_pin:
            if len(self._pin) == 4:
                self._cerrar_pin()
            return
        if self._ignorar:
            return
        self._ignorar = True
        QTimer.singleShot(0, self._soltar)
        if self._paso == 1:
            self._cargar()
        else:
            self._repetir()

    def _soltar(self):
        self._ignorar = False

    def eventFilter(self, obj, event):
        if obj is self.caja and event.type() == QEvent.Type.KeyPress and self._pidiendo_pin:
            tecla = event.key()
            if tecla == Qt.Key.Key_Backspace:
                self.borrar()
            elif tecla in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.confirmar()
            elif event.text() and event.text().isdigit():
                self.escribir(event.text())
            return True
        if obj is self.caja and event.type() == QEvent.Type.KeyPress and self.lista.isVisible():
            tecla = event.key()
            if tecla == Qt.Key.Key_Down and self._filas:
                self._marca = 0 if self._marca < 0 else min(len(self._filas) - 1, self._marca + 1)
                self._pintar_marca()
                return True
            if tecla == Qt.Key.Key_Up and self._marca > 0:
                self._marca -= 1
                self._pintar_marca()
                return True
        return super().eventFilter(obj, event)

    def ubicar(self):
        hoja = self.parentWidget()
        if hoja is None:
            return
        margen = 36
        ancho = max(480, hoja.width() - margen * 2)
        self.setFixedWidth(ancho)
        self.adjustSize()
        alto = max(280, self.sizeHint().height())
        y = margen
        total = hoja.findChild(QLabel, "CobroTotal")
        if total is not None:
            bajo = total.mapTo(hoja, total.rect().bottomLeft())
            y = max(margen, bajo.y() + 16)
        if y + alto > hoja.height() - margen:
            y = max(margen, hoja.height() - alto - margen)
        self.setGeometry(margen, y, ancho, alto)
        self.raise_()
        if self._pidiendo_pin:
            aviso = self._aviso()
            if aviso is not None:
                aviso.raise_()

    def _frase(self):
        if self._modo == "Fiado":
            return "Pida el DNI del cliente." if self._paso == 1 else "Confirme el DNI."
        return "Pida el nombre del cliente." if self._paso == 1 else "Confirme el nombre."

    def _pintar_paso(self):
        self._silencio = True
        self.aviso.setTextFormat(Qt.TextFormat.PlainText)
        self.aviso.setStyleSheet("color: #EF4444; font-size: 18px; font-weight: 800;")
        self.aviso.clear()
        self.caja.clear()
        self._silencio = False
        self._cerrar_lista()
        self.subtitulo.hide()
        if self._modo == "Fiado":
            self.caja.setValidator(self._val_dni)
            self.caja.setPlaceholderText("DNI")
        else:
            self.caja.setValidator(self._val_nombre)
            self.caja.setPlaceholderText("Nombre")
        if self._paso == 2 and self._cliente:
            cartel = cerebro.cartel(self._cliente)
            self.texto.setText(str(cartel.get("saludo") or "Sin datos"))
            self.texto.setStyleSheet("color: #0F172A; font-size: 32px; font-weight: 900;")
            self.subtitulo.setText(self._frase())
            self.subtitulo.show()
            self._pintar_numeros(cartel.get("saldo"), cartel.get("disponible"))
        else:
            self.texto.setText(self._frase())
            self.texto.setStyleSheet("color: #1E3A8A; font-size: 28px; font-weight: 800;")
            self.saldo.clear()
            self.disponible.clear()
        self.caja.setFocus()

    def _pintar_numeros(self, saldo, disponible):
        if saldo is None:
            self.saldo.clear()
        else:
            self.saldo.setText(f"Saldo  ${float(saldo):,.2f}")
        if disponible is None:
            self.disponible.clear()
        else:
            self.disponible.setText(f"Disponible  ${float(disponible):,.2f}")

    def _al_escribir(self, texto):
        if self._silencio or self._modo != "Clientes" or self._paso != 1:
            return
        self.aviso.clear()
        self._armar_lista(texto)

    def _armar_lista(self, texto):
        while self._caja_lista.count():
            item = self._caja_lista.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._filas = list(cerebro.sugerir(texto) or [])
        self._marca = 0 if self._filas else -1
        if not self._filas:
            self.lista.hide()
            self.ubicar()
            return
        for indice, cliente in enumerate(self._filas):
            ficha = dict(cliente) if not isinstance(cliente, dict) else cliente
            self._filas[indice] = ficha
            self._caja_lista.addWidget(_FilaNombre(self, indice, ficha))
        self.lista.setMinimumHeight(62 * len(self._filas))
        self.lista.show()
        self._pintar_marca()
        self.ubicar()

    def _pintar_marca(self):
        for indice in range(self._caja_lista.count()):
            fila = self._caja_lista.itemAt(indice).widget()
            if fila is None:
                continue
            if indice == self._marca:
                fila.setStyleSheet("background: #EFF6FF; border: none; border-bottom: 1px solid #E2E8F0;")
            else:
                fila.setStyleSheet("background: #FFFFFF; border: none; border-bottom: 1px solid #E2E8F0;")

    def _tocar(self, indice):
        if not (0 <= indice < len(self._filas)):
            return
        ficha = self._filas[indice]
        self._tomar_lista(ficha)

    def _cerrar_lista(self):
        while self._caja_lista.count():
            item = self._caja_lista.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.lista.setMinimumHeight(0)
        self.lista.hide()
        self._filas = []
        self._marca = -1

    def _elegida(self):
        if 0 <= self._marca < len(self._filas):
            return self._filas[self._marca]
        return None

    def _fallo(self, mensaje, alarma=False):
        if alarma:
            sonar_alarma_limite_fiado()
        self.aviso.setTextFormat(Qt.TextFormat.PlainText)
        self.aviso.setStyleSheet("color: #EF4444; font-size: 18px; font-weight: 800;")
        self.aviso.setText(mensaje)
        self.ubicar()
        self.caja.setFocus()
        self.caja.selectAll()

    def _pasar(self, cliente, ref):
        self._cliente = cliente
        self._ref = ref
        self._paso = 2
        self._pintar_paso()
        self.ubicar()

    def _cargar(self):
        texto = self.caja.text()
        if self._modo == "Fiado":
            if not cerebro.normalizar_dni(texto):
                self._fallo("DNI inválido. Mínimo 7 dígitos.")
                return
            cliente, estado, msg = cerebro.identificar_dni(texto)
            if estado == "error" or not cliente:
                self._fallo(msg or "No se pudo identificar al cliente.")
                return
            if cerebro.limite_excedido(cliente, self._monto):
                self._avisar_cupo(cliente, cerebro.normalizar_dni(texto))
                return
            self._pasar(cliente, cerebro.normalizar_dni(texto))
            return
        elegido = self._elegida()
        if elegido:
            self._tomar_lista(elegido)
            return
        if len(self._filas) > 1:
            self._fallo("Hay más de un cliente. Elegí el de la lista por el DNI.")
            return
        if len(self._filas) == 1:
            self._tomar_lista(dict(self._filas[0]))
            return
        cliente, estado, msg = cerebro.identificar_nombre(texto.strip())
        if estado == "error" or not cliente:
            self._fallo(msg or "No se pudo identificar al cliente.")
            return
        if cerebro.limite_excedido(cliente, self._monto):
            self._avisar_cupo(cliente, str(dict(cliente).get("nombre") or texto.strip()))
            return
        self._pasar(cliente, str(dict(cliente).get("nombre") or texto.strip()))

    def _tomar_lista(self, cliente):
        if cerebro.limite_excedido(cliente, self._monto):
            self._avisar_cupo(cliente, str(cliente.get("nombre") or ""))
            return
        self._pasar(cliente, str(cliente.get("nombre") or ""))

    def _aviso(self):
        nodo = self.parentWidget()
        while nodo is not None:
            aviso = getattr(nodo, "aviso_toast", None)
            if aviso is not None:
                return aviso
            nodo = nodo.parentWidget()
        return None

    def _avisar_cupo(self, cliente, ref):
        self._cliente = cliente
        self._ref = ref
        self._pin = ""
        self._pidiendo_pin = True
        limite = float(dict(cliente).get("limite_credito", 0))
        disp = cerebro.credito_disponible(cliente)
        exceso = max(0.0, float(self._monto or 0) - disp)
        sonar_alarma_limite_fiado()
        self.aviso.setTextFormat(Qt.TextFormat.RichText)
        self.aviso.setStyleSheet("font-size: 18px; font-weight: 800; background: transparent; border: none;")
        self.aviso.setText(
            "<span style='color:#EF4444;'>Límite superado</span><br>"
            f"<span style='color:#047857;'>crédito: $ {limite:,.0f}</span><br>"
            f"<span style='color:#EF4444;'>exceso: $ {exceso:,.2f}</span>"
        )
        aviso = self._aviso()
        if aviso is not None:
            aviso.pin("Límite superado. PIN de admin")
        self.ubicar()
        self.caja.setFocus()

    def _pintar_pin(self, frase="Límite superado. PIN de admin"):
        aviso = self._aviso()
        if aviso is not None:
            aviso.pin(frase, len(self._pin))

    def _cerrar_pin(self):
        quien = quien_autoriza(self._pin)
        if not quien:
            self._pin = ""
            sonar_alarma_limite_fiado()
            self._pintar_pin("PIN incorrecto. PIN de admin")
            return
        cliente = self._cliente
        ref = self._ref
        cliente_id = dict(cliente or {}).get("id")
        self._soltar_pin()
        if not cliente_id:
            self._fallo("No se pudo identificar al cliente.")
            return
        cerebro.conceder_excepcion(cliente_id, self._monto, quien)
        self._pasar(cliente, ref)

    def _soltar_pin(self):
        self._pidiendo_pin = False
        self._pin = ""
        aviso = self._aviso()
        if aviso is not None:
            aviso.cerrar()

    def _repetir(self):
        if self._modo == "Fiado":
            otro = cerebro.normalizar_dni(self.caja.text())
            if not otro:
                self._fallo("Ingrese el DNI nuevamente.")
                return
            coincide = otro == self._ref
            distinto = "El DNI no coincide. Pida que lo repita."
        else:
            otro = self.caja.text().strip()
            if not otro:
                self._fallo("Ingrese el nombre nuevamente.")
                return
            coincide = otro.lower() == str(self._ref or "").strip().lower()
            distinto = "El nombre no coincide. Pida que lo repita."
        if not coincide:
            sonar_dni_no_coincide()
            self._fallo(distinto)
            return
        cliente_id = dict(self._cliente or {}).get("id")
        self.ocultar()
        if cliente_id:
            self.listo.emit(int(cliente_id))

    def _cancelar(self):
        if self._pidiendo_pin:
            self._soltar_pin()
            cerebro.soltar_excepcion()
            return
        cerebro.soltar_excepcion()
        self.ocultar()
        self.cancelado.emit()
