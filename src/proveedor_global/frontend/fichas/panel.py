"""Alta ya existe. Acá se listan los activos y se abre el historial de cada uno."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
    QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QCursor

from src.proveedor_global.backend.ficha import FichaProveedor, etiqueta
from src.proveedor_global.backend.moneda import texto
from src.proveedor_global.backend.motor_proveedor import MotorProveedor
from src.utils.letra import vestir_id, vestir_nombre, vestir_numero


def _dia(fecha) -> str:
    base = str(fecha or "").strip()[:10]
    partes = base.split("-")
    if len(partes) == 3 and len(partes[0]) == 4:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return base or str(fecha or "")


def _compras_de(nombre: str, filas: list[dict]) -> list[dict]:
    clave = (nombre or "").strip().upper()
    return [fila for fila in filas if str(fila.get("proveedor") or "").strip().upper() == clave]


def _lineas(desc: str) -> list[tuple[str, str]]:
    salida = []
    for cruda in str(desc or "").splitlines():
        linea = cruda.strip()
        if linea.startswith("•") or linea.startswith("-"):
            salida.append(("", linea.lstrip("•- ").strip()))
        elif linea.startswith("↳") or linea.startswith("  "):
            if salida:
                prev = salida[-1][1]
                salida[-1] = ("", f"{prev}  {linea.strip()}")
    return salida


class DialogoHistorialProveedor(QDialog):
    """Historial de compras de un proveedor. Misma forma que el del cliente."""

    def __init__(self, ficha: dict, parent=None):
        super().__init__(parent)
        self._ficha = dict(ficha or {})
        self._filas = _compras_de(
            self._ficha.get("nombre") or "",
            MotorProveedor.load_proveedores("admin"),
        )
        self.setWindowTitle("Historial del proveedor")
        self.setMinimumSize(920, 640)
        self.resize(1000, 720)
        self.setStyleSheet("QDialog { background: #F8FAFC; }")
        self._armar()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 20)
        lay.setSpacing(14)

        panel = QFrame()
        panel.setObjectName("fichaProveedor")
        panel.setStyleSheet(
            "QFrame#fichaProveedor { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px; }"
        )
        caja = QVBoxLayout(panel)
        caja.setContentsMargins(24, 20, 24, 18)
        caja.setSpacing(10)

        fila_tit = QHBoxLayout()
        self.lbl_tit = QLabel()
        self.lbl_tit.setStyleSheet("font-size: 18px; font-weight: 800; color: #1E293B; border: none;")
        fila_tit.addWidget(self.lbl_tit, stretch=1)
        btn_prod = QPushButton("Productos asociados")
        btn_prod.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_prod.setStyleSheet(
            "QPushButton { background: #EEF2FF; color: #3730A3; border: 1px solid #C7D2FE; "
            "border-radius: 8px; padding: 8px 12px; font-weight: 700; }"
            "QPushButton:hover { background: #E0E7FF; }"
        )
        btn_prod.clicked.connect(self._ver_productos)
        fila_tit.addWidget(btn_prod)
        btn_edit = QPushButton("Editar datos")
        btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_edit.setStyleSheet(
            "QPushButton { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; "
            "border-radius: 8px; padding: 8px 12px; font-weight: 700; }"
            "QPushButton:hover { background: #FDE68A; }"
        )
        btn_edit.clicked.connect(self._editar_datos)
        fila_tit.addWidget(btn_edit)
        caja.addLayout(fila_tit)

        self.lbl_meta = QLabel()
        self.lbl_meta.setWordWrap(True)
        self.lbl_meta.setStyleSheet("font-size: 13px; font-weight: 400; color: #64748B; border: none;")
        caja.addWidget(self.lbl_meta)
        self._pintar_cabecera()

        aviso = QLabel("Compras del más reciente al más antiguo. Tocá un renglón para ver el detalle.")
        aviso.setStyleSheet("font-size: 12px; font-weight: 400; color: #94A3B8; border: none;")
        caja.addWidget(aviso)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Tipo", "Monto", "Saldo", "Descripción", "Remito"]
        )
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for col in (0, 1, 2, 3, 5):
            cab.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0; border-radius: 10px;
                background: white; alternate-background-color: #F8FAFC; font-size: 13px;
            }
            QHeaderView::section {
                font-weight: 700; border: none; padding: 10px 8px;
                background: #F1F5F9; color: #334155;
            }
        """)
        self.tabla.cellClicked.connect(self._ver_detalle)
        self._pintar()

        self.detalle = QTableWidget(0, 2)
        self.detalle.setHorizontalHeaderLabels(["", "Detalle"])
        self.detalle.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.detalle.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.detalle.verticalHeader().setVisible(False)
        self.detalle.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.detalle.setStyleSheet(
            "QTableWidget { border: 1px solid #E2E8F0; border-radius: 10px; background: white; }"
        )
        self._pista = QLabel("Pulse el remito para ver el detalle de la compra.")
        self._pista.setStyleSheet("font-size: 12px; font-weight: 400; color: #94A3B8; border: none;")

        detalle_caja = QFrame()
        detalle_caja.setStyleSheet("QFrame { background: transparent; border: none; }")
        dlay = QVBoxLayout(detalle_caja)
        dlay.setContentsMargins(0, 0, 0, 0)
        dlay.addWidget(self._pista)
        dlay.addWidget(self.detalle)

        corte = QSplitter(Qt.Orientation.Vertical)
        corte.addWidget(self.tabla)
        corte.addWidget(detalle_caja)
        corte.setStretchFactor(0, 3)
        corte.setStretchFactor(1, 2)
        caja.addWidget(corte, stretch=1)

        self.lbl_pie = QLabel("")
        self.lbl_pie.setStyleSheet("font-size: 13px; font-weight: 700; color: #475569; border: none;")
        caja.addWidget(self.lbl_pie)
        self._pintar_cabecera()
        lay.addWidget(panel, stretch=1)

        pie = QHBoxLayout()
        pie.addStretch()
        cerrar = QPushButton("CERRAR")
        cerrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cerrar.setStyleSheet(
            "QPushButton { background: #3B82F6; color: white; font-weight: 700; "
            "padding: 12px 28px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #2563EB; }"
        )
        cerrar.clicked.connect(self.accept)
        pie.addWidget(cerrar)
        lay.addLayout(pie)

    def _pintar_cabecera(self):
        nombre = str(self._ficha.get("nombre") or "—").upper()
        self.lbl_tit.setText(f"HISTORIAL — {nombre}")
        self.setWindowTitle(f"Historial — {self._ficha.get('nombre') or 'proveedor'}")
        codigo = str(self._ficha.get("codigo") or "").strip()
        if not codigo or codigo.upper() == "EN CASA" or self._ficha.get("pendiente"):
            codigo = "sin código todavía"
        telefono = str(self._ficha.get("telefono") or "").strip() or "sin teléfono"
        total = sum(float(f.get("monto") or 0) for f in self._filas)
        pagado = sum(float(f.get("pagado") or 0) for f in self._filas)
        deuda = sum(float(f.get("restante") or 0) for f in self._filas)
        self.lbl_meta.setText(
            f"Código: {codigo}   ·   Teléfono: {telefono}   ·   "
            f"Compras: {texto(total)}   ·   Pagado: {texto(pagado)}   ·   Deuda: {texto(deuda)}"
        )
        if hasattr(self, "lbl_pie"):
            self.lbl_pie.setText(self._resumen(total, pagado, deuda))

    def _editar_datos(self):
        dlg = DialogoEditarProveedor(self._ficha, self)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.ficha:
            return
        self._ficha = dlg.ficha
        self._filas = _compras_de(
            self._ficha.get("nombre") or "",
            MotorProveedor.load_proveedores("admin"),
        )
        self._pintar_cabecera()
        self._pintar()

    def _ver_productos(self):
        DialogoProductosAsociados(self._ficha, self).exec()

    def _resumen(self, total, pagado, deuda) -> str:
        return (
            f"{len(self._filas)} compra(s)   ·   Total {texto(total)}   ·   "
            f"Pagado {texto(pagado)}   ·   Deuda {texto(deuda)}"
        )

    def _pintar(self):
        self.tabla.setRowCount(0)
        saldo = 0.0
        corrido = []
        for fila in reversed(self._filas):
            saldo += float(fila.get("restante") or 0)
            corrido.append((fila, saldo))
        for fila, saldo_fila in reversed(corrido):
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            pendiente = str(fila.get("estado") or "") in ("Pendiente", "pending")
            tipo = QTableWidgetItem("DEUDA" if pendiente else "CONTADO")
            tipo.setForeground(QColor("#DC2626" if pendiente else "#15803D"))
            monto = vestir_numero(QTableWidgetItem(texto(fila.get("monto") or 0)))
            monto.setForeground(QColor("#DC2626" if pendiente else "#15803D"))
            self.tabla.setItem(r, 0, vestir_id(QTableWidgetItem(_dia(fila.get("fecha")))))
            self.tabla.setItem(r, 1, tipo)
            self.tabla.setItem(r, 2, monto)
            self.tabla.setItem(r, 3, vestir_numero(QTableWidgetItem(texto(saldo_fila))))
            desc = str(fila.get("desc_full") or "").split("\n", 1)[0]
            desc = desc.replace("Recepción Escáner - ", "").replace("Proveedor:", "").strip() or "Compra"
            self.tabla.setItem(r, 4, vestir_nombre(QTableWidgetItem(desc)))
            remito = vestir_id(QTableWidgetItem(f"#{fila.get('id')}"))
            remito.setForeground(QColor("#2563EB"))
            self.tabla.setItem(r, 5, remito)
            self.tabla.item(r, 0).setData(Qt.ItemDataRole.UserRole, fila)

    def _ver_detalle(self, fila, _col):
        item = self.tabla.item(fila, 0)
        datos = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.detalle.setRowCount(0)
        lineas = _lineas((datos or {}).get("desc_full") or "")
        if not lineas:
            self._pista.setText("Esta compra no tiene renglones cargados.")
            return
        self._pista.setText(f"Remito #{(datos or {}).get('id')}")
        for marca, texto_linea in lineas:
            r = self.detalle.rowCount()
            self.detalle.insertRow(r)
            self.detalle.setItem(r, 0, QTableWidgetItem(marca))
            self.detalle.setItem(r, 1, vestir_nombre(QTableWidgetItem(texto_linea)))


class DialogoProveedoresActivos(QDialog):
    """Lista los proveedores activos. El nombre abre el historial."""

    def __init__(self, parent=None, embebido=False):
        super().__init__(parent)
        self._embebido = embebido
        if embebido:
            self.setWindowFlags(Qt.WindowType.Widget)
        self.setWindowTitle("Proveedores activos")
        self.setMinimumSize(720, 480)
        if not embebido:
            self.resize(780, 520)
        self.setStyleSheet("QDialog { background: #F8FAFC; } QWidget { background: #F8FAFC; }")
        self._compras = MotorProveedor.load_proveedores("admin")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 18)
        lay.setSpacing(12)
        titulo = QLabel("Proveedores activos")
        titulo.setStyleSheet("font-size: 18px; font-weight: 800; color: #1E293B;")
        lay.addWidget(titulo)
        pista = QLabel("Tocá el nombre para ver el historial de compras.")
        pista.setStyleSheet("font-size: 12px; font-weight: 400; color: #64748B;")
        lay.addWidget(pista)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Código", "Proveedor", "Teléfono", "Compras"])
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setStyleSheet("""
            QTableWidget { background: white; border: 1px solid #E2E8F0; border-radius: 10px; }
            QHeaderView::section {
                font-weight: 700; border: none; padding: 8px; background: #F1F5F9; color: #334155;
            }
        """)
        self.tabla.cellClicked.connect(self._al_clic)
        lay.addWidget(self.tabla, stretch=1)
        self._fichas = []
        self._pintar()

        if not embebido:
            pie = QHBoxLayout()
            pie.addStretch()
            cerrar = QPushButton("Cerrar")
            cerrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            cerrar.setStyleSheet(
                "QPushButton { background: #FFFFFF; color: #475569; border: 1px solid #CBD5E1; "
                "border-radius: 8px; padding: 8px 16px; font-weight: 700; }"
            )
            cerrar.clicked.connect(self.accept)
            pie.addWidget(cerrar)
            lay.addLayout(pie)

    def _pintar(self):
        self._fichas = FichaProveedor.listar()
        self.tabla.setRowCount(0)
        for ficha in self._fichas:
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            codigo = str(ficha.get("codigo") or "")
            if codigo.upper() == "EN CASA" or ficha.get("pendiente"):
                codigo = ""
            compras = len(_compras_de(ficha.get("nombre") or "", self._compras))
            self.tabla.setItem(r, 0, vestir_id(QTableWidgetItem(codigo)))
            nombre = vestir_nombre(QTableWidgetItem(etiqueta(ficha) or ficha.get("nombre") or ""))
            nombre.setForeground(QColor("#2563EB"))
            self.tabla.setItem(r, 1, nombre)
            self.tabla.setItem(r, 2, QTableWidgetItem(str(ficha.get("telefono") or "")))
            self.tabla.setItem(r, 3, vestir_numero(QTableWidgetItem(str(compras))))

    def _al_clic(self, fila, _columna):
        if fila < 0 or fila >= len(self._fichas):
            return
        DialogoHistorialProveedor(self._fichas[fila], self).exec()
        self._compras = MotorProveedor.load_proveedores("admin")
        self._pintar()


def _asociados(nombre: str) -> list[dict]:
    from src.motor_abastecimiento.enlace.puente_proveedor import obtener_mapeos

    clave = (nombre or "").strip().upper()
    salida = []
    db, _modo = MotorProveedor._get_read_db("admin")
    for fila in obtener_mapeos() or []:
        if str(fila.get("proveedor_nombre") or "").strip().upper() != clave:
            continue
        tipo = str(fila.get("criterio_tipo") or "").lower()
        valor = str(fila.get("criterio_valor") or "").strip()
        if tipo == "departamento":
            salida.append({
                "tipo": "Departamento",
                "codigo": "",
                "nombre": valor,
                "departamento": valor,
                "criterio_tipo": tipo,
                "criterio_valor": valor,
            })
            continue
        codigo, nom, depto = valor, valor, ""
        if db and valor:
            hallados = db.execute_query(
                "SELECT id, codigo, nombre, departamento FROM productos "
                "WHERE CAST(id AS TEXT) = ? OR UPPER(COALESCE(codigo, '')) = ? LIMIT 1",
                (valor, valor.upper()),
            ) or []
            if hallados:
                cruda = hallados[0]
                if isinstance(cruda, dict):
                    codigo = str(cruda.get("codigo") or cruda.get("id") or "")
                    nom = str(cruda.get("nombre") or valor)
                    depto = str(cruda.get("departamento") or "")
                else:
                    codigo = str(cruda[1] or cruda[0] or "")
                    nom = str(cruda[2] or valor)
                    depto = str(cruda[3] or "") if len(cruda) > 3 else ""
        salida.append({
            "tipo": "Producto",
            "codigo": codigo,
            "nombre": nom,
            "departamento": depto,
            "criterio_tipo": tipo,
            "criterio_valor": valor,
        })
    return salida


def _pasa_asociado(fila: dict, texto: str) -> bool:
    q = (texto or "").strip().upper()
    if not q:
        return True
    nombre = str(fila.get("nombre") or "").upper()
    codigo = str(fila.get("codigo") or "").upper()
    depto = str(fila.get("departamento") or "").upper()
    valor = str(fila.get("criterio_valor") or "").upper()
    if nombre.startswith(q) or f" {q}" in f" {nombre}":
        return True
    if codigo.startswith(q) or valor.startswith(q) or depto.startswith(q):
        return True
    return q in nombre or q in codigo or q in valor


class DialogoProductosAsociados(QDialog):
    def __init__(self, ficha: dict, parent=None):
        super().__init__(parent)
        self._ficha = dict(ficha or {})
        self._nombre = str(self._ficha.get("nombre") or "")
        self._filas = []
        self._visibles = []
        self._coincidencias = []
        self._reloj = QTimer(self)
        self._reloj.setSingleShot(True)
        self._reloj.timeout.connect(self._buscar_catalogo)
        self.setWindowTitle("Productos asociados")
        self.setMinimumSize(860, 560)
        self.resize(960, 640)
        self.setStyleSheet("QDialog { background: #F8FAFC; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 20)
        lay.setSpacing(14)

        panel = QFrame()
        panel.setObjectName("asociados")
        panel.setStyleSheet(
            "QFrame#asociados { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px; }"
        )
        caja = QVBoxLayout(panel)
        caja.setContentsMargins(24, 20, 24, 18)
        caja.setSpacing(10)

        self.lbl_tit = QLabel(f"PRODUCTOS — {self._nombre.upper()}")
        self.lbl_tit.setStyleSheet("font-size: 18px; font-weight: 800; color: #1E293B; border: none;")
        caja.addWidget(self.lbl_tit)
        self.lbl_meta = QLabel("Buscá un producto del catálogo para asociarlo, o uno ya enlazado para sacarlo.")
        self.lbl_meta.setStyleSheet("font-size: 13px; font-weight: 400; color: #64748B; border: none;")
        caja.addWidget(self.lbl_meta)

        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Nombre, otra palabra o código para asociar")
        self.buscar.setClearButtonEnabled(True)
        self.buscar.setStyleSheet(
            "QLineEdit { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; "
            "padding: 10px 12px; font-size: 14px; color: #1E293B; }"
            "QLineEdit:focus { border: 1px solid #93C5FD; background: white; }"
        )
        self.buscar.textChanged.connect(self._al_escribir)
        self.buscar.returnPressed.connect(self._enter_busqueda)
        caja.addWidget(self.buscar)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Código", "Producto", "Departamento", "Tipo"])
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (0, 2, 3):
            cab.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(46)
        self.tabla.horizontalHeader().setMinimumHeight(40)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(
            "QTableWidget { background: white; alternate-background-color: #F8FAFC; "
            "border: 1px solid #E2E8F0; border-radius: 10px; font-size: 13px; }"
            "QHeaderView::section { font-weight: 700; border: none; padding: 10px 8px; "
            "background: #F1F5F9; color: #334155; }"
            "QTableWidget::item { padding: 8px; }"
            "QTableWidget::item:selected { background: #DBEAFE; color: #1E293B; }"
        )
        self.tabla.itemSelectionChanged.connect(self._al_elegir)
        self.tabla.itemDoubleClicked.connect(lambda *_: self._accion_seleccion())
        caja.addWidget(self.tabla, stretch=1)

        self.lbl_estado = QLabel("")
        self.lbl_estado.setStyleSheet("font-size: 13px; font-weight: 700; color: #475569; border: none;")
        caja.addWidget(self.lbl_estado)
        lay.addWidget(panel, stretch=1)

        pie = QHBoxLayout()
        self.btn_asociar = QPushButton("ASOCIAR")
        self.btn_asociar.setEnabled(False)
        self.btn_asociar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_asociar.setStyleSheet(
            "QPushButton { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; "
            "border-radius: 8px; padding: 12px 20px; font-weight: 800; }"
            "QPushButton:hover { background: #D1FAE5; }"
            "QPushButton:disabled { background: #F1F5F9; color: #94A3B8; border-color: #E2E8F0; }"
        )
        self.btn_asociar.clicked.connect(self._asociar_seleccion)
        pie.addWidget(self.btn_asociar)
        self.btn_sacar = QPushButton("DESENLAZAR")
        self.btn_sacar.setEnabled(False)
        self.btn_sacar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sacar.setStyleSheet(
            "QPushButton { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; "
            "border-radius: 8px; padding: 12px 20px; font-weight: 800; }"
            "QPushButton:hover { background: #FECACA; }"
            "QPushButton:disabled { background: #F1F5F9; color: #94A3B8; border-color: #E2E8F0; }"
        )
        self.btn_sacar.clicked.connect(self._desenlazar_seleccion)
        pie.addWidget(self.btn_sacar)
        pie.addStretch()
        cerrar = QPushButton("CERRAR")
        cerrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cerrar.setStyleSheet(
            "QPushButton { background: #3B82F6; color: white; border: none; "
            "border-radius: 8px; padding: 12px 28px; font-weight: 800; }"
            "QPushButton:hover { background: #2563EB; }"
        )
        cerrar.clicked.connect(self.accept)
        pie.addWidget(cerrar)
        lay.addLayout(pie)
        self._cargar()

    def _cargar(self):
        self._filas = _asociados(self._nombre)
        self._pintar()

    def _al_escribir(self):
        self._pintar()
        self._reloj.start(250)

    def _buscar_catalogo(self):
        from src.proveedor_global.backend.recepcion_service import RecepcionService

        consulta = self.buscar.text().strip()
        if len(consulta) < 2 and not consulta.isdigit():
            self._coincidencias = []
        else:
            self._coincidencias = RecepcionService.buscar_productos_por_iniciales(consulta, 20, "")
        self._pintar()

    def _duenos(self) -> dict:
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

    def _para_asociar(self) -> list[dict]:
        ya = set()
        for fila in self._filas:
            ya.add(str(fila.get("criterio_valor") or "").strip().upper())
            ya.add(str(fila.get("codigo") or "").strip().upper())
        duenos = self._duenos()
        propio = self._nombre.strip().upper()
        salida = []
        for ficha in self._coincidencias or []:
            claves = [
                str(ficha.get("id") or "").strip().upper(),
                str(ficha.get("codigo") or "").strip().upper(),
            ]
            if any(clave and clave in ya for clave in claves):
                continue
            dueno = ""
            for clave in claves:
                if clave and clave in duenos:
                    dueno = duenos[clave]
                    break
            if dueno.strip().upper() == propio:
                continue
            nombre = str(ficha.get("nombre") or "")
            if dueno:
                nombre = f"{dueno}  ·  {nombre}"
            salida.append({
                "tipo": "Asociar",
                "codigo": str(ficha.get("codigo") or ficha.get("id") or ""),
                "nombre": nombre,
                "departamento": str(ficha.get("departamento") or ""),
                "criterio_tipo": "producto_id",
                "criterio_valor": str(ficha.get("id") or ficha.get("codigo") or ""),
                "nuevo": True,
                "ocupado": dueno,
            })
        return salida

    def _pintar(self):
        texto = self.buscar.text()
        self._visibles = [f for f in self._filas if _pasa_asociado(f, texto)]
        if texto.strip():
            self._visibles.extend(self._para_asociar())
        self.tabla.setRowCount(0)
        ambar = QColor("#B45309")
        fondo = QColor("#FFFBEB")
        for i, fila in enumerate(self._visibles):
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            codigo = vestir_id(QTableWidgetItem(fila.get("codigo") or ""))
            codigo.setData(Qt.ItemDataRole.UserRole, i)
            nombre = vestir_nombre(QTableWidgetItem(fila.get("nombre") or ""))
            if fila.get("ocupado"):
                nombre.setForeground(ambar)
                codigo.setForeground(ambar)
                codigo.setBackground(fondo)
                nombre.setBackground(fondo)
            elif fila.get("nuevo"):
                nombre.setForeground(QColor("#047857"))
            else:
                nombre.setForeground(QColor("#2563EB"))
            self.tabla.setItem(r, 0, codigo)
            self.tabla.setItem(r, 1, nombre)
            self.tabla.setItem(r, 2, QTableWidgetItem(fila.get("departamento") or ""))
            self.tabla.setItem(r, 3, QTableWidgetItem(fila.get("tipo") or ""))
        productos = sum(1 for f in self._filas if f.get("tipo") == "Producto")
        deptos = sum(1 for f in self._filas if f.get("tipo") == "Departamento")
        nuevas = sum(1 for f in self._visibles if f.get("nuevo"))
        if texto.strip() and nuevas:
            self.lbl_meta.setText(
                f"{nuevas} coincidencias para asociar a {self._nombre}. "
                "En ámbar ya están con otro proveedor."
            )
        elif not self._filas:
            self.lbl_meta.setText("Escribí un producto o un código para asociarlo a este proveedor.")
        else:
            self.lbl_meta.setText(
                f"{productos} productos · {deptos} departamentos. "
                "Buscá otro para asociarlo, o elegí uno para sacarlo."
            )
        aviso = self.lbl_estado.text()
        if texto.strip() and not self._visibles:
            self.lbl_estado.setText("No hay productos con ese nombre o código.")
        elif not aviso.startswith(("Salió", "Salieron", "Quedó", "Quedaron")):
            self.lbl_estado.setText("")
        self._al_elegir()

    def _elegidas(self) -> list[dict]:
        salida = []
        vistos = set()
        for idx in self.tabla.selectionModel().selectedRows():
            celda = self.tabla.item(idx.row(), 0)
            if celda is None:
                continue
            i = celda.data(Qt.ItemDataRole.UserRole)
            if i is None or i in vistos or i >= len(self._visibles):
                continue
            vistos.add(i)
            salida.append(self._visibles[i])
        return salida

    def _al_elegir(self):
        elegidas = self._elegidas()
        nuevas = [f for f in elegidas if f.get("nuevo") and not f.get("ocupado")]
        ocupadas = [f for f in elegidas if f.get("ocupado")]
        vinculadas = [f for f in elegidas if not f.get("nuevo")]
        self.btn_asociar.setEnabled(bool(nuevas) and not vinculadas and not ocupadas)
        self.btn_asociar.setText("ASOCIAR" if len(nuevas) <= 1 else f"ASOCIAR {len(nuevas)}")
        self.btn_sacar.setEnabled(bool(vinculadas) and not nuevas and not ocupadas)
        self.btn_sacar.setText("DESENLAZAR" if len(vinculadas) <= 1 else f"DESENLAZAR {len(vinculadas)}")
        if ocupadas and not nuevas and not vinculadas:
            self.lbl_estado.setText(
                f"Ya está con {ocupadas[0].get('ocupado')}. Desenlazalo antes de pasarlo a otro."
            )

    def _enter_busqueda(self):
        if len(self._visibles) != 1:
            return
        self.tabla.selectRow(0)
        self._accion_seleccion()

    def _accion_seleccion(self):
        elegidas = self._elegidas()
        if not elegidas:
            return
        if all(f.get("nuevo") and not f.get("ocupado") for f in elegidas):
            self._asociar_seleccion()
            return
        if all(not f.get("nuevo") for f in elegidas):
            self._desenlazar_seleccion()

    def _asociar_seleccion(self):
        from src.motor_abastecimiento import MotorAbastecimiento

        elegidas = [f for f in self._elegidas() if f.get("nuevo") and not f.get("ocupado")]
        if not elegidas:
            return
        if len(elegidas) == 1:
            nombre = elegidas[0].get("nombre") or elegidas[0].get("codigo") or "este producto"
            pregunta = f"¿Asociar {nombre} a {self._nombre}?"
        else:
            pregunta = f"¿Asociar {len(elegidas)} productos a {self._nombre}?"
        if QMessageBox.question(
            self, "Asociar", pregunta,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        hechos = []
        for fila in elegidas:
            ok = MotorAbastecimiento.vincular_proveedor(
                "producto_id",
                fila.get("criterio_valor"),
                self._nombre,
                self._ficha.get("telefono") or "",
                "",
                self._ficha.get("id") or None,
            )
            if ok:
                hechos.append(fila.get("codigo") or fila.get("nombre") or "producto")
        if not hechos:
            QMessageBox.warning(self, "No se pudo", "El producto no quedó asociado.")
            return
        if len(hechos) == 1:
            self.lbl_estado.setText(f"Quedó asociado a {self._nombre}.")
        else:
            self.lbl_estado.setText(f"Quedaron {len(hechos)} productos con {self._nombre}.")
        self._cargar()
        self._buscar_catalogo()
        self._avisar_pedidos()

    def _desenlazar_seleccion(self):
        from src.motor_abastecimiento.enlace.puente_proveedor import quitar_proveedor

        elegidas = self._elegidas()
        if not elegidas:
            return
        if len(elegidas) == 1:
            nombre = elegidas[0].get("nombre") or elegidas[0].get("codigo") or "este enlace"
            pregunta = f"¿Sacar {nombre} de {self._nombre}?"
        else:
            pregunta = f"¿Sacar {len(elegidas)} enlaces de {self._nombre}?"
        resp = QMessageBox.question(
            self,
            "Desenlazar",
            pregunta,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        hechos = []
        for fila in elegidas:
            if quitar_proveedor(fila.get("criterio_tipo"), fila.get("criterio_valor")):
                hechos.append(fila.get("nombre") or fila.get("codigo") or "enlace")
        if not hechos:
            QMessageBox.warning(self, "No se pudo", "El enlace sigue activo.")
            return
        if len(hechos) == 1:
            self.lbl_estado.setText(f"Salió {hechos[0]} de {self._nombre}.")
        else:
            self.lbl_estado.setText(f"Salieron {len(hechos)} enlaces de {self._nombre}.")
        self.buscar.blockSignals(True)
        self.buscar.clear()
        self.buscar.blockSignals(False)
        self._cargar()
        self._avisar_pedidos()

    def _avisar_pedidos(self):
        try:
            from PyQt6.QtWidgets import QApplication
            from src.proveedor_global.frontend.panel_pedidos_automaticos import PanelPedidosAutomaticos
        except Exception:
            return
        for ventana in QApplication.topLevelWidgets():
            for panel in ventana.findChildren(PanelPedidosAutomaticos):
                if hasattr(panel, "refrescar_datos"):
                    panel.refrescar_datos()


_QSS_DIA = (
    "QPushButton { background: white; color: #1E293B; border: 1px solid #CBD5E1; "
    "border-radius: 8px; font-weight: 700; padding: 6px 8px; }"
    "QPushButton:checked { background: #1D4ED8; color: white; border: none; }"
)


class DialogoEditarProveedor(QDialog):
    def __init__(self, ficha: dict, parent=None):
        super().__init__(parent)
        self.ficha = None
        self._origen = dict(ficha or {})
        self.setWindowTitle("Editar datos")
        self.setMinimumSize(420, 340)
        self.setStyleSheet("QDialog { background: white; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 16)
        lay.addWidget(QLabel("Nombre"))
        self.txt_nombre = QLineEdit(str(self._origen.get("nombre") or ""))
        lay.addWidget(self.txt_nombre)
        lay.addWidget(QLabel("Teléfono"))
        self.txt_telefono = QLineEdit(str(self._origen.get("telefono") or ""))
        self.txt_telefono.setPlaceholderText("Opcional")
        lay.addWidget(self.txt_telefono)
        lay.addWidget(QLabel("Días de reparto"))
        from src.proveedor_global.frontend.pedido.reparto import dias

        self._dias = []
        puestos = set(dias(self._origen.get("nombre")))
        fila_dias = QHBoxLayout()
        for indice, dia in enumerate(("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")):
            boton = QPushButton(dia)
            boton.setCheckable(True)
            boton.setFixedHeight(34)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setStyleSheet(_QSS_DIA)
            boton.setChecked(indice in puestos)
            self._dias.append(boton)
            fila_dias.addWidget(boton)
        lay.addLayout(fila_dias)
        botones = QHBoxLayout()
        botones.addStretch()
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        botones.addWidget(cancelar)
        guardar = QPushButton("Guardar")
        guardar.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: none; "
            "border-radius: 8px; padding: 8px 16px; font-weight: 700; }"
        )
        guardar.clicked.connect(self._guardar)
        botones.addWidget(guardar)
        lay.addLayout(botones)

    def _guardar(self):
        ok, resultado = FichaProveedor.actualizar(
            self._origen, self.txt_nombre.text(), self.txt_telefono.text(),
        )
        if not ok:
            QMessageBox.warning(self, "No se guardó", str(resultado))
            return
        from src.proveedor_global.frontend.pedido.reparto import guardar

        guardar(
            self.txt_nombre.text(),
            [i for i, boton in enumerate(self._dias) if boton.isChecked()],
        )
        self.ficha = resultado if isinstance(resultado, dict) else None
        self.accept()
