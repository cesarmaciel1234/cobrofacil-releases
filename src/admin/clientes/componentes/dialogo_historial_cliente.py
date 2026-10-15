from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QSplitter,
                             QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QCursor, QBrush
from src.base_de_datos.database import db_manager
from src.clientes_fiado.cerebro.cerebro import cerebro
from src.admin.clientes.consulta.hilo import HiloMovimientosAdmin
from src.admin.clientes.componentes.dialogo_editar_cliente import DialogoEditarCliente, FIADO_EXPRESS_LIMITE_DEFAULT
from src.admin.clientes.componentes.dialogo_ticket import PanelDetalleTicket
from src.utils.letra import vestir_id, vestir_nombre, vestir_numero


from src.admin.clientes.theme import _CLI

class DialogoHistorialCliente(QDialog):
    """Historial de cuenta corriente del cliente (cargos fiado + abonos)."""

    def __init__(self, cliente_id, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.db = db_manager
        self.cliente = cerebro.obtener(cliente_id) or {}
        self._datos_editados = False
        self._hilo_mov = None
        self.setWindowTitle("Historial del cliente")
        self.setMinimumSize(980, 720)
        self.resize(1080, 780)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._build()
        self._cargar_movimientos()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 24)
        lay.setSpacing(16)

        panel = QFrame()
        panel.setStyleSheet(
            f"QFrame {{ background: {_CLI['card']}; border: 1px solid {_CLI['border']}; border-radius: 18px; }}"
        )
        p_lay = QVBoxLayout(panel)
        p_lay.setContentsMargins(28, 24, 28, 24)
        p_lay.setSpacing(12)

        tit_row = QHBoxLayout()
        self.lbl_tit = QLabel()
        self.lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E293B; border: none;")
        tit_row.addWidget(self.lbl_tit, stretch=1)

        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(44, 44)
        btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_edit.setToolTip("Editar nombre, teléfono, dirección y perfil")
        btn_edit.setStyleSheet(
            "QPushButton { background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 10px; "
            "font-size: 18px; }"
            "QPushButton:hover { background: #FDE68A; border-color: #F59E0B; }"
        )
        btn_edit.clicked.connect(self._editar_cliente)
        tit_row.addWidget(btn_edit)

        btn_saldo = QPushButton("✏️")
        btn_saldo.setFixedSize(44, 44)
        btn_saldo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_saldo.setToolTip("Cargar saldo manual")
        btn_saldo.setStyleSheet(
            "QPushButton { background: #ECFDF5; border: 1px solid #6EE7B7; border-radius: 10px; "
            "font-size: 18px; }"
            "QPushButton:hover { background: #D1FAE5; border-color: #10B981; }"
        )
        btn_saldo.clicked.connect(self._cargar_saldo)
        tit_row.addWidget(btn_saldo)
        p_lay.addLayout(tit_row)

        self.lbl_meta = QLabel()
        self.lbl_meta.setWordWrap(True)
        self.lbl_meta.setStyleSheet("font-size: 13px; color: #64748B; border: none;")
        p_lay.addWidget(self.lbl_meta)

        self.lbl_contacto = QLabel()
        self.lbl_contacto.setWordWrap(True)
        self.lbl_contacto.setStyleSheet("font-size: 12px; color: #94A3B8; border: none;")
        p_lay.addWidget(self.lbl_contacto)

        self._actualizar_cabecera()

        sub = QLabel("Movimientos de cuenta corriente (fiados y abonos), del más reciente al más antiguo.")
        sub.setStyleSheet("font-size: 12px; color: #94A3B8; border: none;")
        p_lay.addWidget(sub)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Monto", "Saldo", "Descripción", "Ticket / cobro",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(48)
        self.tabla.horizontalHeader().setMinimumHeight(44)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.cellClicked.connect(self._abrir_ticket)
        self.tabla.currentCellChanged.connect(lambda *_: self._actualizar_borrar())
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0; border-radius: 10px;
                font-size: 13px; background: white; alternate-background-color: #F8FAFC;
            }
            QHeaderView::section {
                font-weight: 900; border: none; padding: 12px 8px;
                background: #F1F5F9; color: #334155; font-size: 11px;
            }
            QTableWidget::item { padding: 10px 8px; }
        """)
        self.tabla.itemSelectionChanged.connect(self._actualizar_borrar)

        self.panel_ticket = PanelDetalleTicket(self)

        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.tabla)
        split.addWidget(self.panel_ticket)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        split.setChildrenCollapsible(False)
        p_lay.addWidget(split, stretch=1)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setStyleSheet("font-size: 13px; font-weight: 700; color: #475569; border: none;")
        p_lay.addWidget(self.lbl_resumen)

        lay.addWidget(panel)

        foot = QHBoxLayout()
        self.btn_borrar = QPushButton("ELIMINAR TICKET / DEUDA")
        self.btn_borrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_borrar.setEnabled(True)
        self.btn_borrar.setToolTip(
            "Elegí un cargo de fiado (no un abono). Marca BORRADO y resta la deuda. El renglón queda tachado."
        )
        self.btn_borrar.setStyleSheet(
            "QPushButton { background: #FEE2E2; color: #991B1B; font-weight: 900; "
            "padding: 12px 20px; border-radius: 8px; border: 1px solid #FECACA; font-size: 12px; }"
            "QPushButton:hover { background: #FECACA; }"
            "QPushButton:disabled { background: #F1F5F9; color: #94A3B8; border-color: #E2E8F0; }"
        )
        self.btn_borrar.clicked.connect(self._borrar_seleccion)
        foot.addWidget(self.btn_borrar)
        foot.addStretch()
        btn_cerrar = QPushButton("CERRAR")
        btn_cerrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cerrar.setStyleSheet(
            "QPushButton { background: #3B82F6; color: white; font-weight: 900; "
            "padding: 12px 28px; border-radius: 8px; border: none; font-size: 13px; }"
            "QPushButton:hover { background: #2563EB; }"
        )
        btn_cerrar.clicked.connect(self.accept)
        foot.addWidget(btn_cerrar)
        lay.addLayout(foot)

    def _actualizar_cabecera(self):
        nombre = dict(self.cliente).get("nombre", "—")
        dni = (dict(self.cliente).get("dni") or "").strip() or "—"
        tipo = (dict(self.cliente).get("tipo_cliente") or "regular").lower()
        tipo_txt = "⚡ Express" if tipo == "express" else "Regular"
        limite = float(dict(self.cliente).get("limite_credito") or 0)
        deuda = float(dict(self.cliente).get("deuda_actual") or 0)
        if tipo == "express" and limite <= 0:
            limite = FIADO_EXPRESS_LIMITE_DEFAULT
        disponible = cerebro.credito_disponible(self.cliente)
        telefono = (dict(self.cliente).get("telefono") or "").strip()
        direccion = (dict(self.cliente).get("direccion") or "").strip()

        self.lbl_tit.setText(f"📋  HISTORIAL — {nombre.upper()}")
        self.lbl_meta.setText(
            f"DNI: {dni}  ·  Tipo: {tipo_txt}  ·  "
            f"Límite: ${limite:,.2f}  ·  Deuda: ${deuda:,.2f}  ·  Disponible: ${disponible:,.2f}"
        )
        partes = []
        if telefono:
            partes.append(f"📞 {telefono}")
        if direccion:
            partes.append(f"📍 {direccion}")
        self.lbl_contacto.setText("  ·  ".join(partes) if partes else "Sin teléfono ni dirección — use ✏️ para completar")

    def _editar_cliente(self):
        dlg = DialogoEditarCliente(self.cliente_id, self)
        if qt_exec(dlg) == QDialog.DialogCode.Accepted:
            self._datos_editados = True
            self.cliente = cerebro.obtener(self.cliente_id) or {}
            self._actualizar_cabecera()
            parent = self.parent()
            if parent and hasattr(parent, "cargar_clientes"):
                parent.cargar_clientes()

    def _cargar_saldo(self):
        from PyQt6.QtWidgets import QInputDialog

        nombre = dict(self.cliente).get("nombre", "—")
        deuda = float(dict(self.cliente).get("deuda_actual") or 0)
        monto, ok = QInputDialog.getDouble(
            self,
            "Cargar saldo",
            f"Cliente: {nombre}\nDeuda actual: ${deuda:,.2f}\n\nMonto a cargar ($):",
            0,
            0,
            99_999_999,
            2,
        )
        if not ok or monto <= 0:
            return
        exito, nuevo_saldo, _nombre = cerebro.cargar_manual(
            self.cliente_id, monto, "Cargo manual desde panel Admin"
        )
        if not exito:
            QMessageBox.warning(self, "Saldo", "No se pudo cargar el saldo.")
            return
        self._datos_editados = True
        self.cliente = cerebro.obtener(self.cliente_id) or {}
        self._actualizar_cabecera()
        self._cargar_movimientos()
        parent = self.parent()
        if parent and hasattr(parent, "cargar_clientes"):
            parent.cargar_clientes()
        QMessageBox.information(self, "Saldo", f"Saldo cargado.\nNueva deuda: ${nuevo_saldo:,.2f}")

    def _cargar_movimientos(self):
        self.tabla.setRowCount(0)
        self.lbl_resumen.setText("Leyendo movimientos…")
        self._actualizar_borrar()
        if self._hilo_mov is not None:
            try:
                self._hilo_mov.listo.disconnect(self._pintar_movimientos)
            except TypeError:
                pass
        self._hilo_mov = HiloMovimientosAdmin(self.cliente_id, self)
        self._hilo_mov.listo.connect(self._pintar_movimientos)
        self._hilo_mov.finished.connect(self._hilo_mov.deleteLater)
        self._hilo_mov.start()

    def _pintar_movimientos(self, movs, error: str):
        self.tabla.setRowCount(0)
        if error:
            self.lbl_resumen.setText("No se pudo leer el historial. El cargo y el ticket no se modificaron.")
            return
        if not movs:
            self.lbl_resumen.setText("Sin movimientos registrados para este cliente.")
            return

        total_cargos = 0.0
        total_abonos = 0.0
        total_anulaciones = 0.0
        total_borrados = 0.0
        total_cancelados = 0.0
        for dato in movs:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setRowHeight(row, 48)

            fecha_txt = str(dato.get("fecha") or "").split(".")[0] or "—"
            tipo = dato.get("tipo") or ""
            monto = float(dato.get("monto") or 0)
            saldo = float(dato.get("saldo_resultante") or 0)
            desc = (dato.get("descripcion") or "—").strip()
            venta_id = dato.get("venta_id") or ""
            borrado = bool(dato.get("borrado"))
            cancelado = bool(dato.get("cancelado"))
            inactivo = borrado or cancelado
            ticket = dato.get("referencia") or "—"
            etiqueta = dato.get("etiqueta") or tipo

            if tipo == "CARGO" and not inactivo:
                total_cargos += monto
            elif tipo == "CARGO" and borrado:
                total_borrados += monto
            elif tipo == "CARGO" and cancelado:
                total_cancelados += monto
            elif tipo == "ABONO":
                total_abonos += monto
            elif tipo == "ANULACION":
                total_anulaciones += monto

            it_fecha = vestir_nombre(QTableWidgetItem(fecha_txt))
            it_fecha.setData(Qt.ItemDataRole.UserRole, dato)
            self.tabla.setItem(row, 0, it_fecha)

            it_tipo = vestir_nombre(QTableWidgetItem(etiqueta))
            if tipo == "CARGO" and inactivo:
                it_tipo.setForeground(QColor("#64748B"))
            elif tipo == "CARGO":
                it_tipo.setForeground(QColor("#DC2626"))
            elif tipo == "ABONO":
                it_tipo.setForeground(QColor("#059669"))
            elif tipo == "ANULACION":
                it_tipo.setForeground(QColor("#475569"))
            self.tabla.setItem(row, 1, it_tipo)

            it_monto = vestir_numero(QTableWidgetItem(f"${monto:,.2f}"))
            if tipo == "CARGO" and inactivo:
                it_monto.setForeground(QColor("#64748B"))
            elif tipo == "CARGO":
                it_monto.setForeground(QColor("#DC2626"))
            elif tipo == "ABONO":
                it_monto.setForeground(QColor("#059669"))
            elif tipo == "ANULACION":
                it_monto.setForeground(QColor("#475569"))
            self.tabla.setItem(row, 2, it_monto)

            self.tabla.setItem(row, 3, vestir_numero(QTableWidgetItem(f"${saldo:,.2f}")))
            self.tabla.setItem(row, 4, vestir_nombre(QTableWidgetItem(desc)))
            it_ticket = vestir_id(QTableWidgetItem(ticket))
            if venta_id and tipo in ("CARGO", "ANULACION"):
                it_ticket.setForeground(QColor("#2563EB"))
                fuente = it_ticket.font()
                fuente.setUnderline(True)
                it_ticket.setFont(fuente)
                it_ticket.setToolTip("Pulse para ver los artículos aquí, sin abrir otra ventana")
                it_ticket.setData(Qt.ItemDataRole.UserRole, str(venta_id))
            elif tipo == "ABONO" and str(ticket).startswith("COB-"):
                it_ticket.setToolTip("Ticket de cobro. Es el mismo COB de la planilla, no una venta.")
            self.tabla.setItem(row, 5, it_ticket)

            if inactivo:
                tachado = QFont()
                tachado.setStrikeOut(True)
                gris = QColor("#94A3B8")
                for col in range(6):
                    celda = self.tabla.item(row, col)
                    if not celda:
                        continue
                    celda.setFont(tachado)
                    celda.setForeground(gris)
                    celda.setBackground(QBrush(QColor("#F8FAFC")))
                if cancelado:
                    it_tipo.setToolTip("Ticket cancelado en F3. Queda en el historial de caja y en esta cuenta.")
                else:
                    it_tipo.setToolTip("Quedó en el historial marcado como BORRADO. El ticket no se elimina.")

        resumen = (
            f"{len(movs)} movimiento(s)  ·  "
            f"Total fiado: ${total_cargos:,.2f}  ·  "
            f"Total abonado: ${total_abonos:,.2f}"
        )
        if total_borrados:
            resumen += f"  ·  Borrado: ${total_borrados:,.2f}"
        if total_cancelados:
            resumen += f"  ·  Cancelado F3: ${total_cancelados:,.2f}"
        if total_anulaciones:
            resumen += f"  ·  Anulado: ${total_anulaciones:,.2f}"
        self.lbl_resumen.setText(resumen)
        viva = -1
        for r in range(self.tabla.rowCount()):
            if self._puede_borrar(self._dato_fila(r)):
                viva = r
                break
        if viva >= 0:
            self.tabla.selectRow(viva)
            self.tabla.setCurrentCell(viva, 0)
        elif self.tabla.rowCount():
            self.tabla.selectRow(0)
            self.tabla.setCurrentCell(0, 0)
        self._actualizar_borrar()

    def _dato_fila(self, fila):
        if fila is None or fila < 0:
            return {}
        item = self.tabla.item(fila, 0)
        if not item:
            return {}
        dato = item.data(Qt.ItemDataRole.UserRole)
        return dato if isinstance(dato, dict) else {}

    def _fila_elegida(self):
        fila = self.tabla.currentRow()
        if fila >= 0:
            return fila
        sel = self.tabla.selectionModel()
        if sel and sel.selectedIndexes():
            return sel.selectedIndexes()[0].row()
        return -1

    def _puede_borrar(self, dato):
        if not isinstance(dato, dict):
            return False
        try:
            mov_id = int(dato.get("id") or 0)
        except (TypeError, ValueError):
            mov_id = 0
        return bool(mov_id) and dato.get("tipo") == "CARGO" and not dato.get("borrado") and not dato.get("cancelado")

    def _actualizar_borrar(self):
        dato = self._dato_fila(self._fila_elegida())
        if self._puede_borrar(dato):
            self.btn_borrar.setText("ELIMINAR TICKET / DEUDA")
            self.btn_borrar.setToolTip("Marca el cargo como BORRADO y resta la deuda. El renglón queda en el historial.")
        else:
            self.btn_borrar.setText("ELIMINAR TICKET / DEUDA")
            self.btn_borrar.setToolTip("Elegí un cargo de fiado vivo. Un abono, una anulación o un BORRADO no se vuelven a eliminar.")

    def _mostrar_ticket(self, ticket):
        self.panel_ticket.cargar(str(ticket))

    def _abrir_ticket(self, fila, columna):
        item = self.tabla.item(fila, 0)
        dato = item.data(Qt.ItemDataRole.UserRole) if item else {}
        if not isinstance(dato, dict):
            dato = {}
        ticket = dato.get("venta_id") or ""
        item_ticket = self.tabla.item(fila, 5)
        if not ticket and item_ticket:
            ticket = item_ticket.data(Qt.ItemDataRole.UserRole) or ""
        if columna != 5 and not ticket and not dato.get("manual"):
            return
        if ticket:
            self._mostrar_ticket(str(ticket))
            return
        if not hasattr(self, "panel_ticket"):
            return
        if dato.get("manual"):
            self.panel_ticket.mensaje(
                "Cargo manual: no hay ticket de venta. El registro queda en el historial "
                "aunque se marque BORRADO."
            )
            return
        if dato.get("tipo") == "ABONO":
            self.panel_ticket.mensaje(
                "Este renglón es un cobro (COB). Los artículos están en el ticket de venta del cargo."
            )

    def _borrar_seleccion(self):
        dato = self._dato_fila(self._fila_elegida())
        tipo = str(dato.get("tipo") or "")
        if not dato:
            QMessageBox.information(
                self, "Eliminar",
                "Elegí un cargo de fiado en la lista (rojo). Un abono o una anulación no se eliminan acá.",
            )
            return
        if tipo == "ABONO":
            QMessageBox.information(
                self, "Eliminar",
                "Ese renglón es un cobro (COB). No se elimina desde el historial.",
            )
            return
        if tipo == "ANULACION":
            QMessageBox.information(
                self, "Eliminar",
                "Esa fila es la anulación. El cargo ya está tachado arriba o al lado.",
            )
            return
        if dato.get("borrado"):
            QMessageBox.information(
                self, "Eliminar",
                "Ese ticket ya está marcado BORRADO. Queda en el historial tachado.",
            )
            return
        if dato.get("cancelado"):
            QMessageBox.information(
                self, "Eliminar",
                "Ese ticket se canceló en F3. Queda en el historial.",
            )
            return
        if not self._puede_borrar(dato):
            QMessageBox.information(
                self, "Eliminar",
                "Elegí un cargo de fiado vivo para marcarlo BORRADO.",
            )
            return
        que = f"ticket #{dato.get('venta_id')}" if dato.get("venta_id") else "cargo manual"
        aviso = QMessageBox(self)
        aviso.setIcon(QMessageBox.Icon.Warning)
        aviso.setWindowTitle("Marcar como BORRADO")
        aviso.setText(
            f"¿Marcar este {que} como BORRADO?\n\n"
            "El cargo y el número de ticket siguen en el historial, claramente tachados. "
            "No se borra el registro. Se resta el monto de la deuda."
        )
        aviso.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        aviso.setDefaultButton(QMessageBox.StandardButton.No)
        if qt_exec(aviso) != QMessageBox.StandardButton.Yes:
            return
        exito, nuevo_saldo, detalle = cerebro.borrar_cargo(dato.get("id"), self.cliente_id)
        if not exito:
            QMessageBox.warning(self, "Borrar", detalle or "No se pudo marcar el cargo.")
            return
        self._datos_editados = True
        self.cliente = cerebro.obtener(self.cliente_id) or {}
        self._actualizar_cabecera()
        self._cargar_movimientos()
        parent = self.parent()
        if parent and hasattr(parent, "cargar_clientes"):
            parent.cargar_clientes()
        if dato.get("venta_id"):
            self.panel_ticket.mensaje(
                f"Ticket #{dato.get('venta_id')} marcado BORRADO. Sigue visible. "
                f"Nueva deuda: ${nuevo_saldo:,.2f}"
            )
        else:
            self.panel_ticket.mensaje(
                f"Cargo manual marcado BORRADO. Sigue visible. Nueva deuda: ${nuevo_saldo:,.2f}"
            )

