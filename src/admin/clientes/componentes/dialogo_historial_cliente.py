import re
from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QSplitter,
                             QAbstractItemView, QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QCursor, QBrush
from src.clientes_fiado.cerebro.cerebro import cerebro
from src.admin.clientes.consulta.hilo import HiloMovimientosAdmin, iniciar_hilo_seguro
from src.admin.clientes.componentes.dialogo_editar_cliente import DialogoEditarCliente, FIADO_EXPRESS_LIMITE_DEFAULT
from src.admin.clientes.componentes.dialogo_ticket import (
    PanelDetalleTicket,
    descripcion_cargo_visible,
)
from src.utils.letra import vestir_id, vestir_nombre, vestir_numero


from src.admin.clientes.theme import _CLI


class DialogoHistorialCliente(QDialog):
    """Historial crudo completo del cliente (cargos fiado + abonos). Sin filtros de período."""

    def __init__(self, cliente_id, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.cliente = cerebro.obtener(cliente_id) or {}
        self._datos_editados = False
        self._hilo_mov = None
        self._movs_pendientes_pintar = []
        self._indice_pintado = 0
        self._token_pintado = 0
        self._todos_movs = []
        self._movimientos = []
        self._totales = {
            "ventas": 0.0, "manuales": 0.0, "cobros": 0.0,
            "cargos": 0.0, "abonos": 0.0, "borrados": 0.0,
            "cancelados": 0.0, "anulaciones": 0.0,
        }
        self._error_interes = ""
        self.setWindowTitle("Historial del cliente")
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            width = max(1, min(1400, int(area.width() * 0.94)))
            height = max(1, min(920, int(area.height() * 0.90)))
            self.setMinimumSize(min(980, width), min(720, height))
            self.resize(width, height)
        else:
            self.setMinimumSize(980, 720)
            self.resize(1080, 780)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._build()
        self._timer_pintado = QTimer(self)
        self._timer_pintado.setSingleShot(True)
        self._timer_pintado.timeout.connect(self._pintar_siguiente_lote)
        self.finished.connect(self._cancelar_pintado)
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
        tit_row.setSpacing(10)

        self.btn_sidebar = QPushButton("☰")
        self.btn_sidebar.setCheckable(True)
        self.btn_sidebar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sidebar.setToolTip("Ver u ocultar panel de información del cliente")
        self.btn_sidebar.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #1E293B; font-size: 16px; font-weight: 900; "
            "border: 1px solid #CBD5E1; border-radius: 8px; min-width: 38px; max-width: 38px; min-height: 34px; max-height: 34px; }"
            "QPushButton:hover { background: #E2E8F0; border-color: #94A3B8; }"
            "QPushButton:checked { background: #2563EB; color: white; border-color: #1D4ED8; }"
        )
        self.btn_sidebar.clicked.connect(self._toggle_sidebar)
        tit_row.addWidget(self.btn_sidebar)

        self.lbl_tit = QLabel()
        self.lbl_tit.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_tit.setStyleSheet("border: none;")
        tit_row.addWidget(self.lbl_tit, stretch=1)
        p_lay.addLayout(tit_row)

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Monto", "Saldo", "Ticket / cobro", "Descripción",
            "Días", "Mantenimiento",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.horizontalHeader().setMinimumHeight(36)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.cellClicked.connect(self._abrir_detalle)
        self.tabla.cellDoubleClicked.connect(self._abrir_detalle)
        self.tabla.currentCellChanged.connect(self._on_fila_cambiada)
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0; border-radius: 10px;
                font-size: 13px; background: white; alternate-background-color: #F8FAFC;
                selection-background-color: #E0E7FF; selection-color: #1E1B4B;
            }
            QHeaderView::section {
                font-weight: 900; border: none; padding: 12px 8px;
                background: #F1F5F9; color: #334155; font-size: 11px;
            }
            QTableWidget::item { padding: 10px 8px; }
        """)
        self.tabla.itemSelectionChanged.connect(self._actualizar_borrar)

        self.panel_ticket = PanelDetalleTicket(self)
        self.panel_ticket.hide()

        bar_resumen = QHBoxLayout()
        bar_resumen.setContentsMargins(0, 4, 0, 0)
        bar_resumen.setSpacing(12)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {_CLI['text_sec']}; border: none;"
        )
        bar_resumen.addWidget(self.lbl_resumen, stretch=1)

        self.lbl_interes_badge = QLabel("")
        self.lbl_interes_badge.setStyleSheet(
            "background: #FEF3C7; color: #92400E; font-size: 13px; font-weight: 900; "
            "padding: 5px 12px; border-radius: 8px; border: 1px solid #FDE68A;"
        )
        self.lbl_interes_badge.hide()
        bar_resumen.addWidget(self.lbl_interes_badge)

        self.lbl_total_estimado = QLabel("")
        self.lbl_total_estimado.setStyleSheet(
            "background: #FEE2E2; color: #DC2626; font-size: 16px; font-weight: 900; "
            "padding: 6px 18px; border-radius: 8px; border: 2px solid #FECACA;"
        )
        self.lbl_total_estimado.hide()
        bar_resumen.addWidget(self.lbl_total_estimado)

        tabla_col = QVBoxLayout()
        tabla_col.setContentsMargins(0, 0, 0, 0)
        tabla_col.setSpacing(8)
        tabla_col.addWidget(self.tabla, stretch=1)
        tabla_col.addLayout(bar_resumen)

        # Sidebar lateral para información del cliente
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(290)
        self.sidebar.setStyleSheet(
            "QFrame#sidebar_cliente { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        self.sidebar.setObjectName("sidebar_cliente")
        s_lay = QVBoxLayout(self.sidebar)
        s_lay.setContentsMargins(14, 12, 14, 12)
        s_lay.setSpacing(10)

        s_hdr = QHBoxLayout()
        lbl_s_tit = QLabel("FICHA DEL CLIENTE")
        lbl_s_tit.setStyleSheet("font-size: 11px; font-weight: 900; color: #64748B; letter-spacing: 0.5px; border: none;")
        s_hdr.addWidget(lbl_s_tit, stretch=1)

        btn_s_close = QPushButton("✕")
        btn_s_close.setFixedSize(24, 24)
        btn_s_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_s_close.setStyleSheet(
            "QPushButton { background: transparent; color: #94A3B8; font-weight: 900; border: none; font-size: 13px; border-radius: 4px; }"
            "QPushButton:hover { background: #E2E8F0; color: #1E293B; }"
        )
        btn_s_close.clicked.connect(self._toggle_sidebar)
        s_hdr.addWidget(btn_s_close)
        s_lay.addLayout(s_hdr)

        # Botones de acción del cliente dentro del sidebar
        s_act_lay = QHBoxLayout()
        s_act_lay.setSpacing(8)

        btn_edit = QPushButton("Editar")
        btn_edit.setFixedHeight(34)
        btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_edit.setToolTip("Editar ficha (nombre, DNI, teléfono, dirección)")
        btn_edit.setStyleSheet(
            "QPushButton { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; "
            "border-radius: 8px; font-size: 12px; font-weight: 900; padding: 0 10px; }"
            "QPushButton:hover { background: #FDE68A; border-color: #F59E0B; }"
        )
        btn_edit.clicked.connect(self._editar_cliente)
        s_act_lay.addWidget(btn_edit, stretch=1)

        btn_saldo = QPushButton("Saldo +")
        btn_saldo.setFixedHeight(34)
        btn_saldo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_saldo.setToolTip("Cargar saldo / cargo manual")
        btn_saldo.setStyleSheet(
            "QPushButton { background: #ECFDF5; color: #065F46; border: 1px solid #6EE7B7; "
            "border-radius: 8px; font-size: 12px; font-weight: 900; padding: 0 10px; }"
            "QPushButton:hover { background: #D1FAE5; border-color: #10B981; }"
        )
        btn_saldo.clicked.connect(self._cargar_saldo)
        s_act_lay.addWidget(btn_saldo, stretch=1)
        s_lay.addLayout(s_act_lay)

        self.lbl_meta = QLabel()
        self.lbl_meta.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_meta.setWordWrap(True)
        self.lbl_meta.setStyleSheet("border: none;")
        s_lay.addWidget(self.lbl_meta)
        s_lay.addStretch(1)

        self.sidebar.hide()

        # Layout horizontal: Sidebar a la IZQUIERDA, Tabla y tickets a la derecha
        cuerpo = QHBoxLayout()
        cuerpo.setContentsMargins(0, 0, 0, 0)
        cuerpo.setSpacing(12)
        cuerpo.addWidget(self.sidebar)
        cuerpo.addLayout(tabla_col, stretch=1)
        p_lay.addLayout(cuerpo, stretch=1)

        self._actualizar_cabecera()

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

        self.btn_ver = QPushButton("🔍 VER DETALLE")
        self.btn_ver.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ver.setToolTip("Abre una ventana con el desglose del ticket, cobro o cargo seleccionado.")
        self.btn_ver.setStyleSheet(
            "QPushButton { background: white; color: #1E293B; font-weight: 900; "
            "padding: 10px 16px; border-radius: 8px; border: 1px solid #CBD5E1; font-size: 12px; }"
            "QPushButton:hover { background: #F1F5F9; border-color: #94A3B8; }"
        )
        self.btn_ver.clicked.connect(self._ver_detalle_seleccion)
        foot.addWidget(self.btn_ver)

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

    def _toggle_sidebar(self):
        visible = self.sidebar.isHidden()
        self.sidebar.setVisible(visible)
        self.btn_sidebar.setChecked(visible)

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
            color_disp = "#DC2626"
            bg_disp = "#FEF2F2"
        else:
            disp_txt = f"Disp ${disponible:,.2f}"
            color_disp = "#059669"
            bg_disp = "#ECFDF5"

        contacto = f"📞 {telefono}" if telefono else "Sin teléfono"
        mantenimiento = getattr(self, "_mantenimiento_acumulado", 0.0)
        total_estimado = getattr(self, "_total_estimado", deuda + mantenimiento)

        if total_estimado > 0.009:
            color_tot = "#DC2626"
            bg_tot = "#FEF2F2"
            lbl_tot = "TOTAL ESTIMADO"
        else:
            color_tot = "#059669"
            bg_tot = "#ECFDF5"
            lbl_tot = "AL DÍA"

        tipo_bg = "#EFF6FF" if tipo == "express" else "#F1F5F9"
        tipo_color = "#1D4ED8" if tipo == "express" else "#334155"

        self.lbl_tit.setText(
            f"<span style='font-size: 18px; font-weight: 900; color: #0F172A;'>👤 {nombre.upper()}</span>&nbsp;&nbsp;"
            f"<span style='background: {tipo_bg}; color: {tipo_color}; border: 1px solid #CBD5E1; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 6px;'>{tipo_txt}</span>"
        )

        self.lbl_meta.setText(
            f"<div style='line-height: 1.6; font-size: 12px; color: #475569;'>\n"
            f"<b style='color: #1E293B;'>DNI:</b> {dni or 'Sin DNI'}<br>\n"
            f"<b style='color: #1E293B;'>Teléfono:</b> {contacto}<br>\n"
            f"<b style='color: #1E293B;'>Categoría:</b> {tipo_txt}<br>\n"
            f"</div>\n"
            f"<div style='margin-top: 10px;'>\n"
            f"<div style='background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 10px; margin-bottom: 6px;'>\n"
            f"<span style='font-size: 10px; font-weight: 800; color: #64748B;'>LÍMITE ASIGNADO</span><br>\n"
            f"<span style='font-size: 14px; font-weight: 900; color: #0F172A;'>${limite:,.2f}</span>\n"
            f"</div>\n"
            f"<div style='background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 10px; margin-bottom: 6px;'>\n"
            f"<span style='font-size: 10px; font-weight: 800; color: #64748B;'>DEUDA CAPITAL</span><br>\n"
            f"<span style='font-size: 14px; font-weight: 900; color: #1E293B;'>${deuda:,.2f}</span>\n"
            f"</div>\n"
            f"<div style='background: #FEF3C7; border: 1px solid #FDE68A; border-radius: 8px; padding: 8px 10px; margin-bottom: 6px;'>\n"
            f"<span style='font-size: 10px; font-weight: 800; color: #92400E;'>MANTENIMIENTO (3%)</span><br>\n"
            f"<span style='font-size: 14px; font-weight: 900; color: #B45309;'>+${mantenimiento:,.2f}</span>\n"
            f"</div>\n"
            f"<div style='background: {bg_tot}; border: 1.5px solid #FECACA; border-radius: 8px; padding: 8px 10px; margin-bottom: 6px;'>\n"
            f"<span style='font-size: 10px; font-weight: 800; color: {color_tot};'>{lbl_tot}</span><br>\n"
            f"<span style='font-size: 15px; font-weight: 900; color: {color_tot};'>${total_estimado:,.2f}</span>\n"
            f"</div>\n"
            f"<div style='background: {bg_disp}; border: 1px solid #CBD5E1; border-radius: 8px; padding: 8px 10px;'>\n"
            f"<span style='font-size: 10px; font-weight: 800; color: {color_disp};'>DISPONIBILIDAD</span><br>\n"
            f"<span style='font-size: 14px; font-weight: 900; color: {color_disp};'>{disp_txt}</span>\n"
            f"</div>\n"
            f"</div>"
        )
        self.lbl_meta.setToolTip("Resumen ejecutivo de la cuenta corriente y disponibilidad de crédito.")

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
        from PyQt6.QtWidgets import QDoubleSpinBox, QLineEdit

        nombre = dict(self.cliente).get("nombre", "—")
        deuda = float(dict(self.cliente).get("deuda_actual") or 0)

        dlg = QDialog(self)
        dlg.setWindowTitle("Cargar saldo / ajuste manual")
        dlg.setModal(True)
        dlg.setMinimumWidth(460)
        dlg.setStyleSheet(f"QDialog {{ background: white; }} QLabel {{ color: {_CLI['text']}; border: none; }}")
        dl = QVBoxLayout(dlg)
        dl.setContentsMargins(22, 20, 22, 20)
        dl.setSpacing(12)

        lbl_head = QLabel(f"CARGO MANUAL · {nombre}")
        vestir_nombre(lbl_head, tam=15)
        lbl_head.setStyleSheet(f"color: {_CLI['text']}; font-weight: 900; border: none;")
        dl.addWidget(lbl_head)

        lbl_deuda = QLabel(f"Deuda actual: ${deuda:,.2f}")
        vestir_numero(lbl_deuda, tam=13)
        lbl_deuda.setStyleSheet(f"color: {_CLI['text_sec']}; border: none;")
        dl.addWidget(lbl_deuda)

        lbl_m = QLabel("Monto a cargar ($):")
        lbl_m.setStyleSheet("font-weight: 800; font-size: 13px;")
        dl.addWidget(lbl_m)
        sp_monto = QDoubleSpinBox()
        sp_monto.setRange(0.01, 99_999_999.00)
        sp_monto.setDecimals(2)
        sp_monto.setPrefix("$ ")
        sp_monto.setMinimumHeight(40)
        sp_monto.setStyleSheet(f"QDoubleSpinBox {{ padding: 6px 10px; border: 1px solid {_CLI['border']}; border-radius: 8px; font-size: 15px; font-weight: 800; }}")
        dl.addWidget(sp_monto)

        lbl_n = QLabel("Motivo / nota (se ve en el historial):")
        lbl_n.setStyleSheet("font-weight: 800; font-size: 13px;")
        dl.addWidget(lbl_n)
        txt_nota = QLineEdit()
        txt_nota.setText("Cargo manual desde panel Admin")
        txt_nota.setPlaceholderText("Ej: Ajuste por cobro duplicado COB-123")
        txt_nota.setMinimumHeight(40)
        txt_nota.selectAll()
        txt_nota.setStyleSheet(f"QLineEdit {{ padding: 8px 12px; border: 1px solid {_CLI['border']}; border-radius: 8px; font-size: 13px; }}")
        dl.addWidget(txt_nota)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("QPushButton { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; border-radius: 8px; padding: 9px 18px; font-weight: 800; }")
        btn_cancel.clicked.connect(dlg.reject)
        btn_ok = QPushButton("Cargar saldo")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(f"QPushButton {{ background: {_CLI['accent']}; color: white; border: none; border-radius: 8px; padding: 9px 20px; font-weight: 800; }}")
        btn_ok.clicked.connect(dlg.accept)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        dl.addLayout(btns)

        if not qt_exec(dlg):
            return
        monto = float(sp_monto.value())
        if monto <= 0:
            return
        motivo = txt_nota.text().strip() or "Cargo manual desde panel Admin"
        exito, nuevo_saldo, _nombre = cerebro.cargar_manual(
            self.cliente_id, monto, motivo
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
        self._cancelar_pintado()
        self.tabla.setRowCount(0)
        self.tabla.setEnabled(True)
        self.lbl_resumen.setText("Leyendo movimientos…")
        self._actualizar_borrar()
        if self._hilo_mov is not None:
            try:
                self._hilo_mov.listo.disconnect(self._guardar_movimientos)
            except (TypeError, RuntimeError):
                pass
        self._hilo_mov = HiloMovimientosAdmin(self.cliente_id)
        self._hilo_mov.listo.connect(self._guardar_movimientos)
        iniciar_hilo_seguro(self._hilo_mov)

    def _guardar_movimientos(self, movs, error: str):
        if error:
            self._todos_movs = []
            self.tabla.setRowCount(0)
            self._movimientos = []
            self.btn_imprimir.setEnabled(False)
            self.lbl_resumen.setText("No se pudo leer el historial. El cargo y el ticket no se modificaron.")
            return
        # Filtrar cualquier cargo plano de MANTENIMIENTO antiguo (el interés es dinámico por ticket)
        self._todos_movs = [
            m for m in (movs or [])
            if "MANTENIMIENTO" not in str(m.get("descripcion") or "").upper()
        ]
        self._error_interes = next(
            (str(dato.get("error_interes") or "") for dato in self._todos_movs
             if dato.get("error_interes")),
            "",
        )
        self._pintar_movimientos(self._todos_movs)

    def _pintar_movimientos(self, movs):
        self._cancelar_pintado()
        self.tabla.setRowCount(0)
        self.tabla.setEnabled(True)
        self._movimientos = []
        self._totales = {
            "ventas": 0.0, "manuales": 0.0, "cobros": 0.0,
            "cargos": 0.0, "abonos": 0.0, "borrados": 0.0,
            "cancelados": 0.0, "anulaciones": 0.0,
        }
        self.btn_imprimir.setEnabled(False)
        self._movs_pendientes_pintar = list(movs or [])
        self._indice_pintado = 0
        self._token_pintado += 1
        token = self._token_pintado
        if not self._movs_pendientes_pintar:
            self.tabla.setRowCount(0)
            self.lbl_resumen.setText("Sin movimientos.")
            self.panel_ticket.mensaje("Sin movimientos en la cuenta")
            self._actualizar_borrar()
            return

        self.tabla.setRowCount(len(self._movs_pendientes_pintar))
        self.tabla.setEnabled(False)
        self.tabla.setUpdatesEnabled(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tabla.verticalHeader().setDefaultSectionSize(46)
        self.tabla.setUpdatesEnabled(True)
        self.lbl_resumen.setText(
            f"Cargando historial… 0 de {len(self._movs_pendientes_pintar)} movimientos"
        )
        self._pintar_lote(token)

    def _pintar_lote(self, token):
        if token != self._token_pintado:
            return
        lote = self._movs_pendientes_pintar
        fin = min(self._indice_pintado + 100, len(lote))
        self.tabla.setUpdatesEnabled(False)
        try:
            for row in range(self._indice_pintado, fin):
                self._pintar_fila(row, lote[row])
        finally:
            self.tabla.setUpdatesEnabled(True)
        self._indice_pintado = fin
        if fin < len(lote):
            self.lbl_resumen.setText(
                f"Cargando historial… {fin} de {len(lote)} movimientos"
            )
            self._timer_pintado.start(1)
            return

        self._finalizar_pintado(lote)

    def _pintar_siguiente_lote(self):
        self._pintar_lote(self._token_pintado)

    def _pintar_fila(self, row, dato):
        self.tabla.setRowHeight(row, 46)
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

        es_venta = bool(venta_id and str(venta_id) not in ("0", "None", ""))
        es_manual = (tipo == "CARGO" and not es_venta)

        if es_venta and not inactivo:
            self._totales["ventas"] += monto
            self._totales["cargos"] += monto
        elif es_manual and not inactivo:
            self._totales["manuales"] += monto
            self._totales["cargos"] += monto
        elif tipo == "CARGO" and borrado:
            self._totales["borrados"] += monto
        elif tipo == "CARGO" and cancelado:
            self._totales["cancelados"] += monto
        elif tipo == "ABONO":
            self._totales["cobros"] += monto
            self._totales["abonos"] += monto
        elif tipo == "ANULACION":
            self._totales["anulaciones"] += monto

        it_fecha = vestir_nombre(QTableWidgetItem(fecha_txt))
        it_fecha.setData(Qt.ItemDataRole.UserRole, dato)
        self.tabla.setItem(row, 0, it_fecha)

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

        it_saldo = vestir_numero(QTableWidgetItem(f"${saldo:,.2f}"))
        self.tabla.setItem(row, 3, it_saldo)
        # Columna 4: Ticket / cobro
        it_ticket = vestir_id(QTableWidgetItem(ticket))
        if venta_id and tipo in ("CARGO", "ANULACION"):
            it_ticket.setForeground(QColor("#2563EB"))
            fuente = it_ticket.font()
            fuente.setUnderline(True)
            it_ticket.setFont(fuente)
            it_ticket.setToolTip("Pulse para ver el desglose de los artículos en una ventana")
            it_ticket.setData(Qt.ItemDataRole.UserRole, str(venta_id))
        elif tipo == "ABONO" and str(ticket).startswith("COB-"):
            it_ticket.setToolTip("Ticket de cobro. Es el mismo COB de la planilla, no una venta.")
        self.tabla.setItem(row, 4, it_ticket)

        # Columna 5: Descripción limpia, simple y armoniosa (sin alertas estridentes ni emojis)
        desc_lower = desc.lower()
        es_ticket = bool(venta_id) or (ticket and str(ticket).strip().startswith("#"))

        if es_ticket:
            tiene_alarma = (
                "excepci" in desc_lower
                or "pin" in desc_lower
                or "alerta" in desc_lower
                or "autoriz" in desc_lower
            )
            if tiene_alarma:
                m_exc = re.search(r'\((excepci[oó]n[^)]*)\)', desc, re.IGNORECASE)
                if m_exc:
                    txt_raw = m_exc.group(1).strip()
                    txt_alerta = f"{txt_raw[0].upper()}{txt_raw[1:]}"
                elif "pin" in desc_lower:
                    txt_alerta = "Excepción PIN"
                elif "excepci" in desc_lower:
                    txt_alerta = "Excepción admin"
                elif "autoriz" in desc_lower:
                    txt_alerta = "Autorización admin"
                else:
                    txt_alerta = desc
                it_desc = vestir_nombre(QTableWidgetItem(txt_alerta))
                it_desc.setForeground(QColor("#64748B"))  # Slate neutral sobrio y armonioso
                it_desc.setToolTip(f"Autorización / Excepción: {desc}")
            else:
                it_desc = vestir_nombre(QTableWidgetItem("—"))
                it_desc.setForeground(QColor("#94A3B8"))
                it_desc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_desc.setToolTip(f"Venta a crédito normal ({ticket})")
        elif tipo == "ABONO":
            m_metodo = re.search(r'\(([^)]+)\)', desc)
            txt_abono = m_metodo.group(1).strip() if m_metodo else (desc or "Abono a cuenta")
            # Quitar marcas técnicas internas
            txt_abono = re.sub(r':\s*F9\s*MANUAL', '', txt_abono, flags=re.IGNORECASE)
            txt_abono = re.sub(r'F9\s*MANUAL', 'Manual', txt_abono, flags=re.IGNORECASE).strip()
            if not txt_abono:
                txt_abono = "Abono a cuenta"
            it_desc = vestir_nombre(QTableWidgetItem(txt_abono))
            it_desc.setForeground(QColor("#475569"))  # Texto neutro legible y armonioso
            it_desc.setToolTip(desc)
        elif tipo == "ANULACION":
            it_desc = vestir_nombre(QTableWidgetItem(desc))
            it_desc.setForeground(QColor("#64748B"))
            it_desc.setToolTip(desc)
        else:
            desc_vis = descripcion_cargo_visible(desc)
            it_desc = vestir_nombre(QTableWidgetItem(desc_vis))
            it_desc.setForeground(QColor("#475569"))
            it_desc.setToolTip(desc)

        self.tabla.setItem(row, 5, it_desc)

        it_dias = vestir_numero(QTableWidgetItem("—"))
        it_dias.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it_interes = vestir_numero(QTableWidgetItem("—"))
        it_interes.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        if tipo == "CARGO" and not inactivo and not dato.get("es_interes"):
            acumulado = float(dato.get("interes_acumulado") or 0)
            dias_interes = int(dato.get("dias_interes") or 0)
            en_saldo = float(dato.get("interes_en_saldo") or 0)

            it_dias.setText(f"{dias_interes} d")
            if dias_interes > 30:
                it_dias.setForeground(QColor("#D97706"))
            it_dias.setToolTip(f"{dias_interes} días desde la compra o cargo.")

            it_interes.setText(f"${acumulado:,.2f}")
            if acumulado > 0:
                it_interes.setForeground(QColor("#B45309"))
            it_interes.setToolTip(
                f"Interés nuevo por aplicar: ${acumulado:,.2f}\n"
                f"Interés ya registrado en el saldo: ${en_saldo:,.2f}\n"
                "Tasa simple: 3% mensual prorrateada por día (+5% apalancamiento si >30d)."
            )
        elif dato.get("es_interes"):
            it_interes.setText("Asentado")
            it_interes.setToolTip(
                "Interés mensual asentado en una sola línea al registrar un abono."
            )

        self.tabla.setItem(row, 6, it_dias)
        self.tabla.setItem(row, 7, it_interes)

        if tipo == "ABONO":
            verde_cobro = QColor("#047857")
            bg_cobro = QBrush(QColor("#ECFDF5"))
            for item in (it_fecha, it_tipo, it_monto, it_saldo, it_ticket, it_desc, it_dias, it_interes):
                if item:
                    item.setBackground(bg_cobro)
            it_tipo.setForeground(verde_cobro)
            it_monto.setForeground(verde_cobro)

        if inactivo:
            tachado = QFont()
            tachado.setStrikeOut(True)
            gris = QColor(_CLI["muted_row"])
            for col in range(8):
                celda = self.tabla.item(row, col)
                if celda:
                    celda.setFont(tachado)
                    celda.setForeground(gris)
                    celda.setBackground(QBrush(QColor("#F8FAFC")))
            if cancelado:
                it_tipo.setToolTip("Ticket cancelado en F3. Queda en el historial de caja y en esta cuenta.")
            else:
                it_tipo.setToolTip("Quedó en el historial marcado como BORRADO. El ticket no se elimina.")

    def _finalizar_pintado(self, movs):
        for columna in (0, 1, 2, 3, 4, 6, 7):
            self.tabla.horizontalHeader().setSectionResizeMode(
                columna, QHeaderView.ResizeToContents
            )
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabla.setEnabled(True)
        self._movimientos = list(movs)
        self.btn_imprimir.setEnabled(True)
        total_ventas = self._totales["ventas"]
        total_manuales = self._totales["manuales"]
        total_cobros = self._totales["cobros"]
        total_borrados = self._totales["borrados"]
        total_cancelados = self._totales["cancelados"]
        total_anulaciones = self._totales["anulaciones"]

        partes = [f"{len(movs)} movimiento(s)"]
        if total_ventas > 0:
            partes.append(f"Ventas: ${total_ventas:,.2f}")
        if total_manuales > 0:
            partes.append(f"Cargos a mano: ${total_manuales:,.2f}")
        if total_cobros > 0:
            partes.append(f"Cobros: ${total_cobros:,.2f}")
        if total_ventas == 0 and total_manuales == 0 and total_cobros == 0:
            partes.append(f"Total fiado: ${self._totales['cargos']:,.2f}")
            partes.append(f"Total cobrado: ${self._totales['abonos']:,.2f}")
        if total_borrados:
            partes.append(f"Borrado: ${total_borrados:,.2f}")
        if total_cancelados:
            partes.append(f"Cancelado F3: ${total_cancelados:,.2f}")
        if total_anulaciones:
            partes.append(f"Anulado: ${total_anulaciones:,.2f}")
        resumen = "  ·  ".join(partes)
        if self._error_interes:
            resumen += "  ·  ERROR: no se pudo calcular el interés"
            self.lbl_resumen.setToolTip(self._error_interes)
            if hasattr(self, "lbl_interes_badge"):
                self.lbl_interes_badge.hide()
            if hasattr(self, "lbl_total_estimado"):
                self.lbl_total_estimado.hide()
        else:
            interes_nuevo = sum(
                float(dato.get("interes_acumulado") or 0)
                for dato in movs
                if dato.get("tipo") == "CARGO"
                and not dato.get("es_interes")
                and not dato.get("borrado")
                and not dato.get("cancelado")
            )
            try:
                ficha = cerebro.obtener(self.cliente_id) or self.cliente
                deuda_actual = float(ficha.get("deuda_actual") or 0)
                if deuda_actual <= 0.009:
                    interes_nuevo = 0.0
                    total_estimado = deuda_actual
                    if hasattr(self, "lbl_interes_badge"):
                        self.lbl_interes_badge.hide()
                    if hasattr(self, "lbl_total_estimado"):
                        if deuda_actual < -0.009:
                            self.lbl_total_estimado.setStyleSheet(
                                "background: #EFF6FF; color: #1D4ED8; font-size: 16px; font-weight: 900; "
                                "padding: 6px 18px; border-radius: 8px; border: 2px solid #BFDBFE;"
                            )
                            self.lbl_total_estimado.setText(f"A FAVOR: +${abs(deuda_actual):,.2f}")
                        else:
                            self.lbl_total_estimado.setStyleSheet(
                                "background: #ECFDF5; color: #047857; font-size: 16px; font-weight: 900; "
                                "padding: 6px 18px; border-radius: 8px; border: 2px solid #A7F3D0;"
                            )
                            self.lbl_total_estimado.setText("AL DÍA: $0.00")
                        self.lbl_total_estimado.show()
                else:
                    total_estimado = deuda_actual + interes_nuevo
                    if hasattr(self, "lbl_interes_badge"):
                        self.lbl_interes_badge.setText(f"Mantenimiento: +${interes_nuevo:,.2f}")
                        self.lbl_interes_badge.show()
                    if hasattr(self, "lbl_total_estimado"):
                        self.lbl_total_estimado.setStyleSheet(
                            "background: #FEF2F2; color: #DC2626; font-size: 16px; font-weight: 900; "
                            "padding: 6px 18px; border-radius: 8px; border: 2px solid #FECACA;"
                        )
                        self.lbl_total_estimado.setText(f"TOTAL ESTIMADO: ${total_estimado:,.2f}")
                        self.lbl_total_estimado.show()
                self.cliente = ficha
                self._mantenimiento_acumulado = interes_nuevo
                self._total_estimado = total_estimado
                self._actualizar_cabecera()

                # Detalle de mantenimiento y total estimado se muestran en sus badges destacados
                pass
            except Exception:
                from src.logger import logger

                logger.exception(
                    "[Historial clientes] No se pudo actualizar el total estimado del cliente %s",
                    self.cliente_id,
                )
                resumen += "  ·  No se pudo actualizar el total estimado"
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
        if hasattr(self, "panel_ticket"):
            dato_sel = self._dato_fila(self._fila_elegida())
            if dato_sel:
                t_sel = str(dato_sel.get("venta_id") or "").strip()
                if t_sel:
                    self.panel_ticket.cargar(t_sel)

    def _cancelar_pintado(self):
        self._token_pintado += 1
        if hasattr(self, "_timer_pintado"):
            self._timer_pintado.stop()
        self._movs_pendientes_pintar = []
        self._indice_pintado = 0

    def _imprimir_historial(self):
        if not self._movimientos:
            QMessageBox.information(self, "Imprimir", "No hay movimientos para imprimir.")
            return
        try:
            from src.hardware.printer import printer_manager

            ok = printer_manager.imprimir_historial_cuenta(
                self.cliente, self._movimientos, self._totales
            )
        except Exception as error:
            QMessageBox.warning(self, "Imprimir", f"No se pudo imprimir el historial.\n{error}")
            return
        if ok:
            QMessageBox.information(self, "Imprimir", "Historial enviado a la tiketera.")
        else:
            QMessageBox.warning(
                self,
                "Imprimir",
                "No se pudo enviar a la impresora. Revisá la tiketera en Configuración.",
            )

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
        return (
            bool(mov_id)
            and dato.get("tipo") == "CARGO"
            and not dato.get("es_interes")
            and not dato.get("borrado")
            and not dato.get("cancelado")
        )

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

    def _ver_detalle_seleccion(self):
        fila = self._fila_elegida()
        if fila >= 0:
            self._mostrar_detalle_fila(fila)
        else:
            QMessageBox.information(self, "Detalle", "Seleccioná un movimiento para ver su detalle.")

    def _mostrar_ticket(self, ticket):
        if hasattr(self, "panel_ticket"):
            self.panel_ticket.cargar(str(ticket))
        from src.admin.clientes.componentes.dialogo_ticket import abrir_detalle_ticket
        abrir_detalle_ticket(str(ticket), self)

    def _abrir_ticket(self, fila, columna):
        item = self.tabla.item(fila, 0)
        dato = item.data(Qt.ItemDataRole.UserRole) if item else {}
        if not isinstance(dato, dict):
            dato = {}
        ticket = str(dato.get("venta_id") or "").strip()
        item_ticket = self.tabla.item(fila, 4) or self.tabla.item(fila, 5)
        if not ticket and item_ticket:
            ticket = str(item_ticket.data(Qt.ItemDataRole.UserRole) or "").strip()
        if columna not in (4, 5) and not ticket and not dato.get("manual"):
            return
        if ticket:
            if hasattr(self, "_mostrar_ticket"):
                self._mostrar_ticket(str(ticket))
                return
            elif hasattr(self, "panel_ticket"):
                self.panel_ticket.cargar(str(ticket))
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

    def _abrir_detalle(self, fila, _columna):
        self._mostrar_detalle_fila(fila)

    def _mostrar_detalle_fila(self, fila):
        dato = self._dato_fila(fila)
        if not dato:
            return
        if hasattr(self, "panel_ticket"):
            ticket = str(dato.get("venta_id") or "").strip()
            tipo = str(dato.get("tipo") or "")
            if ticket and tipo in ("CARGO", "ANULACION"):
                self.panel_ticket.cargar(ticket)
            elif tipo == "ABONO":
                self.panel_ticket.mostrar_cobro(dato)
            elif dato.get("manual") or not ticket:
                self.panel_ticket.mostrar_cargo(dato)
        from src.admin.clientes.componentes.dialogo_ticket import abrir_detalle_ticket
        abrir_detalle_ticket(dato, self)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            fila = self._fila_elegida()
            if fila >= 0:
                self._mostrar_detalle_fila(fila)
                return
        super().keyPressEvent(event)

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
        if dato.get("es_interes"):
            QMessageBox.information(
                self, "Eliminar",
                "El interés asentado no se borra por separado. Al cancelar el ticket asociado, "
                "el sistema revierte su interés y deja la compensación en la cuenta.",
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
