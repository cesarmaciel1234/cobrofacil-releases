from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QCursor


# Sin :hover: al pintar la fila activa Qt reevalúa hover y se traba la flecha.
_ESTILO_FILA = (
    "QFrame { background: #FFFFFF; border-bottom: 2px solid #F1F5F9; border-radius: 0px; }"
)
_ESTILO_FILA_ACTIVA = (
    "QFrame { background: #E2E8F0; border-bottom: 2px solid #CBD5E1; border-radius: 0px; }"
)


class FilaSugerencia(QFrame):
    seleccionada = pyqtSignal(dict)

    def __init__(self, indice, parent=None):
        super().__init__(parent)
        self.indice = int(indice)
        self.cliente = {}
        self._activa = False
        self.setFixedHeight(72)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(_ESTILO_FILA)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(2)

        self.lbl_nombre = QLabel("")
        self.lbl_nombre.setStyleSheet("color: #0F172A; font-size: 22px; font-weight: 900; background: transparent; border: none;")
        lay.addWidget(self.lbl_nombre)

        self.lbl_dni = QLabel("")
        self.lbl_dni.setStyleSheet("color: #475569; font-size: 16px; font-weight: 700; background: transparent; border: none;")
        lay.addWidget(self.lbl_dni)

    def cargar(self, cliente, indice):
        self.indice = int(indice)
        self.cliente = dict(cliente) if hasattr(cliente, "keys") else (cliente if isinstance(cliente, dict) else {})
        nombre_str = str(self.cliente.get("nombre") or self.cliente.get("nombre_completo") or "")
        self.lbl_nombre.setText(nombre_str)
        dni = str(self.cliente.get("dni") or "").strip()
        self.lbl_dni.setText(f"DNI: {dni}" if dni else "Sin DNI")

    def marcar(self, activa):
        activa = bool(activa)
        if self._activa == activa:
            return
        self._activa = activa
        self.setStyleSheet(_ESTILO_FILA_ACTIVA if activa else _ESTILO_FILA)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.seleccionada.emit(self.cliente)


class PanelBuscadorClientes(QWidget):
    texto_cambiado = pyqtSignal(str)
    cliente_elegido = pyqtSignal(dict)
    creacion_solicitada = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._clientes_actuales = []
        self._indice_seleccionado = -1

        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(15)

        self.lbl_titulo = QLabel("CRÉDITO")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #0F172A; font-size: 32px; font-weight: 900; letter-spacing: 2px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_subtitulo = QLabel("Pida el DNI o el nombre del cliente.")
        self.lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitulo.setStyleSheet("color: #64748B; font-size: 18px; font-weight: 700; margin-bottom: 10px;")
        lay.addWidget(self.lbl_subtitulo)

        self.cont_busqueda = QFrame()
        self.cont_busqueda.setStyleSheet("background: transparent;")
        lay_busq = QVBoxLayout(self.cont_busqueda)
        lay_busq.setContentsMargins(0, 0, 0, 0)

        self.caja_busqueda = QLineEdit()
        self.caja_busqueda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caja_busqueda.setMinimumHeight(76)
        self.caja_busqueda.setPlaceholderText("Ej: Juan Perez o 34123456")
        self.caja_busqueda.setStyleSheet(
            "QLineEdit { background: #F8FAFC; color: #0F172A; border: 3px solid #CBD5E1; border-radius: 12px; padding: 10px 20px; font-size: 28px; font-weight: 900; }"
            "QLineEdit:focus { border: 3px solid #2563EB; background: #FFFFFF; }"
        )
        self.caja_busqueda.textChanged.connect(self.texto_cambiado.emit)
        self.caja_busqueda.installEventFilter(self)
        lay_busq.addWidget(self.caja_busqueda)

        self.lbl_sin_coincidencia = QLabel("No hay coincidencia. Presione ENTER para guardar como nuevo cliente")
        self.lbl_sin_coincidencia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sin_coincidencia.setStyleSheet("color: #64748B; font-size: 18px; font-weight: 700; margin-top: 10px;")
        self.lbl_sin_coincidencia.hide()
        lay_busq.addWidget(self.lbl_sin_coincidencia)

        lay.addWidget(self.cont_busqueda)

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setMinimumHeight(50)
        self.lbl_error.setStyleSheet(
            "QLabel { background: #FEF2F2; color: #DC2626; border: 2px solid #F87171; border-radius: 8px; padding: 5px 15px; font-size: 18px; font-weight: 900; margin-top: -10px; }"
        )
        self.lbl_error.hide()
        lay.addWidget(self.lbl_error)

        self.lista_sugerencias = QFrame()
        self.lista_sugerencias.setObjectName("ListaSugerencias")
        self.lista_sugerencias.setStyleSheet(
            "QFrame#ListaSugerencias { background: #FFFFFF; border: 3px solid #E2E8F0; border-radius: 12px; }"
        )

        self.lay_lista = QVBoxLayout(self.lista_sugerencias)
        self.lay_lista.setContentsMargins(0, 5, 0, 5)
        self.lay_lista.setSpacing(0)
        self._filas = []
        for i in range(5):
            fila = FilaSugerencia(i)
            fila.seleccionada.connect(self.cliente_elegido.emit)
            fila.hide()
            self.lay_lista.addWidget(fila)
            self._filas.append(fila)
        self.lista_sugerencias.hide()
        lay.addWidget(self.lista_sugerencias)

        lay.addStretch(1)

    def aplicar_modo(self, modo):
        if modo == "MasCredito":
            self.lbl_titulo.setText("COBRANZA")
            self.lbl_subtitulo.setText("Busque el cliente para abonar o liquidar.")
        else:
            self.lbl_titulo.setText("CRÉDITO")
            self.lbl_subtitulo.setText("Pida el DNI o el nombre del cliente.")

    def eventFilter(self, obj, event):
        if obj is self.caja_busqueda and event.type() == QEvent.Type.KeyPress:
            k = event.key()
            if k in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                if event.isAutoRepeat():
                    return True
                self.navegar("abajo" if k == Qt.Key.Key_Down else "arriba")
                return True
            if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.aceptar_actual()
                return True
        return super().eventFilter(obj, event)

    def mostrar_sugerencias(self, clientes):
        self._clientes_actuales = list(clientes[:5] if clientes else [])
        self._indice_seleccionado = 0 if len(self._clientes_actuales) == 1 else -1

        if not self._clientes_actuales:
            self.lista_sugerencias.hide()
            for fila in self._filas:
                fila.hide()
            if self.caja_busqueda.text().strip():
                self.lbl_sin_coincidencia.show()
            else:
                self.lbl_sin_coincidencia.hide()
            return

        self.lbl_sin_coincidencia.hide()
        for i, fila in enumerate(self._filas):
            if i < len(self._clientes_actuales):
                fila.cargar(self._clientes_actuales[i], i)
                fila.show()
            else:
                fila.hide()
        self.lista_sugerencias.show()
        self._pintar_filas()

    def limpiar(self):
        self.caja_busqueda.clear()
        self.mostrar_sugerencias([])

    def focus_caja(self):
        self.caja_busqueda.setFocus()

    def _pintar_filas(self):
        for i, w in enumerate(self._filas):
            w.marcar(w.isVisible() and i == self._indice_seleccionado)

    def navegar(self, direccion):
        if not self._clientes_actuales:
            return True
        n = len(self._clientes_actuales)
        if n <= 0:
            return True
        anterior = self._indice_seleccionado
        if self._indice_seleccionado < 0:
            self._indice_seleccionado = 0 if direccion == "abajo" else n - 1
        elif direccion == "arriba":
            self._indice_seleccionado = (self._indice_seleccionado - 1) % n
        else:
            self._indice_seleccionado = (self._indice_seleccionado + 1) % n
        if self._indice_seleccionado != anterior:
            self._pintar_filas()
        return True

    def aceptar_actual(self):
        texto = self.caja_busqueda.text().strip()

        if not self._clientes_actuales:
            if texto:
                try:
                    from src.clientes_fiado.cerebro.cerebro import cerebro
                    solo_num = texto.replace(".", "").replace(" ", "").replace("-", "")
                    existente = None
                    if solo_num.isdigit() and len(solo_num) >= 7:
                        existente = cerebro.buscar_por_dni(solo_num)
                    if not existente:
                        existente = cerebro.buscar_por_nombre(texto)
                    if existente:
                        self._emitir_cliente(dict(existente))
                        return True
                except Exception:
                    pass
                self.creacion_solicitada.emit(texto)
                return True
            return False

        if len(self._clientes_actuales) == 1:
            self._emitir_cliente(self._clientes_actuales[0])
            return True

        if 0 <= self._indice_seleccionado < len(self._clientes_actuales):
            self._emitir_cliente(self._clientes_actuales[self._indice_seleccionado])
            return True

        return False

    def _emitir_cliente(self, c):
        c_dict = dict(c) if hasattr(c, "keys") else (c if isinstance(c, dict) else {})
        self.cliente_elegido.emit(c_dict)
