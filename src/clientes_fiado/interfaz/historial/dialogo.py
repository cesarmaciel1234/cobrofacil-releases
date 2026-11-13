from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QSplitter,
                             QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QCursor, QBrush
from src.clientes_fiado.cerebro.cerebro import cerebro
from src.clientes_fiado.interfaz.historial.hilo import HiloMovimientos
from src.clientes_fiado.interfaz.historial.panel_ticket import PanelDetalleTicket
from src.clientes_fiado.interfaz.historial.tema import _CLI
from src.repositories.cliente_repository import FIADO_EXPRESS_LIMITE_DEFAULT
from src.utils.letra import vestir_id, vestir_nombre, vestir_numero


class DialogoAlcanceImpresionCuenta(QDialog):
    """
    Diálogo espacioso para seleccionar el alcance del comprobante de cuenta corriente:
    Solo deuda actual vs Historial completo. Elimina el recorte de textos de QMessageBox.
    """

    def __init__(self, parent, info, nombre_cliente=""):
        super().__init__(parent)
        self.setWindowTitle("Imprimir estado de cuenta")
        self.setFixedWidth(520)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self.resultado = None  # True: solo deuda actual, False: completo, None: cancelado

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        # Cabecera
        h_head = QHBoxLayout()
        lbl_icon = QLabel("🖨")
        lbl_icon.setStyleSheet("font-size: 26px; border: none; background: transparent;")
        h_head.addWidget(lbl_icon)

        v_tit = QVBoxLayout()
        v_tit.setSpacing(2)
        lbl_tit = QLabel("¿Qué movimientos querés imprimir?")
        lbl_tit.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; border: none; background: transparent;")
        nom_txt = f"Cliente: {nombre_cliente.upper()}" if nombre_cliente else "Seleccione el alcance del comprobante"
        lbl_sub = QLabel(nom_txt)
        lbl_sub.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600; border: none; background: transparent;")
        v_tit.addWidget(lbl_tit)
        v_tit.addWidget(lbl_sub)
        h_head.addLayout(v_tit)
        h_head.addStretch()
        lay.addLayout(h_head)

        # Caja de detalle explicativa
        caja_info = QFrame()
        caja_info.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;")
        lay_info = QVBoxLayout(caja_info)
        lay_info.setContentsMargins(14, 12, 14, 12)
        lay_info.setSpacing(6)

        cant_act = info.get("cant_actual", 0)
        cant_tot = info.get("cant_total", 0)
        lbl_desc1 = QLabel(f"• <b>Solo deuda actual:</b> últimos <b>{cant_act}</b> movimientos desde el último saldo $0.00.")
        lbl_desc1.setStyleSheet("font-size: 12px; color: #334155; border: none; background: transparent;")
        lbl_desc2 = QLabel(f"• <b>Historial completo:</b> <b>{cant_tot}</b> movimientos registrados en total.")
        lbl_desc2.setStyleSheet("font-size: 12px; color: #64748B; border: none; background: transparent;")
        lay_info.addWidget(lbl_desc1)
        lay_info.addWidget(lbl_desc2)
        lay.addWidget(caja_info)

        # Botones de acción verticales amplios (nunca recortan texto)
        btn_actual = QPushButton(f"📄 Imprimir Solo Deuda Actual ({cant_act} movimientos)")
        btn_actual.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_actual.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: 900; font-size: 13px; "
            "padding: 12px 16px; border-radius: 8px; border: none; } "
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_actual.clicked.connect(self._elegir_actual)
        lay.addWidget(btn_actual)

        btn_completo = QPushButton(f"📚 Imprimir Historial Completo ({cant_tot} movimientos)")
        btn_completo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_completo.setStyleSheet(
            "QPushButton { background: white; color: #0F172A; font-weight: 900; font-size: 13px; "
            "padding: 11px 16px; border-radius: 8px; border: 1px solid #CBD5E1; } "
            "QPushButton:hover { background: #F1F5F9; border-color: #94A3B8; }"
        )
        btn_completo.clicked.connect(self._elegir_completo)
        lay.addWidget(btn_completo)

        # Pie con Cancelar
        h_foot = QHBoxLayout()
        h_foot.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancelar.setStyleSheet(
            "QPushButton { background: transparent; color: #64748B; font-weight: 600; font-size: 12px; "
            "padding: 6px 14px; border: none; } "
            "QPushButton:hover { color: #0F172A; text-decoration: underline; }"
        )
        btn_cancelar.clicked.connect(self.reject)
        h_foot.addWidget(btn_cancelar)
        lay.addLayout(h_foot)

    def _elegir_actual(self):
        self.resultado = True
        self.accept()

    def _elegir_completo(self):
        self.resultado = False
        self.accept()


def imprimir_historial_dialogo(parent, cliente, movimientos, totales):
    """Elige alcance (solo deuda actual vs completo) si hay corte saldado e imprime."""
    if not movimientos:
        QMessageBox.information(parent, "Imprimir", "No hay movimientos para imprimir.")
        return
    try:
        from src.hardware.printer import printer_manager, resumen_corte_cuenta

        try:
            deuda = float(dict(cliente or {}).get("deuda_actual") or 0)
        except (TypeError, ValueError):
            deuda = 0.0

        info = resumen_corte_cuenta(movimientos, deuda)
        solo_deuda = False
        if info["tiene_corte"]:
            nom = str(dict(cliente or {}).get("nombre") or "")
            dlg_alcance = DialogoAlcanceImpresionCuenta(parent, info, nombre_cliente=nom)
            if qt_exec(dlg_alcance) != QDialog.DialogCode.Accepted or dlg_alcance.resultado is None:
                return
            solo_deuda = dlg_alcance.resultado

        ok = printer_manager.imprimir_historial_cuenta(
            cliente,
            movimientos,
            totales,
            solo_deuda_actual=solo_deuda,
        )
    except Exception as error:
        QMessageBox.warning(parent, "Imprimir", f"No se pudo imprimir el historial.\n{error}")
        return
    if ok:
        QMessageBox.information(parent, "Imprimir", "Estado de cuenta enviado a la tiketera.")
    else:
        QMessageBox.warning(
            parent,
            "Imprimir",
            "No se pudo enviar a la impresora. Revisá la tiketera en Configuración.",
        )


class DialogoHistorialCliente(QDialog):
    """Historial crudo completo (admin + cajero). Sin filtros de período."""

    def __init__(self, cliente_id, parent=None, modo="admin"):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self._modo = "cajero" if str(modo or "").strip().lower() == "cajero" else "admin"
        self.cliente = cerebro.obtener(cliente_id) or {}
        self._datos_editados = False
        self._hilo_mov = None
        self._todos_movs = []
        self._movimientos = []
        self._totales = {
            "cargos": 0.0, "abonos": 0.0, "borrados": 0.0,
            "cancelados": 0.0, "anulaciones": 0.0,
        }
        self.setWindowTitle("Historial del cliente")
        self.setMinimumSize(980, 720)
        self.resize(1080, 780)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._build()
        self._cargar_movimientos()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 14)
        lay.setSpacing(10)

        panel = QFrame()
        panel.setStyleSheet(
            f"QFrame {{ background: {_CLI['card']}; border: 1px solid {_CLI['border']}; border-radius: 14px; }}"
        )
        p_lay = QVBoxLayout(panel)
        p_lay.setContentsMargins(18, 14, 18, 14)
        p_lay.setSpacing(8)

        tit_row = QHBoxLayout()
        tit_row.setSpacing(8)
        self.lbl_tit = QLabel()
        self.lbl_tit.setStyleSheet("font-size: 16px; font-weight: 900; color: #1E293B; border: none;")
        tit_row.addWidget(self.lbl_tit, stretch=1)

        self.btn_edit = QPushButton("Editar")
        self.btn_edit.setFixedHeight(34)
        self.btn_edit.setMinimumWidth(72)
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.setToolTip("Editar ficha (nombre, DNI, teléfono, dirección)")
        self.btn_edit.setStyleSheet(
            "QPushButton { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; "
            "border-radius: 8px; font-size: 12px; font-weight: 900; padding: 0 12px; }"
            "QPushButton:hover { background: #FDE68A; border-color: #F59E0B; }"
        )
        self.btn_edit.clicked.connect(self._editar_cliente)
        tit_row.addWidget(self.btn_edit)

        self.btn_saldo = QPushButton("Saldo +")
        self.btn_saldo.setFixedHeight(34)
        self.btn_saldo.setMinimumWidth(78)
        self.btn_saldo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_saldo.setToolTip("Cargar saldo / cargo manual")
        self.btn_saldo.setStyleSheet(
            "QPushButton { background: #ECFDF5; color: #065F46; border: 1px solid #6EE7B7; "
            "border-radius: 8px; font-size: 12px; font-weight: 900; padding: 0 12px; }"
            "QPushButton:hover { background: #D1FAE5; border-color: #10B981; }"
        )
        self.btn_saldo.clicked.connect(self._cargar_saldo)
        tit_row.addWidget(self.btn_saldo)
        if self._modo == "cajero":
            self.btn_edit.hide()
            self.btn_saldo.hide()
        p_lay.addLayout(tit_row)

        # Una sola línea: números + contacto si hay
        self.lbl_meta = QLabel()
        self.lbl_meta.setWordWrap(False)
        self.lbl_meta.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {_CLI['text_sec']}; border: none;"
        )
        p_lay.addWidget(self.lbl_meta)
        self._actualizar_cabecera()

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Monto", "Saldo", "Descripción", "Ticket / cobro",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.horizontalHeader().setMinimumHeight(36)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.cellClicked.connect(self._abrir_detalle)
        self.tabla.currentCellChanged.connect(self._on_fila_cambiada)
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
        self.lbl_resumen.setStyleSheet(
            f"font-size: 12px; font-weight: 800; color: {_CLI['text_sec']}; border: none;"
        )
        p_lay.addWidget(self.lbl_resumen)

        lay.addWidget(panel)

        foot = QHBoxLayout()
        foot.setSpacing(8)
        self.btn_borrar = QPushButton("ELIMINAR")
        self.btn_borrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_borrar.setEnabled(False)
        self.btn_borrar.setToolTip(
            "Marca el cargo vivo como BORRADO y resta la deuda."
        )
        self.btn_borrar.setStyleSheet(
            "QPushButton { background: #FEE2E2; color: #991B1B; font-weight: 900; "
            "padding: 10px 16px; border-radius: 8px; border: 1px solid #FECACA; font-size: 12px; }"
            "QPushButton:hover { background: #FECACA; }"
            "QPushButton:disabled { background: #F1F5F9; color: #475569; border-color: #E2E8F0; }"
        )
        self.btn_borrar.clicked.connect(self._borrar_seleccion)
        foot.addWidget(self.btn_borrar)

        self.btn_imprimir = QPushButton("🖨 IMPRIMIR")
        self.btn_imprimir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_imprimir.setEnabled(False)
        self.btn_imprimir.setToolTip("Imprime el historial completo en la tiketera")
        self.btn_imprimir.setStyleSheet(
            "QPushButton { background: white; color: #0F172A; font-weight: 900; "
            "padding: 10px 16px; border-radius: 8px; border: 1px solid #CBD5E1; font-size: 12px; }"
            "QPushButton:hover { background: #F1F5F9; border-color: #94A3B8; }"
            "QPushButton:disabled { background: #F1F5F9; color: #475569; border-color: #E2E8F0; }"
        )
        self.btn_imprimir.clicked.connect(self._imprimir_historial)
        foot.addWidget(self.btn_imprimir)
        foot.addStretch()
        btn_cerrar = QPushButton("CERRAR")
        btn_cerrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cerrar.setStyleSheet(
            "QPushButton { background: #3B82F6; color: white; font-weight: 900; "
            "padding: 10px 22px; border-radius: 8px; border: none; font-size: 12px; }"
            "QPushButton:hover { background: #2563EB; }"
        )
        btn_cerrar.clicked.connect(self.accept)
        foot.addWidget(btn_cerrar)
        lay.addLayout(foot)

    def _actualizar_cabecera(self):
        nombre = dict(self.cliente).get("nombre", "—")
        dni = (dict(self.cliente).get("dni") or "").strip()
        tipo = (dict(self.cliente).get("tipo_cliente") or "regular").lower()
        tipo_txt = "Express" if tipo == "express" else "Regular"
        limite = float(dict(self.cliente).get("limite_credito") or 0)
        deuda = float(dict(self.cliente).get("deuda_actual") or 0)
        if tipo == "express" and limite <= 0:
            limite = FIADO_EXPRESS_LIMITE_DEFAULT
        disponible = float(cerebro.credito_disponible(self.cliente) or 0)
        telefono = (dict(self.cliente).get("telefono") or "").strip()

        if disponible < -0.009:
            disp_txt = f"Excedido ${abs(disponible):,.2f}"
        else:
            disp_txt = f"Disp ${disponible:,.2f}"

        dni_html = (
            f"DNI {dni}"
            if dni
            else "<span style='color:#64748B;'>Sin DNI</span>"
        )
        partes = [
            dni_html,
            tipo_txt,
            f"Lím ${limite:,.2f}",
            f"Deuda ${deuda:,.2f}",
            disp_txt,
        ]
        if telefono:
            partes.append(telefono)
        self.lbl_tit.setText(f"HISTORIAL — {nombre.upper()}")
        self.lbl_meta.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_meta.setText("  ·  ".join(partes))
        self.lbl_meta.setToolTip(
            "Editar completa DNI, teléfono y dirección" if not dni or not telefono else ""
        )

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
                self._hilo_mov.listo.disconnect(self._guardar_movimientos)
            except TypeError:
                pass
        self._hilo_mov = HiloMovimientosAdmin(self.cliente_id, self)
        self._hilo_mov.listo.connect(self._guardar_movimientos)
        self._hilo_mov.finished.connect(self._hilo_mov.deleteLater)
        self._hilo_mov.start()

    def _guardar_movimientos(self, movs, error: str):
        if error:
            self._todos_movs = []
            self.tabla.setRowCount(0)
            self._movimientos = []
            self.btn_imprimir.setEnabled(False)
            self.lbl_resumen.setText("No se pudo leer el historial. El cargo y el ticket no se modificaron.")
            return
        self._todos_movs = list(movs or [])
        self._pintar_movimientos(self._todos_movs)

    def _pintar_movimientos(self, movs):
        self.tabla.setRowCount(0)
        self._movimientos = []
        self._totales = {
            "cargos": 0.0, "abonos": 0.0, "borrados": 0.0,
            "cancelados": 0.0, "anulaciones": 0.0,
        }
        self.btn_imprimir.setEnabled(False)
        if not movs:
            self.lbl_resumen.setText("Sin movimientos.")
            self.panel_ticket.mensaje("Sin movimientos en la cuenta")
            self._actualizar_borrar()
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

            es_venta = bool(venta_id and str(venta_id) not in ("0", "None", ""))
            es_manual = (tipo == "CARGO" and not es_venta)

            it_tipo = vestir_nombre(QTableWidgetItem(etiqueta))
            if inactivo:
                it_tipo.setForeground(QColor(_CLI["muted_row"]))
            elif es_venta:
                it_tipo.setForeground(QColor("#DC2626"))  # Venta fiada
            elif es_manual:
                it_tipo.setForeground(QColor("#7C3AED"))  # Cargo manual a mano
                fuente_tipo = it_tipo.font()
                fuente_tipo.setBold(True)
                it_tipo.setFont(fuente_tipo)
            elif tipo == "ABONO":
                it_tipo.setForeground(QColor("#059669"))  # Cobro
            elif tipo == "ANULACION":
                it_tipo.setForeground(QColor("#334155"))
            self.tabla.setItem(row, 1, it_tipo)

            it_monto = vestir_numero(QTableWidgetItem(f"${monto:,.2f}"))
            if inactivo:
                it_monto.setForeground(QColor(_CLI["muted_row"]))
            elif es_venta:
                it_monto.setForeground(QColor("#DC2626"))
            elif es_manual:
                it_monto.setForeground(QColor("#7C3AED"))
            elif tipo == "ABONO":
                it_monto.setForeground(QColor("#059669"))
            elif tipo == "ANULACION":
                it_monto.setForeground(QColor("#334155"))
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

            if tipo == "ABONO":
                verde_cobro = QColor("#047857")
                bg_cobro = QBrush(QColor("#ECFDF5"))
                for col in range(6):
                    celda = self.tabla.item(row, col)
                    if celda:
                        celda.setForeground(verde_cobro)
                        celda.setBackground(bg_cobro)

            if inactivo:
                tachado = QFont()
                tachado.setStrikeOut(True)
                gris = QColor(_CLI["muted_row"])
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

        self._movimientos = list(movs)
        self._totales = {
            "cargos": total_cargos,
            "abonos": total_abonos,
            "borrados": total_borrados,
            "cancelados": total_cancelados,
            "anulaciones": total_anulaciones,
        }
        self.btn_imprimir.setEnabled(True)
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
        self._mostrar_detalle_fila(self._fila_elegida())

    def _imprimir_historial(self):
        imprimir_historial_dialogo(self, self.cliente, self._movimientos, self._totales)

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
        puede = self._puede_borrar(dato)
        self.btn_borrar.setEnabled(puede)
        if puede:
            self.btn_borrar.setText("ELIMINAR TICKET / DEUDA")
            self.btn_borrar.setToolTip(
                "Marca el cargo como BORRADO y resta la deuda. El renglón queda en el historial."
            )
        else:
            self.btn_borrar.setText("ELIMINAR TICKET / DEUDA")
            self.btn_borrar.setToolTip(
                "Elegí un cargo de fiado vivo. Un abono, una anulación o un BORRADO no se vuelven a eliminar."
            )

    def _on_fila_cambiada(self, fila_actual, _col_act, _fila_prev, _col_prev):
        self._actualizar_borrar()
        if fila_actual is not None and fila_actual >= 0:
            self._mostrar_detalle_fila(fila_actual)

    def _abrir_detalle(self, fila, _columna):
        self._mostrar_detalle_fila(fila)

    def _mostrar_detalle_fila(self, fila):
        if not hasattr(self, "panel_ticket"):
            return
        dato = self._dato_fila(fila)
        if not dato:
            self.panel_ticket.mensaje("Clic en una fila para ver el detalle")
            return
        ticket = str(dato.get("venta_id") or "").strip()
        tipo = str(dato.get("tipo") or "")
        if ticket and tipo in ("CARGO", "ANULACION"):
            self.panel_ticket.cargar(ticket)
            return
        if tipo == "ABONO":
            self.panel_ticket.mostrar_cobro(dato)
            return
        if dato.get("manual") or not ticket:
            self.panel_ticket.mostrar_cargo(dato)
            return
        self.panel_ticket.mensaje(str(dato.get("descripcion") or "Movimiento"))

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
            "Se resta el monto de la deuda. Si hay ticket de venta, queda CANCELADA "
            "(vuelve el stock y lo ve auditoría). El renglón sigue tachado en el historial."
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
                f"#{dato.get('venta_id')} BORRADO · deuda ${nuevo_saldo:,.2f}"
            )
        else:
            self.panel_ticket.mensaje(f"Cargo BORRADO · deuda ${nuevo_saldo:,.2f}")

