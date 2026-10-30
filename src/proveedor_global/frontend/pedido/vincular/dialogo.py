from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QMessageBox, QLineEdit,
    QAbstractItemView, QCompleter,
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from src.motor_abastecimiento import MotorAbastecimiento
from src.proveedor_global.backend.ficha import FichaProveedor, etiqueta
from src.proveedor_global.frontend.pedido.alta.dialogo import DialogoAltaProveedor
from src.utils.letra import vestir_id, vestir_nombre


class _HiloDepartamentos(QThread):
    """Pide al inventario la lista de departamentos, fuera de la ventana."""
    listo = pyqtSignal(list)

    def run(self):
        nombres = []
        vistos = set()
        try:
            from src.motor_inventario.motor_departamentos import MotorDepartamentos

            for fila in MotorDepartamentos().obtener_departamentos() or []:
                nombre = ""
                if isinstance(fila, dict):
                    nombre = str(fila.get("nombre") or "").strip()
                elif fila:
                    nombre = str(fila[1] if len(fila) > 1 else fila[0]).strip()
                if nombre and nombre.upper() not in vistos:
                    vistos.add(nombre.upper())
                    nombres.append(nombre)
        except Exception:
            pass
        try:
            from src.base_de_datos.database import db_manager

            extra = db_manager.execute_query(
                "SELECT DISTINCT departamento FROM productos "
                "WHERE departamento IS NOT NULL AND TRIM(departamento) != ''"
            ) or []
            for fila in extra:
                nombre = str(
                    (fila.get("departamento") if isinstance(fila, dict) else fila[0]) or ""
                ).strip()
                if nombre and nombre.upper() not in vistos:
                    vistos.add(nombre.upper())
                    nombres.append(nombre)
        except Exception:
            pass
        nombres.sort(key=str.upper)
        self.listo.emit(nombres)


class _HiloProductos(QThread):
    """Busca productos por las iniciales, dentro del departamento si hay uno."""
    listo = pyqtSignal(int, list)

    def __init__(self, texto, generacion, departamento=""):
        super().__init__()
        self._texto = texto
        self._generacion = generacion
        self._departamento = departamento

    def run(self):
        try:
            from src.proveedor_global.backend.recepcion_service import RecepcionService

            filas = RecepcionService.buscar_productos_por_iniciales(
                self._texto, 12, self._departamento,
            )
        except Exception:
            filas = []
        self.listo.emit(self._generacion, filas)


class DialogoVincularProveedor(QDialog):
    """Asigna un proveedor a un departamento o a un producto. El alta se siente igual con o sin tienda."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asignar proveedor")
        self._producto = None
        self._coincidencias = []
        self._generacion = 0
        self.setMinimumWidth(480)
        self.resize(520, 480)
        self.setStyleSheet(f"""
            QDialog {{ background: #FFFFFF; font-family: 'Segoe UI', sans-serif; }}
            QLabel {{ font-size: 12px; font-weight: 700; color: #1E293B; }}
            QLineEdit, QComboBox {{
                border: 1px solid #CBD5E1; border-radius: 8px; padding: 8px;
                font-size: 13px; color: #0F172A; background: #F8FAFC;
            }}
            QLineEdit:focus, QComboBox:focus {{ border: 1.5px solid #2563EB; background: #FFFFFF; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        self.lbl_pista = QLabel("Elegí un departamento. La lista solo muestra productos de ahí.")
        self.lbl_pista.setWordWrap(True)
        self.lbl_pista.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 400;")
        lay.addWidget(self.lbl_pista)

        lay.addWidget(QLabel("Departamento"))
        self.cb_depto = QComboBox()
        self.cb_depto.addItem("Cargando…", "")
        self.cb_depto.currentIndexChanged.connect(self._al_cambiar_depto)
        lay.addWidget(self.cb_depto)
        self._hilo_deptos = _HiloDepartamentos(self)
        self._hilo_deptos.listo.connect(self._poblar_departamentos)
        self._hilo_deptos.start()

        lay.addWidget(QLabel("Producto"))
        self.txt_valor = QLineEdit()
        self.txt_valor.setPlaceholderText("Nombre, otra palabra o código")
        self.txt_valor.installEventFilter(self)
        self.txt_valor.textChanged.connect(self._al_escribir)
        lay.addWidget(self.txt_valor)

        self.lbl_vacio = QLabel("")
        self.lbl_vacio.setWordWrap(True)
        self.lbl_vacio.setStyleSheet("color: #9A3412; font-size: 12px; font-weight: 600;")
        self.lbl_vacio.hide()
        lay.addWidget(self.lbl_vacio)

        self.lbl_elegido = QLabel("")
        self.lbl_elegido.setWordWrap(True)
        self.lbl_elegido.setStyleSheet("color: #1D4ED8; font-size: 13px; font-weight: 700;")
        self.lbl_elegido.hide()
        lay.addWidget(self.lbl_elegido)

        self.tbl_productos = QTableWidget(0, 3)
        self.tbl_productos.setHorizontalHeaderLabels(["Código", "Producto", "Depto"])
        self.tbl_productos.verticalHeader().setVisible(False)
        self.tbl_productos.setShowGrid(False)
        self.tbl_productos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_productos.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_productos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_productos.setMaximumHeight(196)
        self.tbl_productos.hide()
        cab = self.tbl_productos.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_productos.cellClicked.connect(lambda fila, _c: self._elegir_fila(fila))
        lay.addWidget(self.tbl_productos)
        self._reloj = QTimer(self)
        self._reloj.setSingleShot(True)
        self._reloj.timeout.connect(self._buscar_producto)
        self._coincidencias = []

        lay.addWidget(QLabel("Proveedor"))
        self.cb_proveedor = QComboBox()
        self.cb_proveedor.setEditable(True)
        self.cb_proveedor.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cb_proveedor.lineEdit().setPlaceholderText("Escribí el nombre. Si no existe, se crea.")
        completar = QCompleter(self.cb_proveedor.model(), self)
        completar.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completar.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        completar.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.cb_proveedor.setCompleter(completar)
        if self.cb_proveedor.lineEdit():
            self.cb_proveedor.lineEdit().installEventFilter(self)
        lay.addWidget(self.cb_proveedor)
        self.cb_proveedor.currentIndexChanged.connect(self._al_elegir_ficha)

        lay.addWidget(QLabel("Teléfono"))
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Opcional. Si la ficha ya lo tiene, se completa.")
        self.txt_telefono.installEventFilter(self)
        lay.addWidget(self.txt_telefono)
        self._cargar_fichas()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setAutoDefault(False)
        btn_cancel.setDefault(False)
        btn_cancel.setStyleSheet("background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; border-radius: 8px; padding: 8px 16px; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_guardar = QPushButton("Guardar vínculo")
        btn_guardar.setAutoDefault(True)
        btn_guardar.setDefault(True)
        btn_guardar.setStyleSheet("background: #2563EB; color: white; border: none; border-radius: 8px; padding: 8px 18px; font-weight: bold;")
        btn_guardar.clicked.connect(self._guardar)
        btn_box.addWidget(btn_guardar)
        self.btn_guardar = btn_guardar
        lay.addLayout(btn_box)

    def _poblar_departamentos(self, nombres):
        self.cb_depto.blockSignals(True)
        self.cb_depto.clear()
        self.cb_depto.addItem("Todos los departamentos", "")
        for nombre in nombres or []:
            self.cb_depto.addItem(nombre, nombre)
        self.cb_depto.blockSignals(False)
        self._poner_pista()

    def _depto_elegido(self) -> str:
        return str(self.cb_depto.currentData() or "").strip()

    def _poner_pista(self):
        depto = self._depto_elegido()
        if depto:
            self.lbl_pista.setText(f"Solo productos de {depto}.")
            self.txt_valor.setPlaceholderText("Nombre, otra palabra o código")
        else:
            self.lbl_pista.setText("Sin departamento, la lista recorre todo el catálogo.")
            self.txt_valor.setPlaceholderText("Nombre, otra palabra o código")

    def _al_cambiar_depto(self):
        depto = self._depto_elegido().upper()
        if self._producto:
            actual = str(self._producto.get("departamento") or "").strip().upper()
            if depto and actual != depto:
                self._producto = None
                self.lbl_elegido.hide()
        self._poner_pista()
        self.lbl_vacio.hide()
        consulta = self.txt_valor.text().strip()
        if len(consulta) >= 2 or consulta.isdigit():
            self._reloj.start(80)

    def _al_escribir(self, texto):
        self._producto = None
        self.lbl_elegido.hide()
        self.lbl_vacio.hide()
        consulta = (texto or "").strip()
        if len(consulta) < 2 and not consulta.isdigit():
            self._reloj.stop()
            self._generacion += 1
            self.tbl_productos.setRowCount(0)
            self.tbl_productos.hide()
            return
        self._reloj.start(160)

    def _buscar_producto(self):
        self._generacion += 1
        hilo = _HiloProductos(self.txt_valor.text(), self._generacion, self._depto_elegido())
        hilo.setParent(self)
        hilo.listo.connect(self._pintar_productos)
        hilo.finished.connect(hilo.deleteLater)
        hilo.start()

    def _duenos_producto(self) -> dict:
        from src.motor_abastecimiento.enlace.puente_proveedor import obtener_mapeos

        salida = {}
        for fila in obtener_mapeos() or []:
            if str(fila.get("criterio_tipo") or "").lower() != "producto_id":
                continue
            valor = str(fila.get("criterio_valor") or "").strip().upper()
            nombre = str(fila.get("proveedor_nombre") or "").strip()
            if valor and nombre:
                salida[valor] = nombre
        return salida

    def _dueno_de(self, ficha, duenos) -> str:
        for clave in (ficha.get("id"), ficha.get("codigo")):
            texto = str(clave or "").strip().upper()
            if texto and texto in duenos:
                return duenos[texto]
        return ""

    def _pintar_productos(self, generacion, filas):
        if generacion != self._generacion:
            return
        duenos = self._duenos_producto()
        self._coincidencias = []
        self.tbl_productos.setRowCount(0)
        ocupado = QColor("#B45309")
        fondo = QColor("#FFFBEB")
        for cruda in filas or []:
            ficha = dict(cruda)
            dueno = self._dueno_de(ficha, duenos)
            ficha["_proveedor"] = dueno
            self._coincidencias.append(ficha)
            fila = self.tbl_productos.rowCount()
            self.tbl_productos.insertRow(fila)
            nombre = str(ficha.get("nombre") or "")
            if dueno:
                nombre = f"{dueno}  ·  {nombre}"
            celdas = [
                vestir_id(QTableWidgetItem(str(ficha.get("codigo") or ficha.get("id") or ""))),
                vestir_nombre(QTableWidgetItem(nombre)),
            ]
            depto = QTableWidgetItem(str(ficha.get("departamento") or ""))
            depto.setFont(QFont("Segoe UI", 10))
            celdas.append(depto)
            for col, celda in enumerate(celdas):
                if dueno:
                    celda.setForeground(ocupado)
                    celda.setBackground(fondo)
                self.tbl_productos.setItem(fila, col, celda)
        self.tbl_productos.setColumnHidden(2, bool(self._depto_elegido()))
        self.tbl_productos.setVisible(bool(self._coincidencias))
        if self._coincidencias:
            self.lbl_vacio.hide()
            libre = next((i for i, f in enumerate(self._coincidencias) if not f.get("_proveedor")), -1)
            if libre >= 0:
                self.tbl_productos.selectRow(libre)
            return
        depto = self._depto_elegido()
        if depto:
            self.lbl_vacio.setText(f"En {depto} no hay productos con ese nombre o código.")
            self.lbl_vacio.show()
        else:
            self.lbl_vacio.hide()

    def _elegir_fila(self, fila):
        if fila < 0 or fila >= len(self._coincidencias):
            return
        self._producto = self._coincidencias[fila]
        dueno = str(self._producto.get("_proveedor") or "").strip()
        if dueno:
            self._producto = None
            self.lbl_elegido.hide()
            self.lbl_vacio.setText(f"Ya está con {dueno}. Desenlazalo antes de pasarlo a otro.")
            self.lbl_vacio.show()
            return
        self._generacion += 1
        self.tbl_productos.hide()
        self.lbl_vacio.hide()
        self.txt_valor.blockSignals(True)
        self.txt_valor.setText(str(self._producto.get("nombre") or ""))
        self.txt_valor.blockSignals(False)
        codigo = self._producto.get("codigo") or self._producto.get("id")
        self.lbl_elegido.setText(f"Enlaza  {self._producto.get('nombre')}  ·  {codigo}")
        self.lbl_elegido.show()
        self.cb_proveedor.setFocus()

    def _enter_guarda(self, obj) -> bool:
        if obj is self.txt_telefono:
            return True
        linea = self.cb_proveedor.lineEdit()
        if obj is not linea:
            return False
        popup = self.cb_proveedor.completer().popup() if self.cb_proveedor.completer() else None
        return not (popup is not None and popup.isVisible())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._enter_guarda(obj):
                self._guardar()
                return True
        if obj is self.txt_valor and event.type() == QEvent.Type.KeyPress:
            tecla = event.key()
            if tecla in (Qt.Key.Key_Down, Qt.Key.Key_Up) and self.tbl_productos.isVisible():
                actual = self.tbl_productos.currentRow()
                paso = 1 if tecla == Qt.Key.Key_Down else -1
                destino = max(0, min(self.tbl_productos.rowCount() - 1, actual + paso))
                self.tbl_productos.selectRow(destino)
                return True
            if tecla in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.tbl_productos.isVisible() and self.tbl_productos.rowCount():
                    self._elegir_fila(max(0, self.tbl_productos.currentRow()))
                    return True
                if self._es_pistola(self.txt_valor.text()):
                    self._elegir_pistola()
                    return True
        return super().eventFilter(obj, event)

    def _es_pistola(self, texto: str) -> bool:
        limpio = (texto or "").strip()
        return len(limpio) >= 4 and limpio.isdigit()

    def _elegir_pistola(self):
        """La pistola manda el código y Enter antes de que la lista pinte."""
        self._reloj.stop()
        self._generacion += 1
        from src.proveedor_global.backend.recepcion_service import RecepcionService

        codigo = self.txt_valor.text().strip()
        filas = RecepcionService.buscar_productos_por_iniciales(
            codigo, 12, self._depto_elegido(),
        )
        self._pintar_productos(self._generacion, filas)
        for i, ficha in enumerate(filas):
            pid = str(ficha.get("id") or "")
            cod = str(ficha.get("codigo") or "")
            if codigo == pid or codigo == cod:
                self._elegir_fila(i)
                return
        if len(filas) == 1:
            self._elegir_fila(0)

    def _cargar_fichas(self, seleccionar_id=None, seleccionar_nombre=None):
        self.cb_proveedor.blockSignals(True)
        self.cb_proveedor.clear()
        indice = -1
        for ficha in FichaProveedor.listar():
            self.cb_proveedor.addItem(etiqueta(ficha), ficha)
            actual = self.cb_proveedor.count() - 1
            if seleccionar_id and ficha.get("id") == seleccionar_id:
                indice = actual
            elif indice < 0 and seleccionar_nombre and str(ficha.get("nombre") or "").upper() == seleccionar_nombre.upper():
                indice = actual
        if indice >= 0:
            self.cb_proveedor.setCurrentIndex(indice)
        else:
            self.cb_proveedor.setCurrentIndex(-1)
            if self.cb_proveedor.lineEdit():
                self.cb_proveedor.lineEdit().clear()
        self.cb_proveedor.blockSignals(False)
        if indice >= 0:
            self._al_elegir_ficha()

    def _alta(self):
        alta = DialogoAltaProveedor(self)
        if alta.exec() != QDialog.DialogCode.Accepted or not alta.ficha:
            return
        self._cargar_fichas(alta.ficha.get("id"), alta.ficha.get("nombre"))

    def _al_elegir_ficha(self):
        ficha = self.cb_proveedor.currentData()
        texto = self.cb_proveedor.currentText().strip()
        if isinstance(ficha, dict) and etiqueta(ficha).strip().upper() == texto.upper():
            if ficha.get("telefono"):
                self.txt_telefono.setText(ficha.get("telefono") or "")

    def _ficha_proveedor(self, nombre, telefono):
        elegido = self.cb_proveedor.currentData()
        if isinstance(elegido, dict) and etiqueta(elegido).strip().upper() == nombre.upper():
            return elegido
        ok, resultado = FichaProveedor.crear(nombre, telefono)
        if not ok or not isinstance(resultado, dict):
            QMessageBox.warning(self, "No se creó", str(resultado))
            return None
        return resultado

    def _guardar(self):
        nombre = self.cb_proveedor.currentText().strip()
        if not nombre:
            QMessageBox.warning(self, "Sin proveedor", "Escribí el nombre del proveedor.")
            return
        if self.txt_valor.text().strip() and not self._producto and self.tbl_productos.isVisible():
            self._elegir_fila(max(0, self.tbl_productos.currentRow()))
            if not self._producto:
                return
        if self._producto and str(self._producto.get("_proveedor") or "").strip():
            QMessageBox.warning(
                self, "Ya tiene proveedor",
                f"Ya está con {self._producto.get('_proveedor')}. Desenlazalo antes de pasarlo a otro.",
            )
            return
        if self._producto:
            tipo = "producto_id"
            val = str(self._producto.get("id") or "").strip()
            visible = self._producto.get("nombre") or val
            if not val:
                QMessageBox.warning(self, "Sin producto", "Elegí un producto de la lista.")
                return
        else:
            tipo = "departamento"
            val = str(self.cb_depto.currentData() or "").strip()
            visible = val
            if not val:
                QMessageBox.warning(
                    self, "Falta el destino",
                    "Elegí un departamento o un producto de la lista.",
                )
                return
        tel = self.txt_telefono.text().strip()
        ficha = self._ficha_proveedor(nombre, tel)
        if not ficha:
            return
        tel = tel or ficha.get("telefono") or ""
        ok = MotorAbastecimiento.vincular_proveedor(
            tipo, val, ficha["nombre"], tel, "", ficha.get("id") or None,
        )
        if not ok:
            QMessageBox.warning(self, "No se asignó", "No se pudo guardar el vínculo.")
            return
        QMessageBox.information(
            self, "Vínculo guardado",
            f"Se asignó {ficha.get('nombre')} a {visible}.",
        )
        self.accept()
