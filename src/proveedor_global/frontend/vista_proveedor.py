from src.utils.qt_compat import qt_exec
import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Utilidades visuales importadas desde el módulo del Jefe
from src.contabilidad.shared_globals import (
    section_title, date_field, input_field, build_table,
    btn_primary, btn_ghost, PAL
)

from src.proveedor_global.backend.ficha import FichaProveedor, etiqueta, nombre_de_eleccion
from src.proveedor_global.backend.motor_proveedor import MotorProveedor
from src.proveedor_global.frontend.panel_pedidos_automaticos import (
    DialogoAltaProveedor, PanelPedidosAutomaticos,
)
from src.proveedor_global.backend.moneda import leer, texto
from src.proveedor_global.frontend.panel_recepcion_rapida import PanelRecepcionRapida, plata
from src.utils.letra import vestir_id, vestir_nombre, vestir_numero


def _dia(fecha) -> str:
    texto = str(fecha or "").strip()
    base = texto[:10]
    partes = base.split("-")
    if len(partes) == 3 and len(partes[0]) == 4:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return base or texto

class VistaProveedor(QWidget):
    """
    Vista unificada de Proveedores (Romaneo y Compras Rǭpidas).
    """
    request_dashboard = pyqtSignal()
    def __init__(self, parent=None, perfil="admin", db_jefe=None):
        super().__init__(parent)
        self.perfil = perfil.lower()
        self._db_jefe = db_jefe
        try:
            from src.motor_inventario.planilla.orquestador import MotorPlanilla

            MotorPlanilla.arrancar()
        except Exception:
            pass

        # Layout principal
        lay = QVBoxLayout(self)
        if self.perfil != "contabilidad":
            lay.setContentsMargins(24, 24, 24, 24)
            self.setStyleSheet("background: #F8FAFC;")
        else:
            lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)

        self.lay_container = lay

        if self.perfil != "contabilidad":
            nav = QFrame()
            nav.setFixedHeight(50)
            nav.setStyleSheet("background: transparent; border-bottom: 1px solid #E2E8F0;")
            n_lay = QHBoxLayout(nav)
            n_lay.setContentsMargins(0, 0, 0, 0)
            btn_volver = QPushButton("← Volver")
            btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_volver.setFixedHeight(34)
            btn_volver.setStyleSheet("""
                QPushButton {
                    background: #F8FAFC; color: #475569;
                    border: 1px solid #E2E8F0; border-radius: 8px;
                    padding: 0 16px; font-weight: 700; font-size: 12px;
                }
                QPushButton:hover { background: #CBD5E1; color: #0F172A; }
            """)
            btn_volver.clicked.connect(self.request_dashboard.emit)
            n_lay.addWidget(btn_volver)
            n_lay.addStretch()
            lay.addWidget(nav)

        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        lay = self.lay_container
        lay.addWidget(section_title("🚚  Proveedores y Abastecimiento"))

        # ── SELECTOR DE PESTAÑAS PRINCIPAL ────────────────────────────────────
        tab_box = QHBoxLayout()
        tab_box.setSpacing(10)

        self.btn_tab_pedidos = QPushButton("📦 1. Pedidos Faltantes")
        self.btn_tab_pedidos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_pedidos.setFixedHeight(38)

        self.btn_tab_recepcion = QPushButton("⚡ 2. Recepción Rápida (Escáner)")
        self.btn_tab_recepcion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_recepcion.setFixedHeight(38)

        self.btn_tab_carga = QPushButton("🥩 3. Romaneo y Frigorífico")
        self.btn_tab_carga.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_carga.setFixedHeight(38)

        self.btn_tab_pedidos.clicked.connect(lambda: self._switch_tab(0))
        self.btn_tab_recepcion.clicked.connect(lambda: self._switch_tab(1))
        self.btn_tab_carga.clicked.connect(lambda: self._switch_tab(2))

        tab_box.addWidget(self.btn_tab_pedidos)
        tab_box.addWidget(self.btn_tab_recepcion)
        tab_box.addWidget(self.btn_tab_carga)
        tab_box.addStretch()
        lay.addLayout(tab_box)

        # ── CONTENEDOR MULTI-PESTAÑA ──────────────────────────────────────────
        self.stack = QStackedWidget()

        # Pestaña 1: Motor Autónomo de Pedidos
        self.panel_pedidos = PanelPedidosAutomaticos(self)
        self.stack.addWidget(self.panel_pedidos)

        # Pestaña 2: Recepción Rápida por Escáner
        self.panel_recepcion = PanelRecepcionRapida(self, perfil=self.perfil)
        self.panel_recepcion.compra_guardada.connect(self.cargar_datos)
        self.stack.addWidget(self.panel_recepcion)

        # Pestaña 3: Carga de Compras / Romaneo Tradicional
        self.widget_carga = QWidget()
        lay_carga = QVBoxLayout(self.widget_carga)
        lay_carga.setContentsMargins(0, 0, 0, 0)
        lay_carga.setSpacing(16)

        self._lbl_estado_red = QLabel("")
        self._lbl_estado_red.setWordWrap(True)
        self._lbl_estado_red.setStyleSheet(
            f"QLabel {{ background: {PAL['surface']}; color: {PAL['text']}; "
            f"border: 1px solid {PAL['border']}; border-radius: 8px; padding: 9px 12px; "
            "font-weight: 700; }}"
        )
        self._lbl_estado_red.hide()
        lay_carga.addWidget(self._lbl_estado_red)

        main_h = QHBoxLayout()
        main_h.setSpacing(20)

        left_panel = QFrame()
        self._panel_carga = left_panel
        left_panel.setObjectName("Card")
        left_panel.setStyleSheet(f"""
            QFrame#Card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PAL['surface']}, stop:1 #F8FAFC);
                border: 1px solid {PAL['border']};
                border-radius: 16px;
            }}
        """)
        fl = QGridLayout(left_panel)
        fl.setContentsMargins(25, 25, 25, 25); fl.setSpacing(15)

        title_lbl = QLabel("🧾 DATOS DEL REMITO")
        title_lbl.setStyleSheet(f"QLabel {{ color: {PAL['primary']}; font-weight: 900; font-size: 14px; letter-spacing: 1px; }}")
        fl.addWidget(title_lbl, 0, 0, 1, 4)

        lbl_fecha = QLabel("Fecha:")
        lbl_fecha.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_fecha, 1, 0)
        self._prov_date = date_field(); fl.addWidget(self._prov_date, 1, 1)

        lbl_prov = QLabel("Proveedor:")
        lbl_prov.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_prov, 1, 2)

        self._prov_nombre = QComboBox()
        self._prov_nombre.setEditable(True)
        self._prov_nombre.setPlaceholderText("Ej: Frigorífico Rioplatense")
        self._prov_nombre.setStyleSheet(f"QComboBox {{ background: white; border: 1px solid {PAL['border']}; padding: 8px; border-radius: 6px; color: {PAL['text']}; font-size: 13px; }}")
        caja_prov = QHBoxLayout()
        caja_prov.setSpacing(8)
        caja_prov.addWidget(self._prov_nombre, 1)
        self._btn_alta_prov = QPushButton("＋ Id")
        self._btn_alta_prov.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_alta_prov.setFixedWidth(64)
        self._btn_alta_prov.setStyleSheet(
            "QPushButton { background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; "
            "border-radius: 6px; padding: 8px; font-weight: 700; }"
        )
        self._btn_alta_prov.clicked.connect(self._alta_proveedor)
        caja_prov.addWidget(self._btn_alta_prov)
        fl.addLayout(caja_prov, 1, 3)
        self._cargar_combo_proveedores()

        lbl_tropa = QLabel("Tropa/Lote:")
        lbl_tropa.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_tropa, 2, 0)
        self._prov_tropa = input_field("Nro Tropa"); fl.addWidget(self._prov_tropa, 2, 1)

        lbl_merc = QLabel("Mercadería (Foco):")
        lbl_merc.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_merc, 2, 2)
        self._prov_type = QComboBox()
        self._prov_type.addItems(["Carne_Media Res", "Carne_Mocho", "Carne_Pecho", "Cerdo", "Pollo", "Achuras", "Otro"])
        self._prov_type.setStyleSheet(f"QComboBox {{ background: {PAL.get('surface2', '#E2E8F0')}; border: 1px solid {PAL['border']}; padding: 8px; border-radius: 6px; color: {PAL['text']}; font-weight: 800; font-size: 13px; }}")
        self._prov_type.currentTextChanged.connect(self._on_prov_type_change)
        fl.addWidget(self._prov_type, 2, 3)

        lbl_precio = QLabel("Precio Unit.:")
        lbl_precio.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_precio, 3, 0)
        self._prov_precio = input_field("Precio x Kg/Caja")
        self._prov_precio.setStyleSheet(f"QLineEdit {{ background: #FEF3C7; border: 2px solid #F59E0B; padding: 10px; border-radius: 8px; color: #92400E; font-weight: bold; font-size: 14px; }}")
        fl.addWidget(self._prov_precio, 3, 1)

        self._lbl_carga = QLabel("⚡ CARGA RÁPIDA (PESO + ENTER):")
        self._lbl_carga.setStyleSheet("QLabel { color: #EF4444; font-weight: 900; font-size: 13px; text-transform: uppercase; }")
        fl.addWidget(self._lbl_carga, 3, 2)

        self._romaneo_input = input_field("Ej: 80.5 y Enter")
        self._romaneo_input.setStyleSheet(f"QLineEdit {{ background: #ECFDF5; border: 2px solid #10B981; padding: 12px; border-radius: 8px; color: #065F46; font-weight: 900; font-size: 16px; }}")
        self._romaneo_input.returnPressed.connect(self._add_romaneo_item)
        fl.addWidget(self._romaneo_input, 3, 3)

        self._romaneo_table = build_table(["Nro", "Mercadería", "Precio Unit.", "Peso/Cant", "Subtotal", "X"])
        self._romaneo_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._romaneo_table.setFixedHeight(200)
        self._romaneo_table.setStyleSheet(f"QTableWidget {{ background: white; border: 1px solid {PAL['border']}; border-radius: 8px; font-size: 13px; font-weight: 600; }}")
        fl.addWidget(self._romaneo_table, 4, 0, 1, 4)

        main_h.addWidget(left_panel, stretch=6)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        totals_card = QFrame()
        totals_card.setStyleSheet(f"""
            QFrame {{ background: #0F172A; border-radius: 16px; border: 2px solid #1E293B; }}
            QLabel {{ color: white; background: transparent; }}
        """)
        t_lay = QVBoxLayout(totals_card)
        t_lay.setContentsMargins(20, 20, 20, 20)

        lbl_t1 = QLabel("RESUMEN DE ROMANEO")
        lbl_t1.setStyleSheet("QLabel { color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px; }")
        t_lay.addWidget(lbl_t1)

        self._lbl_romaneo_totals = QLabel(f"0 items - {texto(0)}")
        self._lbl_romaneo_totals.setStyleSheet("QLabel { color: #38BDF8; font-weight: 900; font-size: 22px; }")
        t_lay.addWidget(self._lbl_romaneo_totals)

        t_lay.addSpacing(15)
        lbl_t2 = QLabel("MONTO TOTAL")
        lbl_t2.setStyleSheet("QLabel { color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px; }")
        t_lay.addWidget(lbl_t2)

        self._prov_amount = QLineEdit("0.00")
        self._prov_amount.setReadOnly(True)
        self._prov_amount.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._prov_amount.setStyleSheet("QLineEdit { background: transparent; border: none; color: #10B981; font-weight: 900; font-size: 36px; }")
        t_lay.addWidget(self._prov_amount)

        right_panel.addWidget(totals_card)

        action_card = QFrame()
        self._panel_acciones = action_card
        action_card.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 16px; }}")
        a_lay = QVBoxLayout(action_card)
        a_lay.setContentsMargins(20, 20, 20, 20)

        lbl_pago = QLabel("💳 CONDICIÓN DE PAGO:")
        lbl_pago.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        a_lay.addWidget(lbl_pago)
        self._prov_payment = QComboBox()
        self._prov_payment.addItems(["A Pagar (Deuda en Cta. Cte.)", "Contado (Pago Inmediato)"])
        self._prov_payment.setStyleSheet(f"QComboBox {{ background: {PAL.get('surface2', '#E2E8F0')}; border: 1px solid {PAL['border']}; padding: 12px; border-radius: 8px; color: {PAL['text']}; font-weight: 800; font-size: 13px; }}")
        a_lay.addWidget(self._prov_payment)

        a_lay.addSpacing(15)
        btn_add = QPushButton("✅ PROCESAR COMPRA")
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669);
                color: white; border-radius: 16px; padding: 15px; font-weight: 900; font-size: 16px;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._save_proveedor)
        a_lay.addWidget(btn_add)

        right_panel.addWidget(action_card)
        right_panel.addStretch()

        main_h.addLayout(right_panel, stretch=4)
        lay_carga.addLayout(main_h)
        lay_carga.addStretch()

        self.stack.addWidget(self.widget_carga)
        lay.addWidget(self.stack)

        # ── SECCIÓN INFERIOR COMPARTIDA: HISTÓRICO Y CUENTAS CORRIENTES ───────
        self.history_container = QWidget()
        h_box = QVBoxLayout(self.history_container)
        h_box.setContentsMargins(0, 0, 0, 0)
        h_box.setSpacing(10)

        lbl_hist = section_title("📋  Histórico de Compras a Proveedores (Cuentas Corrientes)")
        h_box.addWidget(lbl_hist)

        self._tbl_prov = build_table(["ID", "Proveedor", "Monto Total", "Pagado", "Restante", "Fecha", "Estado", "Acción"])
        self._tbl_prov.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self._tbl_prov.setFixedHeight(210)
        h_box.addWidget(self._tbl_prov)

        lay.addWidget(self.history_container)

        self._switch_tab(0)

    def _switch_tab(self, idx):
        self.stack.setCurrentIndex(idx)
        
        btn_activo_style = """
            QPushButton {
                background: #2563EB; color: #FFFFFF; border: none;
                border-radius: 8px; padding: 0 16px; font-weight: 800; font-size: 13px;
            }
        """
        btn_inactivo_style = """
            QPushButton {
                background: #FFFFFF; color: #475569; border: 1.5px solid #CBD5E1;
                border-radius: 8px; padding: 0 16px; font-weight: 700; font-size: 13px;
            }
            QPushButton:hover { background: #F8FAFC; border-color: #94A3B8; }
        """

        self.btn_tab_pedidos.setStyleSheet(btn_activo_style if idx == 0 else btn_inactivo_style)
        self.btn_tab_recepcion.setStyleSheet(btn_activo_style if idx == 1 else btn_inactivo_style)
        self.btn_tab_carga.setStyleSheet(btn_activo_style if idx == 2 else btn_inactivo_style)

        if idx == 0:
            self.history_container.hide()
            if hasattr(self, 'panel_pedidos'):
                self.panel_pedidos.refrescar_datos()
        elif idx == 1:
            self.history_container.show()
            self.cargar_datos()
            if hasattr(self, 'panel_recepcion'):
                self.panel_recepcion.recargar_proveedores()
                self.panel_recepcion.enfocar_escaner()
        elif idx == 2:
            self.history_container.show()
            self._cargar_combo_proveedores()
            self.cargar_datos()

    def _on_prov_type_change(self, text):
        if text == "Pollo":
            self._lbl_carga.setText("⚡ CARGA RÁPIDA (KILOS TOTALES CAJÓN):")
            self._romaneo_input.setPlaceholderText("Ej: 20 (Kilos del cajón)")
        elif text == "Cerdo":
            self._lbl_carga.setText("⚡ CARGA RÁPIDA (PESOS DEL CERDO):")
            self._romaneo_input.setPlaceholderText("Ej: 80.5 y Enter")
        else:
            self._lbl_carga.setText("⚡ CARGA RÁPIDA (PESO + ENTER):")
            self._romaneo_input.setPlaceholderText("Ej: 80.5 y Enter")
        self._romaneo_input.setFocus()

    def _add_romaneo_item(self):
        val = self._romaneo_input.text().strip().replace(',', '.')
        precio_val = self._prov_precio.text().strip().replace(',', '.')
        if not val or not precio_val:
            QMessageBox.warning(self, "Error", "Debe ingresar el Precio Unitario antes de cargar pesos.")
            self._prov_precio.setFocus()
            return

        try:
            val_float = float(val)
            precio_float = float(precio_val)
            subtotal = val_float * precio_float

            row = self._romaneo_table.rowCount()
            self._romaneo_table.insertRow(row)

            nro_item = QTableWidgetItem(f"#{row+1}")
            nro_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._romaneo_table.setItem(row, 0, nro_item)

            merc_item = QTableWidgetItem(self._prov_type.currentText())
            merc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._romaneo_table.setItem(row, 1, merc_item)

            pu_item = QTableWidgetItem(texto(precio_float))
            pu_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._romaneo_table.setItem(row, 2, pu_item)

            peso_item = QTableWidgetItem(f"{val_float:.2f}")
            peso_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._romaneo_table.setItem(row, 3, peso_item)

            sub_item = QTableWidgetItem(texto(subtotal))
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._romaneo_table.setItem(row, 4, sub_item)

            btn_del = QPushButton("X")
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet("QPushButton { background-color: #ef4444; color: white; border-radius: 4px; font-weight: bold; }")
            btn_del.clicked.connect(lambda _, r=row: self._remove_romaneo_item(r))

            widget = QWidget()
            l = QHBoxLayout(widget)
            l.setContentsMargins(0,0,0,0)
            l.addWidget(btn_del)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._romaneo_table.setCellWidget(row, 5, widget)

            self._romaneo_input.clear()
            self._romaneo_input.setFocus()
            self._romaneo_table.scrollToBottom()
            self._update_prov_calc()
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese valores numéricos válidos en Peso/Precio.")

    def _remove_romaneo_item(self, row):
        self._romaneo_table.removeRow(row)
        for i in range(self._romaneo_table.rowCount()):
            self._romaneo_table.item(i, 0).setText(f"#{i+1}")
            widget = self._romaneo_table.cellWidget(i, 5)
            if widget:
                btn = widget.findChild(QPushButton)
                if btn:
                    try: btn.clicked.disconnect()
                    except: pass
                    btn.clicked.connect(lambda _, r=i: self._remove_romaneo_item(r))
        self._update_prov_calc()

    def _update_prov_calc(self):
        monto_total = 0.0
        items_count = self._romaneo_table.rowCount()
        for i in range(items_count):
            monto_total += leer(self._romaneo_table.item(i, 4).text())

        self._lbl_romaneo_totals.setText(f"{items_count} items - {texto(monto_total)}")
        self._prov_amount.setText(f"{monto_total:.2f}")

    def cargar_datos(self):
        """Carga el historial de compras utilizando el motor."""
        tienda_online = MotorProveedor.tienda_disponible()
        _db, modo = MotorProveedor._get_read_db(self.perfil, self._db_jefe)
        self._solo_lectura = not tienda_online
        self._panel_carga.setEnabled(tienda_online)
        self._panel_acciones.setEnabled(tienda_online)
        if self._solo_lectura and modo == "copia":
            self._lbl_estado_red.setText(
                "Sin conexión con la tienda. Consulta de solo lectura desde la última copia del nodo; "
                "compras y pagos requieren conexión."
            )
            self._lbl_estado_red.show()
        elif self._solo_lectura and modo == "sin_copia":
            self._lbl_estado_red.setText(
                "Sin conexión y sin copia del nodo disponible. No se muestra un historial local incompleto; "
                "conecte la tienda o el nodo."
            )
            self._lbl_estado_red.show()
        elif self._solo_lectura:
            self._lbl_estado_red.setText(
                "Consulta de solo lectura. Compras y pagos requieren conexión con la tienda."
            )
            self._lbl_estado_red.show()
        else:
            self._lbl_estado_red.hide()

        rows = MotorProveedor.load_proveedores(self.perfil, self._db_jefe)
        self._tbl_prov.setRowCount(0)

        for r in rows:
            row = self._tbl_prov.rowCount()
            self._tbl_prov.insertRow(row)

            vals = [
                str(r["id"]),
                r["proveedor"],
                plata(r["monto"]),
                plata(r["pagado"]),
                plata(r["restante"]),
                _dia(r["fecha"]),
                "✅ Pagado" if r["estado"] not in ("Pendiente", "pending") else "⏳ Pendiente"
            ]

            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c == 0:
                    vestir_id(it)
                elif c == 1:
                    vestir_nombre(it)
                elif c in (2, 3, 4):
                    vestir_numero(it)
                if c == 6 and "Pendiente" in v:
                    it.setForeground(QColor(PAL["danger"]))
                elif c == 6 and "Pagado" in v:
                    it.setForeground(QColor("#10B981"))
                self._tbl_prov.setItem(row, c, it)

            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0,0,0,0)
            btn_ver = btn_ghost("👁️ Ver Remito")
            btn_ver.setFixedHeight(30)
            btn_ver.clicked.connect(lambda _, rid=r["id"], d=r["desc_full"], rem=r["restante"]: self._show_remito_detail(rid, d, rem))
            l.addWidget(btn_ver)
            self._tbl_prov.setCellWidget(row, 7, w)

    def _show_remito_detail(self, debt_id, desc, restante):
        dlg = QDialog(self)
        dlg.setWindowTitle("📄 Detalle de Remito")
        dlg.setMinimumWidth(400)
        dlg.setStyleSheet(f"QDialog {{ background: {PAL['bg']}; }} QLabel {{ color: {PAL['text']}; font-size: 14px; }}")

        lay = QVBoxLayout(dlg)
        lbl_desc = QLabel(desc.replace("\n", "<br>"))
        lbl_desc.setWordWrap(True)
        lay.addWidget(lbl_desc)
        lay.addSpacing(20)

        if restante > 0 and not getattr(self, "_solo_lectura", False):
            btn_pagar = btn_primary(f"💳 Pagar Deuda (Falta {texto(restante)})")
            btn_pagar.clicked.connect(lambda: [dlg.accept(), self._pagar_proveedor(debt_id, restante)])
            lay.addWidget(btn_pagar)

        btn_cerrar = btn_ghost("Cerrar")
        btn_cerrar.clicked.connect(dlg.reject)
        lay.addWidget(btn_cerrar)
        qt_exec(dlg)

    def _pagar_proveedor(self, debt_id, restante):
        if getattr(self, "_solo_lectura", False):
            QMessageBox.warning(
                self, "Sin conexión", "La consulta está disponible, pero los pagos requieren conexión con la tienda."
            )
            return
        if restante <= 0:
            QMessageBox.information(self, "Aviso", "Esta cuenta ya está saldada.")
            return
        amt, ok = QInputDialog.getDouble(self, "Pagar a Proveedor", f"Monto a pagar (Restante: {texto(restante)}):", min=0, max=restante, decimals=2)
        if ok and amt > 0:
            try:
                MotorProveedor.pagar_proveedor(debt_id, amt, self.perfil, self._db_jefe)
                QMessageBox.information(self, "Éxito", f"Pago de {texto(amt)} registrado.")
                self.cargar_datos()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo registrar el pago: {e}")

    def _cargar_combo_proveedores(self, conservar=True):
        texto = self._prov_nombre.currentText() if conservar else ""
        self._prov_nombre.blockSignals(True)
        self._prov_nombre.clear()
        self._prov_nombre.addItem("Sin Proveedor (Proveedor General)", {"nombre": "Proveedor General", "codigo": "P00000"})
        vistos = {"PROVEEDOR GENERAL"}
        for ficha in FichaProveedor.listar():
            self._prov_nombre.addItem(etiqueta(ficha), ficha)
            vistos.add(ficha["nombre"].strip().upper())
        for nombre in MotorProveedor.get_proveedores_unicos(self.perfil, self._db_jefe) or []:
            limpio = str(nombre or "").strip()
            if limpio and limpio.upper() not in vistos:
                self._prov_nombre.addItem(limpio)
                vistos.add(limpio.upper())
        if texto:
            self._prov_nombre.setCurrentText(texto)
        self._prov_nombre.blockSignals(False)

    def _alta_proveedor(self):
        alta = DialogoAltaProveedor(self)
        if alta.exec() != QDialog.DialogCode.Accepted or not alta.ficha:
            return
        self._cargar_combo_proveedores(conservar=False)
        marca = etiqueta(alta.ficha)
        idx = self._prov_nombre.findText(marca)
        if idx >= 0:
            self._prov_nombre.setCurrentIndex(idx)

    def _save_proveedor(self):
        if getattr(self, "_solo_lectura", False):
            QMessageBox.warning(
                self, "Sin conexión", "La consulta está disponible, pero las compras requieren conexión con la tienda."
            )
            return
        amount_text = self._prov_amount.text()
        if not amount_text or self._romaneo_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Debe cargar ítems y un monto total.")
            return

        try:
            amount = float(amount_text)
            date = self._prov_date.date().toString("yyyy-MM-dd")
            prov_name = nombre_de_eleccion(
                self._prov_nombre.currentText(), self._prov_nombre.currentData()
            )
            tropa = self._prov_tropa.text() or "-"

            grupos = {}
            for i in range(self._romaneo_table.rowCount()):
                nro = self._romaneo_table.item(i, 0).text()
                merc = self._romaneo_table.item(i, 1).text()
                precio = leer(self._romaneo_table.item(i, 2).text())
                peso = float(self._romaneo_table.item(i, 3).text())
                key = (merc, precio)
                if key not in grupos: grupos[key] = []
                grupos[key].append((nro, peso))

            payment = self._prov_payment.currentText()

            success, msg = MotorProveedor.save_proveedor(
                date, prov_name, tropa, grupos, payment, amount, self.perfil, self._db_jefe
            )

            if success:
                QMessageBox.information(self, "Exito", "Compra registrada correctamente.")
                self._romaneo_table.setRowCount(0)
                self._prov_precio.clear()
                self._prov_amount.clear()
                self._romaneo_input.clear()
                self._prov_tropa.clear()
                self._cargar_combo_proveedores(conservar=False)
                if hasattr(self, '_prov_nombre'):
                    self._prov_nombre.setCurrentText("")
                self._update_prov_calc()
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error", f"Error guardando proveedor: {msg}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error procesando la compra: {e}")

