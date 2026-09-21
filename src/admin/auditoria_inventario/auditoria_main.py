from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit,
    QDialog, QComboBox, QAbstractItemView, QFrame, QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QBrush
from src.cerebro_global.auditoria.motor_conector_auditoria import obtener_conector_auditoria
from src.utils.theme_manager import theme_manager
from src.config import config


def _info_unidad(unidad="", departamento="", pesable=False):
    u = str(unidad or "").strip().upper()
    dep = str(departamento or "").lower()
    textil = u in ("MT", "M", "METRO", "METROS") or "textil" in dep or "tela" in dep
    if textil:
        return {
            "clave": "MT",
            "corto": "metros",
            "stock": "metros en sistema",
            "hint": "Medí los metros de tela (rollo o corte). Este número reemplaza el conteo.",
        }
    if pesable or u in ("KG", "KILO", "KILOS"):
        return {
            "clave": "KG",
            "corto": "kilos",
            "stock": "kilos en sistema",
            "hint": "Pesá el producto. Este número reemplaza el conteo.",
        }
    if u in ("LT", "L", "LITRO", "LITROS"):
        return {
            "clave": "LT",
            "corto": "litros",
            "stock": "litros en sistema",
            "hint": "Anotá los litros. Este número reemplaza el conteo.",
        }
    if u in ("CJ", "CAJA", "CAJAS"):
        return {
            "clave": "CJ",
            "corto": "cajas",
            "stock": "cajas en sistema",
            "hint": "Contá las cajas. Este número reemplaza el conteo.",
        }
    return {
        "clave": "UN",
        "corto": "unidades",
        "stock": "unidades en sistema",
        "hint": "Contá las unidades. Este número reemplaza el conteo.",
    }


class DialogoConteo(QDialog):
    """Teclado grande para cargar el conteo físico (TPV)."""

    def __init__(
        self,
        parent,
        nombre,
        codigo,
        stock_sist,
        conteo_actual,
        departamento="",
        unidad="",
        pesable=False,
        on_historial=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Conteo físico")
        self.setModal(True)
        self.setMinimumSize(520, 700)
        self._on_historial = on_historial
        info = _info_unidad(unidad, departamento, pesable)
        self._buffer = ""
        if conteo_actual not in ("", None):
            try:
                self._buffer = f"{float(conteo_actual):g}".replace(".", ",")
            except ValueError:
                self._buffer = ""
        self.setStyleSheet(
            "QDialog { background: #F8FAFC; }"
            "QLabel { color: #0F172A; }"
            "QPushButton { border: none; border-radius: 10px; font-weight: 800; }"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        card_l = QVBoxLayout(card)
        card_l.setSpacing(8)
        titulo = QLabel(nombre or "Producto")
        titulo.setStyleSheet("font-size: 22px; font-weight: 900;")
        titulo.setWordWrap(True)
        lbl_cod = QLabel(f"Código  {codigo or '—'}")
        lbl_cod.setStyleSheet("font-size: 15px; color: #334155;")
        lbl_dep = QLabel(f"Departamento  {departamento or '—'}")
        lbl_dep.setStyleSheet("font-size: 15px; color: #334155;")
        lbl_uni = QLabel(f"Unidad  {info['corto']}")
        lbl_uni.setStyleSheet("font-size: 15px; color: #334155;")
        lbl_stk = QLabel(f"Stock sistema  {stock_sist}  {info['corto']}")
        lbl_stk.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A; padding-top: 4px;")
        card_l.addWidget(titulo)
        card_l.addWidget(lbl_cod)
        card_l.addWidget(lbl_dep)
        card_l.addWidget(lbl_uni)
        card_l.addWidget(lbl_stk)
        root.addWidget(card)

        hint = QLabel(info["hint"])
        hint.setStyleSheet("font-size: 13px; color: #475569;")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.lbl_valor = QLabel("0")
        self.lbl_valor.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_valor.setStyleSheet(
            "background: #FFFFFF; border: 2px solid #2563EB; border-radius: 12px; "
            "padding: 16px 20px; font-size: 42px; font-weight: 900; color: #0F172A;"
        )
        self._sufijo = info["corto"]
        root.addWidget(self.lbl_valor)

        grid = QGridLayout()
        grid.setSpacing(8)
        teclas = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
            ("0", 3, 0), (",", 3, 1), ("⌫", 3, 2),
        ]
        for txt, r, c in teclas:
            b = QPushButton(txt)
            b.setMinimumHeight(64)
            if txt == "⌫":
                b.setStyleSheet("background: #FEE2E2; color: #991B1B; font-size: 22px;")
            else:
                b.setStyleSheet("background: #E2E8F0; color: #0F172A; font-size: 24px;")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, t=txt: self._tecla(t))
            grid.addWidget(b, r, c)
        root.addLayout(grid)

        acciones = QHBoxLayout()
        if on_historial:
            btn_h = QPushButton("Historial")
            btn_h.setMinimumHeight(48)
            btn_h.setStyleSheet("background: #3B82F6; color: white; font-size: 14px; padding: 0 16px;")
            btn_h.clicked.connect(on_historial)
            acciones.addWidget(btn_h)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setMinimumHeight(48)
        btn_cancel.setStyleSheet("background: #64748B; color: white; font-size: 14px; padding: 0 16px;")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Guardar conteo")
        btn_ok.setMinimumHeight(48)
        btn_ok.setStyleSheet("background: #10B981; color: white; font-size: 16px; padding: 0 22px;")
        btn_ok.clicked.connect(self.accept)
        acciones.addStretch()
        acciones.addWidget(btn_cancel)
        acciones.addWidget(btn_ok)
        root.addLayout(acciones)
        self._refrescar()

    def _tecla(self, t):
        if t == "⌫":
            self._buffer = self._buffer[:-1]
        elif t == ",":
            if "," not in self._buffer and "." not in self._buffer:
                self._buffer = (self._buffer or "0") + ","
        else:
            if self._buffer in ("0", ""):
                self._buffer = t
            else:
                self._buffer += t
        self._refrescar()

    def _refrescar(self):
        num = self._buffer if self._buffer != "" else "0"
        self.lbl_valor.setText(f"{num}  {self._sufijo}")

    def valor(self) -> float:
        raw = (self._buffer or "0").replace(",", ".")
        try:
            return max(0.0, float(raw))
        except ValueError:
            return 0.0


class AuditoriaMain(QWidget):
    COL_ID, COL_COD, COL_NOM, COL_DEP, COL_SIST, COL_REAL, COL_DIF = range(7)

    def __init__(self):
        super().__init__()
        self.conector_auditoria = obtener_conector_auditoria()
        self.user_role = self._rol_actual()
        self._vista = "todos"
        self.setup_ui()
        self.aplicar_permisos_perfil()
        self.cargar_datos()

    def showEvent(self, event):
        super().showEvent(event)
        self.aplicar_permisos_perfil()
        self._apply_theme()
        QTimer.singleShot(80, self.txt_buscar.setFocus)

    def _rol_actual(self):
        try:
            return str(getattr(config, "current_role", "") or "").lower()
        except Exception:
            return ""

    def _es_lectura(self):
        # Esta pantalla es de admin: solo el cajero queda en solo lectura.
        return self._rol_actual() == "cajero"

    def _apply_theme(self):
        is_dark = theme_manager.is_dark()
        bg = "#1E293B" if is_dark else "#FFFFFF"
        text = "#F8FAFC" if is_dark else "#0F172A"
        border = "#334155" if is_dark else "#E2E8F0"
        main_bg = "#0F172A" if is_dark else "#F8FAFC"
        self.setStyleSheet(f"background-color: {main_bg}; color: {text};")
        self.txt_buscar.setStyleSheet(
            f"padding: 10px; font-size: 14px; border: 1px solid {border}; "
            f"border-radius: 8px; background-color: {bg}; color: {text};"
        )
        header_style = (
            f"QHeaderView::section {{ background-color: {'#1E293B' if is_dark else '#F8FAFC'}; "
            f"color: {'#94A3B8' if is_dark else '#64748B'}; font-weight: bold; "
            f"border: 1px solid {border}; }}"
        )
        self.tabla.setStyleSheet(
            f"QTableWidget {{ background-color: {bg}; color: {text}; gridline-color: {border}; "
            f"font-size: 15px; border-radius: 8px; border: 1px solid {border}; }}"
            f"QTableWidget::item {{ padding: 6px; }}"
            f"{header_style}"
        )

    def aplicar_permisos_perfil(self):
        self.user_role = self._rol_actual()
        lectura = self._es_lectura()
        self.btn_aplicar.setEnabled(not lectura)
        self.btn_editar.setEnabled(not lectura)
        if lectura:
            self.btn_aplicar.setStyleSheet(
                "background: #64748B; color: #94A3B8; font-weight: bold; font-size: 16px; "
                "padding: 12px 24px; border-radius: 8px; border: none;"
            )
            self.btn_aplicar.setToolTip("El perfil cajero no puede aplicar ajustes de stock.")
        else:
            self.btn_aplicar.setStyleSheet(
                "background: #10B981; color: white; font-weight: bold; font-size: 16px; "
                "padding: 12px 24px; border-radius: 8px; border: none;"
            )
            self.btn_aplicar.setToolTip("")

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 25, 25, 25)
        root.setSpacing(12)

        nav = QHBoxLayout()
        btn_back = QPushButton("VOLVER AL PANEL")
        btn_back.setStyleSheet(
            "QPushButton { background: #64748B; color: white; padding: 10px 20px; "
            "border-radius: 8px; font-weight: bold; font-size: 12px; border: none; }"
            "QPushButton:hover { background: #475569; }"
        )
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self._volver)

        title = QLabel("AUDITORÍA DE STOCK")
        title.setStyleSheet("font-size: 18px; font-weight: 900; letter-spacing: 0.5px;")
        nav.addWidget(btn_back)
        nav.addSpacing(16)
        nav.addWidget(title)
        nav.addStretch()
        root.addLayout(nav)

        self.lbl_estado = QLabel("Listo para contar. Escaneá o escribí el código y Enter.")
        self.lbl_estado.setStyleSheet("color: #64748B; font-size: 13px;")
        root.addWidget(self.lbl_estado)

        kpis = QHBoxLayout()
        self.kpi_total = QLabel("0 SKU")
        self.kpi_contados = QLabel("0 contados")
        self.kpi_faltante = QLabel("Faltante 0")
        self.kpi_sobrante = QLabel("Sobrante 0")
        for w in (self.kpi_total, self.kpi_contados, self.kpi_faltante, self.kpi_sobrante):
            w.setStyleSheet(
                "background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; "
                "padding: 8px 14px; font-weight: 700; color: #0F172A;"
            )
            kpis.addWidget(w)
        kpis.addStretch()
        root.addLayout(kpis)

        filtro_lay = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Escanear código o filtrar por nombre / depto…")
        self.txt_buscar.textChanged.connect(self._aplicar_filtros)
        self.txt_buscar.returnPressed.connect(self._on_codigo_escaneado)

        self.cmb_vista = QComboBox()
        self.cmb_vista.addItem("Todos", "todos")
        self.cmb_vista.addItem("Solo contados", "contados")
        self.cmb_vista.addItem("Solo diferencias", "dif")
        self.cmb_vista.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cmb_vista.setMinimumWidth(160)
        self.cmb_vista.currentIndexChanged.connect(self._aplicar_filtros)

        btn_reload = QPushButton("Recargar stock")
        btn_reload.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reload.clicked.connect(lambda: self.cargar_datos(forzar=True))
        btn_reload.setStyleSheet(
            "padding: 8px 14px; border-radius: 8px; border: 1px solid #CBD5E1; font-weight: 600;"
        )

        filtro_lay.addWidget(QLabel("Contar:"))
        filtro_lay.addWidget(self.txt_buscar, 1)
        filtro_lay.addWidget(self.cmb_vista)
        filtro_lay.addWidget(btn_reload)
        root.addLayout(filtro_lay)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(
            ["ID", "Código", "Nombre", "Depto", "Stock sist.", "Conteo real", "Diferencia"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemChanged.connect(self._on_item_changed)
        self.tabla.cellDoubleClicked.connect(self._on_producto_doble_click)
        root.addWidget(self.tabla)

        bot_lay = QHBoxLayout()
        self.btn_editar = QPushButton("EDITAR CONTEO")
        self.btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_editar.setStyleSheet(
            "background: #3B82F6; color: white; font-weight: bold; font-size: 14px; "
            "padding: 12px 20px; border-radius: 8px; border: none;"
        )
        self.btn_editar.clicked.connect(self._editar_fila_seleccionada)

        self.btn_historial = QPushButton("HISTORIAL")
        self.btn_historial.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_historial.setStyleSheet(
            "background: #64748B; color: white; font-weight: bold; font-size: 14px; "
            "padding: 12px 20px; border-radius: 8px; border: none;"
        )
        self.btn_historial.clicked.connect(self._historial_fila_seleccionada)

        self.btn_aplicar = QPushButton("CONFIRMAR Y APLICAR AJUSTES")
        self.btn_aplicar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_aplicar.clicked.connect(self._aplicar_ajustes)
        bot_lay.addWidget(self.btn_editar)
        bot_lay.addWidget(self.btn_historial)
        bot_lay.addStretch()
        bot_lay.addWidget(self.btn_aplicar)
        root.addLayout(bot_lay)

    def _volver(self):
        w = self.window()
        if w and hasattr(w, "switch_tab"):
            w.switch_tab(0)
            return
        from PyQt6.QtWidgets import QApplication
        for widget in QApplication.instance().topLevelWidgets():
            if hasattr(widget, "switch_tab"):
                widget.switch_tab(0)
                break

    def _puede_editar(self):
        return not self._es_lectura()

    def _on_codigo_escaneado(self):
        if not self._puede_editar():
            self.lbl_estado.setText("Solo lectura: el cajero no puede cargar conteos.")
            return
        codigo = self.txt_buscar.text().strip()
        if not codigo:
            return

        row = self._buscar_fila(codigo)
        if row is None:
            self.lbl_estado.setText(f"No hay producto con código o ID «{codigo}».")
            self._aplicar_filtros()
            return

        id_item = self.tabla.item(row, self.COL_ID)
        depto = self.tabla.item(row, self.COL_DEP).text() if self.tabla.item(row, self.COL_DEP) else ""
        pesable = bool(id_item.data(Qt.ItemDataRole.UserRole + 1)) if id_item else False
        unidad = str(id_item.data(Qt.ItemDataRole.UserRole + 2) or "") if id_item else ""
        info = _info_unidad(unidad, depto, pesable)
        if info["clave"] in ("KG", "MT", "LT"):
            self._mostrar_dialogo_edicion(row)
        else:
            self._sumar_conteo(row, 1.0)
        self.txt_buscar.clear()
        self.tabla.selectRow(row)
        self.tabla.scrollToItem(self.tabla.item(row, 0))

    def _buscar_fila(self, codigo: str):
        codigo = codigo.strip()
        for i in range(self.tabla.rowCount()):
            item_cod = self.tabla.item(i, self.COL_COD)
            item_id = self.tabla.item(i, self.COL_ID)
            if item_cod and item_cod.text().strip() == codigo:
                return i
            if item_id and item_id.text().strip() == codigo:
                return i
        return None

    def _sumar_conteo(self, row, cantidad):
        item = self.tabla.item(row, self.COL_REAL)
        actual = 0.0
        txt = (item.text() or "").strip()
        if txt:
            try:
                actual = float(txt)
            except ValueError:
                actual = 0.0
        nuevo = actual + float(cantidad)
        item.setText(f"{nuevo:g}")
        nombre = self.tabla.item(row, self.COL_NOM).text()
        self.lbl_estado.setText(f"{nombre}: conteo {nuevo:g} (sumó {cantidad:g})")

    def _fila_seleccionada(self):
        row = self.tabla.currentRow()
        if row < 0:
            sel = self.tabla.selectedItems()
            if sel:
                row = sel[0].row()
        return row

    def _editar_fila_seleccionada(self):
        row = self._fila_seleccionada()
        if row < 0:
            QMessageBox.information(self, "Auditoría", "Seleccioná un producto de la lista.")
            return
        self._mostrar_dialogo_edicion(row)

    def _historial_fila_seleccionada(self):
        row = self._fila_seleccionada()
        if row < 0:
            QMessageBox.information(self, "Auditoría", "Seleccioná un producto de la lista.")
            return
        p_id = self.tabla.item(row, self.COL_ID).text()
        codigo = self.tabla.item(row, self.COL_COD).text()
        nombre = self.tabla.item(row, self.COL_NOM).text()
        self._ver_historial_ajustes(p_id, codigo, nombre)

    def _on_producto_doble_click(self, row, col=None):
        if row is None or row < 0:
            return
        self._mostrar_dialogo_edicion(row)

    def _mostrar_dialogo_edicion(self, row):
        if getattr(self, "_dialogo_abierto", False):
            return
        def _txt(col):
            it = self.tabla.item(row, col)
            return it.text() if it else ""

        codigo = _txt(self.COL_COD)
        nombre = _txt(self.COL_NOM)
        depto = _txt(self.COL_DEP)
        stock_sist = _txt(self.COL_SIST)
        conteo_actual = _txt(self.COL_REAL)
        p_id = _txt(self.COL_ID)
        if not nombre and not p_id:
            return

        id_item = self.tabla.item(row, self.COL_ID)
        pesable = bool(id_item.data(Qt.ItemDataRole.UserRole + 1)) if id_item else False
        unidad = str(id_item.data(Qt.ItemDataRole.UserRole + 2) or "") if id_item else ""
        dlg = DialogoConteo(
            self,
            nombre,
            codigo,
            stock_sist,
            conteo_actual,
            departamento=depto,
            unidad=unidad,
            pesable=pesable,
            on_historial=lambda: self._ver_historial_ajustes(p_id, codigo, nombre),
        )
        self._dialogo_abierto = True
        try:
            if dlg.exec() == QDialog.DialogCode.Accepted:
                item = self.tabla.item(row, self.COL_REAL)
                if item:
                    item.setText(f"{dlg.valor():g}")
        finally:
            self._dialogo_abierto = False

    def _ver_historial_ajustes(self, p_id, codigo, nombre):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Historial — {nombre}")
        dialog.setFixedSize(720, 420)
        dialog.setStyleSheet("QDialog { background-color: #F8FAFC; }")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"{nombre} ({codigo or p_id})"))
        tabla_hist = QTableWidget()
        tabla_hist.setColumnCount(6)
        tabla_hist.setHorizontalHeaderLabels(
            ["Fecha", "Usuario", "Stock ant.", "Stock nuevo", "Dif.", "Motivo"]
        )
        tabla_hist.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(tabla_hist)
        self._cargar_historial_producto(tabla_hist, p_id, codigo)
        btn_cerrar = QPushButton("CERRAR")
        btn_cerrar.clicked.connect(dialog.accept)
        layout.addWidget(btn_cerrar)
        dialog.exec()

    def _cargar_historial_producto(self, tabla, p_id, codigo):
        pid = None
        try:
            pid = int(p_id)
        except (TypeError, ValueError):
            pid = None
        filas = self.conector_auditoria.obtener_historial_ajustes(producto_id=pid, codigo=codigo)
        tabla.setRowCount(0)
        if not filas:
            tabla.insertRow(0)
            tabla.setItem(0, 0, QTableWidgetItem("Sin ajustes registrados"))
            return
        for i, r in enumerate(filas):
            tabla.insertRow(i)
            vals = [
                str(r.get("fecha") or ""),
                str(r.get("responsable") or ""),
                f"{float(r.get('stock_sistema') or 0):.3f}",
                f"{float(r.get('stock_fisico') or 0):.3f}",
                f"{float(r.get('diferencia') or 0):.3f}",
                str(r.get("motivo") or ""),
            ]
            for c, v in enumerate(vals):
                tabla.setItem(i, c, QTableWidgetItem(v))

    def cargar_datos(self, forzar=True):
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(0)
        productos = self.conector_auditoria.obtener_inventario_para_auditoria(
            forzar_actualizacion=forzar
        )
        lectura = self._es_lectura()
        is_dark = theme_manager.is_dark()
        for i, row in enumerate(productos):
            self.tabla.insertRow(i)
            p_id = str(row.get("id") or "")
            codigo = str(row.get("codigo") or "")
            nombre = str(row.get("nombre") or "")
            depto = str(row.get("departamento") or "GENERAL")
            stock = f"{float(row.get('stock') or 0.0):.3f}"
            for col, val in enumerate([p_id, codigo, nombre, depto, stock]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla.setItem(i, col, item)
            id_item = self.tabla.item(i, self.COL_ID)
            id_item.setData(Qt.ItemDataRole.UserRole + 1, bool(row.get("es_pesable")))
            id_item.setData(Qt.ItemDataRole.UserRole + 2, str(row.get("unidad") or "UN"))

            item_conteo = QTableWidgetItem("")
            if lectura:
                item_conteo.setFlags(item_conteo.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_conteo.setBackground(QColor("#E2E8F0" if not is_dark else "#334155"))
            else:
                item_conteo.setBackground(QColor("#FEF3C7" if not is_dark else "#7C2D12"))
            self.tabla.setItem(i, self.COL_REAL, item_conteo)

            item_dif = QTableWidgetItem("")
            item_dif.setFlags(item_dif.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.setItem(i, self.COL_DIF, item_dif)

        self.tabla.blockSignals(False)
        self._apply_theme()
        self._actualizar_kpis()
        self.lbl_estado.setText(f"{len(productos)} productos cargados. Escaneá para sumar al conteo.")

    def _aplicar_filtros(self, *_):
        t = self.txt_buscar.text().lower().strip()
        vista = self.cmb_vista.currentData() or "todos"
        for i in range(self.tabla.rowCount()):
            match_txt = True
            if t:
                match_txt = False
                for col in (self.COL_ID, self.COL_COD, self.COL_NOM, self.COL_DEP):
                    item = self.tabla.item(i, col)
                    if item and t in item.text().lower():
                        match_txt = True
                        break
            match_vista = True
            conteo = (self.tabla.item(i, self.COL_REAL).text() or "").strip()
            if vista == "contados":
                match_vista = bool(conteo)
            elif vista == "dif":
                try:
                    match_vista = abs(float(self.tabla.item(i, self.COL_DIF).text() or 0)) > 1e-9
                except ValueError:
                    match_vista = False
            self.tabla.setRowHidden(i, not (match_txt and match_vista))

    def _on_item_changed(self, item):
        if item.column() != self.COL_REAL:
            return
        row = item.row()
        str_val = item.text().strip()
        stock_sist_item = self.tabla.item(row, self.COL_SIST)
        dif_item = self.tabla.item(row, self.COL_DIF)
        is_dark = theme_manager.is_dark()
        if not str_val:
            dif_item.setText("")
            item.setBackground(QColor("#7C2D12" if is_dark else "#FEF3C7"))
            self._actualizar_kpis()
            return
        try:
            conteo = float(str_val)
            stock_sis = float(stock_sist_item.text())
            dif = conteo - stock_sis
            dif_item.setText(f"{dif:.3f}")
            if dif > 1e-9:
                dif_item.setForeground(QBrush(QColor("#1D4ED8")))
            elif dif < -1e-9:
                dif_item.setForeground(QBrush(QColor("#B91C1C")))
            else:
                dif_item.setForeground(QBrush(QColor("#0F172A")))
            item.setBackground(QColor("#FFFFFF" if not is_dark else "#1E293B"))
        except ValueError:
            pass
        self._actualizar_kpis()
        self._aplicar_filtros()

    def _actualizar_kpis(self):
        total = self.tabla.rowCount()
        contados = 0
        falt = 0.0
        sobr = 0.0
        for i in range(total):
            txt = (self.tabla.item(i, self.COL_REAL).text() or "").strip()
            if not txt:
                continue
            contados += 1
            try:
                dif = float(self.tabla.item(i, self.COL_DIF).text() or 0)
            except ValueError:
                dif = 0.0
            if dif < -1e-9:
                falt += -dif
            elif dif > 1e-9:
                sobr += dif
        self.kpi_total.setText(f"{total} SKU")
        self.kpi_contados.setText(f"{contados} contados")
        self.kpi_faltante.setText(f"Faltante {falt:g}")
        self.kpi_sobrante.setText(f"Sobrante {sobr:g}")

    def _recoger_ajustes(self):
        ajustes = []
        for i in range(self.tabla.rowCount()):
            conteo_item = self.tabla.item(i, self.COL_REAL)
            str_val = conteo_item.text().strip() if conteo_item else ""
            if not str_val:
                continue
            try:
                p_id = int(self.tabla.item(i, self.COL_ID).text())
                nombre = self.tabla.item(i, self.COL_NOM).text()
                stock_sis = float(self.tabla.item(i, self.COL_SIST).text())
                conteo = float(str_val)
                dif = conteo - stock_sis
                if abs(dif) < 1e-9:
                    continue
                ajustes.append({
                    "id": p_id,
                    "nombre": nombre,
                    "stock_sistema": stock_sis,
                    "stock_fisico": conteo,
                    "diferencia": dif,
                })
            except ValueError:
                continue
        return ajustes

    def _aplicar_ajustes(self):
        if self._es_lectura():
            QMessageBox.warning(
                self, "Acceso denegado",
                "Tu perfil no puede modificar stock.",
            )
            return

        ajustes = self._recoger_ajustes()
        if not ajustes:
            QMessageBox.information(self, "Auditoría", "No hay diferencias para aplicar.")
            return

        n = len(ajustes)
        falt = sum(-a["diferencia"] for a in ajustes if a["diferencia"] < 0)
        sobr = sum(a["diferencia"] for a in ajustes if a["diferencia"] > 0)
        reply = QMessageBox.question(
            self,
            "Confirmar ajustes",
            f"Se aplicará el conteo físico a {n} producto(s).\n"
            f"Faltante: {falt:g}  ·  Sobrante: {sobr:g}\n\n"
            "El stock del sistema quedará igual al conteo. ¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        u = config.current_user or {}
        usuario = u.get("nombre") or u.get("username") or u.get("usuario") or "Admin"
        ok, errores = self.conector_auditoria.aplicar_lote_ajustes(ajustes, usuario)
        self.cargar_datos(forzar=True)
        self.txt_buscar.clear()
        if ok:
            QMessageBox.information(self, "Éxito", "Inventario ajustado y registrado en el historial.")
        else:
            QMessageBox.warning(
                self, "Parcial",
                "Algunos ajustes no se aplicaron:\n\n" + "\n".join(errores[:20]),
            )
