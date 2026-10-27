from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QComboBox, QFrame, QMessageBox, QApplication,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QEvent
from PyQt6.QtGui import QColor, QFont

from src.proveedor_global.backend.recepcion_service import RecepcionService
from src.proveedor_global.backend.ficha import FichaProveedor, etiqueta
from src.proveedor_global.frontend.panel_pedidos_automaticos import DialogoAltaProveedor
from src.contabilidad.shared_globals import PAL, date_field
from src.utils.letra import (
    vestir_id, vestir_nombre, vestir_numero, fuente_nombre
)


def plata(n) -> str:
    """Monto de la tienda: símbolo y separadores de la config."""
    from src.proveedor_global.backend.moneda import texto

    return texto(n)

class PanelRecepcionRapida(QWidget):
    """
    Panel de Recepción Rápida de Mercadería por Escáner y Buscador Inteligente Asistido.
    Diseñado para máxima facilidad:
    - Escaneo con pistola (códigos de barras exactos).
    - Multiplicadores al estilo Cajero (ej: 12*codigo o 7*prov).
    - Buscador predictivo en vivo con ventana flotante para usuarios sin experiencia.
    - Estructura gemela en espejo con Romaneo Frigorífico y Cuentas Corrientes.
    """
    compra_guardada = pyqtSignal()

    def __init__(self, parent=None, perfil="admin"):
        super().__init__(parent)
        self.perfil = perfil
        self._items = []  # Lista de dicts con los articulos ingresados
        self._whatsapp_texto_ultimo = ""
        self._multiplicador_activo = 1.0

        self._build_ui()
        self._init_buscador_asistido()
        self.recargar_proveedores()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        main_h = QHBoxLayout()
        main_h.setSpacing(20)

        # ── 1. COLUMNA IZQUIERDA: DATOS DEL REMITO + ESCÁNER + TABLA ────────
        left_panel = QFrame()
        left_panel.setObjectName("Card")
        left_panel.setStyleSheet(f"""
            QFrame#Card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PAL['surface']}, stop:1 #F8FAFC);
                border: 1px solid {PAL['border']};
                border-radius: 16px;
            }}
        """)
        fl = QGridLayout(left_panel)
        fl.setContentsMargins(20, 20, 20, 20)
        fl.setSpacing(12)

        # Título
        title_lbl = QLabel("🧾 DATOS DEL REMITO Y RECEPCIÓN")
        title_lbl.setStyleSheet(f"QLabel {{ color: {PAL['primary']}; font-weight: 900; font-size: 14px; letter-spacing: 1px; }}")
        fl.addWidget(title_lbl, 0, 0, 1, 4)

        # Fila 1: Fecha y Proveedor
        lbl_fecha = QLabel("Fecha:")
        lbl_fecha.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; font-size: 13px; }}")
        fl.addWidget(lbl_fecha, 1, 0)

        self.dt_fecha = date_field()
        fl.addWidget(self.dt_fecha, 1, 1)

        lbl_prov = QLabel("Proveedor:")
        lbl_prov.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; font-size: 13px; }}")
        fl.addWidget(lbl_prov, 1, 2)

        caja_prov = QHBoxLayout()
        caja_prov.setSpacing(8)

        self.cb_proveedor = QComboBox()
        self.cb_proveedor.setEditable(True)
        self.cb_proveedor.setFixedHeight(36)
        self.cb_proveedor.setPlaceholderText("Seleccionar o escribir proveedor...")
        self.cb_proveedor.setStyleSheet(f"""
            QComboBox {{
                background: white; border: 1px solid {PAL['border']};
                padding: 0 10px; border-radius: 6px; color: #0F172A; font-size: 13px; font-weight: 700;
            }}
            QComboBox QLineEdit {{
                color: #0F172A; background: white; border: none; font-size: 13px; font-weight: 700;
            }}
        """)
        caja_prov.addWidget(self.cb_proveedor, 1)

        self._btn_alta_prov = QPushButton("＋ Id")
        self._btn_alta_prov.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_alta_prov.setFixedWidth(64)
        self._btn_alta_prov.setFixedHeight(36)
        self._btn_alta_prov.setStyleSheet(
            "QPushButton { background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; "
            "border-radius: 6px; font-weight: 800; font-size: 12px; }"
            "QPushButton:hover { background: #E0E7FF; }"
        )
        self._btn_alta_prov.clicked.connect(self._alta_proveedor)
        caja_prov.addWidget(self._btn_alta_prov)

        fl.addLayout(caja_prov, 1, 3)

        # Fila 2: Barra de Escáner Verde (Autofocus Permanente)
        self.scan_card = QFrame()
        self.scan_card.setObjectName("ScanCard")
        self.scan_card.setStyleSheet("""
            QFrame#ScanCard {
                background: #F0FDF4; border: 2px solid #86EFAC; border-radius: 10px;
            }
        """)
        s_lay = QHBoxLayout(self.scan_card)
        s_lay.setContentsMargins(12, 8, 12, 8)
        s_lay.setSpacing(10)

        lbl_scan_icon = QLabel("⚡")
        lbl_scan_icon.setStyleSheet("font-size: 18px;")
        s_lay.addWidget(lbl_scan_icon)

        self.txt_scan = QLineEdit()
        self.txt_scan.setFixedHeight(36)
        self.txt_scan.setPlaceholderText("Escaneá con pistola o escribí (ej: 1*prov, harina, 7*código) + ENTER")
        self.txt_scan.setStyleSheet("""
            QLineEdit {
                background: #FFFFFF; border: 1.5px solid #4ADE80; border-radius: 6px;
                padding: 0 12px; font-size: 13px; font-weight: 700; color: #14532D;
            }
            QLineEdit:focus { border: 2px solid #16A34A; }
        """)
        self.txt_scan.returnPressed.connect(self._on_scan_enter)
        self.txt_scan.installEventFilter(self)
        s_lay.addWidget(self.txt_scan, 1)

        btn_agregar_manual = QPushButton("➕ Agregar")
        btn_agregar_manual.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_agregar_manual.setFixedHeight(36)
        btn_agregar_manual.setStyleSheet("""
            QPushButton {
                background: #16A34A; color: white; border: none; border-radius: 6px;
                padding: 0 16px; font-size: 12px; font-weight: 800;
            }
            QPushButton:hover { background: #15803D; }
        """)
        btn_agregar_manual.clicked.connect(self._on_scan_enter)
        s_lay.addWidget(btn_agregar_manual)

        fl.addWidget(self.scan_card, 2, 0, 1, 4)

        # Fila 3: Tabla de Mercadería Escaneada en Vivo
        self.tbl_ingreso = QTableWidget()
        self.tbl_ingreso.setColumnCount(8)
        self.tbl_ingreso.setHorizontalHeaderLabels([
            "#", "Código", "Producto", "Stock Act.", "Cant.", "Costo unit.", "Subtotal", "❌"
        ])
        self.tbl_ingreso.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_ingreso.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_ingreso.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl_ingreso.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_ingreso.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_ingreso.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_ingreso.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_ingreso.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tbl_ingreso.setColumnWidth(7, 44)

        self.tbl_ingreso.setFixedHeight(210)
        self.tbl_ingreso.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_ingreso.setStyleSheet(f"""
            QTableWidget {{
                background: #FFFFFF; border: 1px solid {PAL['border']}; border-radius: 8px;
                gridline-color: #F1F5F9; font-size: 12px;
            }}
            QHeaderView::section {{
                background: #F8FAFC; color: #334155; font-weight: 800;
                padding: 8px; border: none; border-bottom: 2px solid #CBD5E1;
            }}
        """)
        self.tbl_ingreso.cellChanged.connect(self._on_cell_edited)
        fl.addWidget(self.tbl_ingreso, 3, 0, 1, 4)

        main_h.addWidget(left_panel, stretch=6)

        # ── 2. COLUMNA DERECHA: RESUMEN DE RECEPCIÓN Y CIERRE ────────────────
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        # Tarjeta oscura de Totales (Mismo diseño que Romaneo)
        totals_card = QFrame()
        totals_card.setStyleSheet("""
            QFrame {{ background: #0F172A; border-radius: 16px; border: 2px solid #1E293B; }}
            QLabel {{ color: white; background: transparent; }}
        """)
        t_lay = QVBoxLayout(totals_card)
        t_lay.setContentsMargins(20, 18, 20, 18)
        t_lay.setSpacing(6)

        lbl_t1 = QLabel("RESUMEN DE RECEPCIÓN")
        lbl_t1.setStyleSheet("QLabel { color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px; }")
        t_lay.addWidget(lbl_t1)

        self.lbl_total_bultos = QLabel("0 artículos - 0 unidades")
        self.lbl_total_bultos.setStyleSheet("QLabel { color: #38BDF8; font-weight: 900; font-size: 20px; }")
        t_lay.addWidget(self.lbl_total_bultos)

        t_lay.addSpacing(12)
        lbl_t2 = QLabel("MONTO TOTAL")
        lbl_t2.setStyleSheet("QLabel { color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px; }")
        t_lay.addWidget(lbl_t2)

        self.lbl_total_monto = QLabel(plata(0))
        self.lbl_total_monto.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_total_monto.setStyleSheet("QLabel { color: #10B981; font-weight: 900; font-size: 34px; }")
        t_lay.addWidget(self.lbl_total_monto)

        right_panel.addWidget(totals_card)

        # Tarjeta de Condición de Pago y Acciones
        action_card = QFrame()
        action_card.setStyleSheet(f"""
            QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 16px; }}
            QLabel {{ color: {PAL['text']}; font-weight: bold; font-size: 12px; }}
        """)
        a_lay = QVBoxLayout(action_card)
        a_lay.setContentsMargins(18, 16, 18, 16)
        a_lay.setSpacing(10)

        lbl_pago = QLabel("💳 CONDICIÓN DE PAGO:")
        a_lay.addWidget(lbl_pago)

        self.cb_pago = QComboBox()
        self.cb_pago.setFixedHeight(38)
        self.cb_pago.addItems(["A Pagar (Deuda en Cta. Cte.)", "Contado (Pago Inmediato)"])
        self.cb_pago.setStyleSheet(f"""
            QComboBox {{
                background: {PAL.get('surface2', '#E2E8F0')}; border: 1px solid {PAL['border']};
                padding: 0 10px; border-radius: 8px; color: {PAL['text']}; font-weight: 800; font-size: 13px;
            }}
        """)
        a_lay.addWidget(self.cb_pago)

        a_lay.addSpacing(6)
        btn_confirmar = QPushButton("📥 CONFIRMAR INGRESO A STOCK")
        btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirmar.setFixedHeight(46)
        btn_confirmar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669);
                color: white; border: none; border-radius: 12px; padding: 0 16px;
                font-weight: 900; font-size: 14px; letter-spacing: 0.5px;
            }
            QPushButton:hover { background: #059669; }
        """)
        btn_confirmar.clicked.connect(self._confirmar_ingreso)
        a_lay.addWidget(btn_confirmar)

        # Fila de utilidades (WhatsApp + Limpiar)
        aux_h = QHBoxLayout()
        aux_h.setSpacing(8)

        self.btn_whatsapp = QPushButton("📱 Copiar WhatsApp")
        self.btn_whatsapp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_whatsapp.setFixedHeight(34)
        self.btn_whatsapp.setStyleSheet("""
            QPushButton {
                background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE;
                border-radius: 8px; padding: 0 10px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background: #E0E7FF; }
        """)
        self.btn_whatsapp.clicked.connect(self._copiar_whatsapp)
        aux_h.addWidget(self.btn_whatsapp, 1)

        btn_limpiar = QPushButton("🗑️ Limpiar")
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar.setFixedHeight(34)
        btn_limpiar.setStyleSheet("""
            QPushButton {
                background: #F8FAFC; color: #64748B; border: 1px solid #CBD5E1;
                border-radius: 8px; padding: 0 10px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background: #F1F5F9; color: #0F172A; }
        """)
        btn_limpiar.clicked.connect(self._limpiar_planilla)
        aux_h.addWidget(btn_limpiar)

        a_lay.addLayout(aux_h)

        right_panel.addWidget(action_card)
        right_panel.addStretch()

        main_h.addLayout(right_panel, stretch=4)
        root.addLayout(main_h)

    def _init_buscador_asistido(self):
        """Inicializa el overlay flotante de resultados para usuarios sin experiencia de PC."""
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._ejecutar_busqueda_en_vivo)
        self.txt_scan.textChanged.connect(self._on_txt_scan_changed)

        # Panel flotante overlay
        self.panel_busqueda = QFrame(self)
        self.panel_busqueda.setObjectName("BuscadorAsistidoPanel")
        self.panel_busqueda.hide()
        self.panel_busqueda.setStyleSheet("""
            QFrame#BuscadorAsistidoPanel {
                background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 10px;
            }
        """)

        b_lay = QVBoxLayout(self.panel_busqueda)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setSpacing(0)

        self.tbl_busqueda = QTableWidget(0, 3)
        self.tbl_busqueda.setObjectName("BuscadorAsistidoTable")
        self.tbl_busqueda.setHorizontalHeaderLabels(["PRODUCTO", "COSTO ACTUAL", "STOCK ACTUAL"])
        self.tbl_busqueda.verticalHeader().setVisible(False)
        self.tbl_busqueda.setShowGrid(False)
        self.tbl_busqueda.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_busqueda.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_busqueda.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_busqueda.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        hdr = self.tbl_busqueda.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.tbl_busqueda.setStyleSheet("""
            QTableWidget#BuscadorAsistidoTable {
                background-color: #FFFFFF; color: #0F172A; border: none; font-size: 13px; font-weight: 700;
            }
            QTableWidget#BuscadorAsistidoTable::item {
                padding: 6px 12px; border-bottom: 1px solid #E2E8F0;
            }
            QTableWidget#BuscadorAsistidoTable::item:selected {
                background-color: #DBEAFE; color: #0F172A; font-weight: 800;
            }
            QHeaderView::section {
                background-color: #F8FAFC; color: #64748B; font-weight: 800; font-size: 11px;
                padding: 6px 10px; border: none; border-bottom: 1px solid #E2E8F0;
            }
        """)
        self.tbl_busqueda.itemClicked.connect(lambda _: self._seleccionar_item_busqueda())
        b_lay.addWidget(self.tbl_busqueda)

        # Pie informativo con atajos claros
        self.lbl_busqueda_pie = QLabel("Resultados · ↑↓ Navegar · Enter Agregar · Esc Cerrar")
        self.lbl_busqueda_pie.setStyleSheet("""
            background: #F8FAFC; color: #64748B; font-size: 11px; font-weight: 800;
            padding: 7px 12px; border-top: 1px solid #E2E8F0; border-bottom-left-radius: 9px; border-bottom-right-radius: 9px;
        """)
        b_lay.addWidget(self.lbl_busqueda_pie)

    def eventFilter(self, obj, event):
        if obj == self.txt_scan and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if self.panel_busqueda.isVisible():
                if key == Qt.Key.Key_Down:
                    curr = self.tbl_busqueda.currentRow()
                    if curr < self.tbl_busqueda.rowCount() - 1:
                        self.tbl_busqueda.setCurrentCell(curr + 1, 0)
                        self.tbl_busqueda.selectRow(curr + 1)
                    return True
                elif key == Qt.Key.Key_Up:
                    curr = self.tbl_busqueda.currentRow()
                    if curr > 0:
                        self.tbl_busqueda.setCurrentCell(curr - 1, 0)
                        self.tbl_busqueda.selectRow(curr - 1)
                    return True
                elif key == Qt.Key.Key_Escape:
                    self._ocultar_busqueda()
                    return True
                elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if self.tbl_busqueda.currentRow() >= 0:
                        self._seleccionar_item_busqueda()
                        return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "panel_busqueda") and self.panel_busqueda.isVisible():
            self._posicionar_panel_busqueda()

    def _on_txt_scan_changed(self, txt: str):
        txt = (txt or "").strip()

        query = txt
        if '*' in query:
            partes = query.split('*', 1)
            query = partes[1].strip()

        # Si lo que se ingresó (directo o post-asterisco) es un código numérico largo de pistola de barras, no abrimos popup
        if query.isdigit() and len(query) >= 8:
            self.search_timer.stop()
            self._ocultar_busqueda()
            return

        if len(query) < 2:
            self.search_timer.stop()
            self._ocultar_busqueda()
            return

        self.search_timer.start(120)

    def _ejecutar_busqueda_en_vivo(self):
        txt_raw = self.txt_scan.text().strip()
        if not txt_raw:
            self._ocultar_busqueda()
            return

        try:
            prods, multiplicador = RecepcionService.buscar_productos_coincidentes(txt_raw, limit=8)
        except Exception:
            prods, multiplicador = [], 1.0
        if not prods:
            self._mostrar_busqueda_vacia(txt_raw)
            return

        self._multiplicador_activo = multiplicador
        self.tbl_busqueda.setRowCount(len(prods))

        blanco = QColor("#0F172A")
        amarillo = QColor("#B45309")
        gris = QColor("#64748B")

        for idx, p in enumerate(prods):
            # Producto
            nom_item = QTableWidgetItem(p["nombre"])
            nom_item.setData(Qt.ItemDataRole.UserRole, p)
            nom_item.setForeground(blanco)
            f_nom = QFont("Segoe UI", 11)
            f_nom.setBold(True)
            nom_item.setFont(f_nom)

            # Costo
            c_val = p.get("costo_actual", 0.0)
            costo_str = plata(c_val) if c_val > 0 else plata(0)
            costo_item = QTableWidgetItem(costo_str)
            costo_item.setForeground(amarillo)
            costo_item.setFont(f_nom)
            costo_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # Stock
            s_val = p.get("stock_actual", 0.0)
            s_str = f"{int(s_val)} un." if float(s_val).is_integer() else f"{s_val:.2f} un."
            stock_item = QTableWidgetItem(s_str)
            stock_item.setForeground(gris)
            stock_item.setFont(f_nom)
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tbl_busqueda.setItem(idx, 0, nom_item)
            self.tbl_busqueda.setItem(idx, 1, costo_item)
            self.tbl_busqueda.setItem(idx, 2, stock_item)

        self.tbl_busqueda.setCurrentCell(0, 0)
        self.tbl_busqueda.selectRow(0)

        n = len(prods)
        cant_txt = f"{int(multiplicador)}x" if float(multiplicador).is_integer() else f"{multiplicador:.2f}x"
        self.lbl_busqueda_pie.setText(
            f"{n} producto{'s' if n != 1 else ''} encontrado{'s' if n != 1 else ''} (Multiplicador: {cant_txt})  ·  ↑↓ Navegar  ·  Enter Agregar  ·  Esc Cerrar"
        )
        self.panel_busqueda.show()
        self._posicionar_panel_busqueda()

    def _mostrar_busqueda_vacia(self, txt_raw):
        self.tbl_busqueda.setRowCount(1)
        vacio = QTableWidgetItem(f"Sin coincidencias para «{txt_raw}»")
        vacio.setData(Qt.ItemDataRole.UserRole, None)
        vacio.setForeground(QColor("#F87171"))
        vacio.setFlags(Qt.ItemFlag.NoItemFlags)
        self.tbl_busqueda.setItem(0, 0, vacio)
        self.tbl_busqueda.setItem(0, 1, QTableWidgetItem(""))
        self.tbl_busqueda.setItem(0, 2, QTableWidgetItem(""))
        self.lbl_busqueda_pie.setText("Presione Esc para cerrar o ingrese otro nombre")
        self.panel_busqueda.show()
        self._posicionar_panel_busqueda()

    def _posicionar_panel_busqueda(self):
        if not hasattr(self, "panel_busqueda") or not self.panel_busqueda.isVisible():
            return
        ancla = self.window() or self
        if self.panel_busqueda.parent() is not ancla:
            self.panel_busqueda.setParent(ancla)
        pos = self.scan_card.mapTo(ancla, QPoint(0, self.scan_card.height() + 4))
        w = max(520, self.scan_card.width())
        rows_count = max(1, min(self.tbl_busqueda.rowCount(), 6))
        h = 32 + (rows_count * 36) + 30
        self.panel_busqueda.setGeometry(pos.x(), pos.y(), w, h)
        self.panel_busqueda.show()
        self.panel_busqueda.raise_()

    def _ocultar_busqueda(self):
        if hasattr(self, "panel_busqueda"):
            self.panel_busqueda.hide()

    def _seleccionar_item_busqueda(self):
        row = self.tbl_busqueda.currentRow()
        if row < 0:
            return
        item_0 = self.tbl_busqueda.item(row, 0)
        if not item_0:
            return
        prod = item_0.data(Qt.ItemDataRole.UserRole)
        if not prod:
            return

        cant = getattr(self, "_multiplicador_activo", 1.0) or 1.0
        self._agregar_producto_a_planilla(prod, cant)

        self._ocultar_busqueda()
        self.txt_scan.clear()
        self.enfocar_escaner()

    def _agregar_producto_a_planilla(self, prod: dict, cantidad: float):
        p_id = prod["id"]
        encontrado_idx = None
        for idx, it in enumerate(self._items):
            if it["id"] == p_id:
                encontrado_idx = idx
                break

        if encontrado_idx is not None:
            self._items[encontrado_idx]["cantidad"] += cantidad
            self._items[encontrado_idx]["subtotal"] = round(
                self._items[encontrado_idx]["cantidad"] * self._items[encontrado_idx]["costo"], 2
            )
        else:
            costo_ini = prod.get("costo_actual", 0.0)
            self._items.append({
                "id": prod["id"],
                "codigo": prod["codigo"],
                "nombre": prod["nombre"],
                "departamento": prod.get("departamento", "GENERAL"),
                "stock_actual": prod.get("stock_actual", 0.0),
                "cantidad": cantidad,
                "costo": costo_ini,
                "subtotal": round(cantidad * costo_ini, 2)
            })

        self._renderizar_tabla()

    def recargar_proveedores(self):
        """Carga la lista de proveedores desde FichaProveedor con opción por defecto."""
        try:
            texto_actual = self.cb_proveedor.currentText()
            self.cb_proveedor.blockSignals(True)
            self.cb_proveedor.clear()
            self.cb_proveedor.addItem("Sin Proveedor (Proveedor General)", "Proveedor General")
            fichas = FichaProveedor.listar()
            for f in fichas:
                self.cb_proveedor.addItem(f"{f['nombre']} ({f['codigo']})", f['nombre'])
            if texto_actual:
                idx = self.cb_proveedor.findText(texto_actual)
                if idx >= 0:
                    self.cb_proveedor.setCurrentIndex(idx)
                else:
                    self.cb_proveedor.setCurrentText(texto_actual)
            if not (texto_actual or "").strip():
                self.cb_proveedor.setCurrentIndex(0)
            self.cb_proveedor.blockSignals(False)
        except Exception:
            self.cb_proveedor.blockSignals(False)
            if self.cb_proveedor.count() == 0:
                self.cb_proveedor.addItem("Sin Proveedor (Proveedor General)", "Proveedor General")
            if not self.cb_proveedor.currentText().strip():
                self.cb_proveedor.setCurrentIndex(0)

    def _alta_proveedor(self):
        alta = DialogoAltaProveedor(self)
        if alta.exec() != DialogoAltaProveedor.DialogCode.Accepted or not alta.ficha:
            return
        self.recargar_proveedores()
        ficha = alta.ficha
        et = f"{ficha['nombre']} ({ficha['codigo']})"
        idx = self.cb_proveedor.findText(et)
        if idx >= 0:
            self.cb_proveedor.setCurrentIndex(idx)
        else:
            self.cb_proveedor.setCurrentText(ficha['nombre'])

    def enfocar_escaner(self):
        self.txt_scan.setFocus()
        self.txt_scan.selectAll()

    def _on_scan_enter(self):
        txt = self.txt_scan.text().strip()
        if not txt:
            return

        # 1. Si es un escaneo con código de barras exacto o ID exacto, se procesa prioritariamente (ej: 1*7790150570180)
        prod, multiplicador = RecepcionService.buscar_producto_por_escaneo(txt)
        if prod:
            self._agregar_producto_a_planilla(prod, multiplicador)
            self.txt_scan.clear()
            self._ocultar_busqueda()
            self.enfocar_escaner()
            return

        # 2. Si no fue código exacto pero el buscador asistido está desplegado con un ítem elegido, agregamos ese
        if self.panel_busqueda.isVisible() and self.tbl_busqueda.currentRow() >= 0:
            self._seleccionar_item_busqueda()
            return

        # 3. No encontrado
        QMessageBox.warning(self, "No encontrado", f"No se encontró ningún producto con: '{txt}'.\nPuede tipear el nombre o parte del código para ver sugerencias.")
        self.enfocar_escaner()

    def _renderizar_tabla(self):
        self.tbl_ingreso.blockSignals(True)
        self.tbl_ingreso.setRowCount(len(self._items))

        total_b = 0.0
        total_m = 0.0

        for idx, it in enumerate(self._items):
            cant = it["cantidad"]
            costo = it["costo"]
            subt = it["subtotal"]

            total_b += cant
            total_m += subt

            # #
            item_nro = vestir_id(QTableWidgetItem(f"#{idx+1}"))
            item_nro.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_nro.setFlags(item_nro.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Código
            item_cod = vestir_id(QTableWidgetItem(str(it["codigo"])))
            item_cod.setFlags(item_cod.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Nombre
            item_nom = vestir_nombre(QTableWidgetItem(str(it["nombre"])))
            item_nom.setFlags(item_nom.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Stock Actual
            item_stock = vestir_numero(QTableWidgetItem(str(it["stock_actual"])))
            item_stock.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_stock.setFlags(item_stock.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Cantidad (editable)
            cant_str = str(int(cant)) if isinstance(cant, float) and cant.is_integer() else f"{cant:.2f}"
            item_cant = vestir_numero(QTableWidgetItem(cant_str))
            item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_cant.setForeground(QColor("#2563EB"))

            # Costo Unitario (editable)
            item_costo = vestir_numero(QTableWidgetItem(f"{costo:.2f}"))
            item_costo.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            item_costo.setForeground(QColor("#D97706"))

            # Subtotal
            item_subt = vestir_numero(QTableWidgetItem(plata(subt)))
            item_subt.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            item_subt.setFlags(item_subt.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.tbl_ingreso.setItem(idx, 0, item_nro)
            self.tbl_ingreso.setItem(idx, 1, item_cod)
            self.tbl_ingreso.setItem(idx, 2, item_nom)
            self.tbl_ingreso.setItem(idx, 3, item_stock)
            self.tbl_ingreso.setItem(idx, 4, item_cant)
            self.tbl_ingreso.setItem(idx, 5, item_costo)
            self.tbl_ingreso.setItem(idx, 6, item_subt)

            # Botón ❌ Quitar ítem individual
            btn_del = QPushButton("❌")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setFixedSize(28, 26)
            btn_del.setStyleSheet("""
                QPushButton {
                    background: #FEE2E2; color: #DC2626; border: none; border-radius: 4px;
                    font-size: 11px; font-weight: bold;
                }
                QPushButton:hover { background: #FCA5A5; }
            """)
            btn_del.clicked.connect(lambda _, i=idx: self._eliminar_item(i))

            w_del = QWidget()
            l_del = QHBoxLayout(w_del)
            l_del.setContentsMargins(0, 0, 0, 0)
            l_del.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l_del.addWidget(btn_del)
            self.tbl_ingreso.setCellWidget(idx, 7, w_del)

        self.tbl_ingreso.blockSignals(False)

        # Actualizar KPIs
        bultos_fmt = int(total_b) if total_b.is_integer() else f"{total_b:.2f}"
        self.lbl_total_bultos.setText(f"{len(self._items)} art. ({bultos_fmt} un.)")
        self.lbl_total_monto.setText(plata(total_m))

    def _eliminar_item(self, idx: int):
        if 0 <= idx < len(self._items):
            self._items.pop(idx)
            self._renderizar_tabla()
            self.enfocar_escaner()

    def _on_cell_edited(self, row, col):
        """Permite editar cantidad (col 4) o costo unitario (col 5) en la misma celda."""
        if row >= len(self._items):
            return

        it = self._items[row]
        if col == 4:
            txt_cant = self.tbl_ingreso.item(row, col).text().replace(',', '.')
            try:
                nueva_cant = max(0.01, float(txt_cant))
                it["cantidad"] = nueva_cant
                it["subtotal"] = round(nueva_cant * it["costo"], 2)
            except ValueError:
                pass
        elif col == 5:
            from src.proveedor_global.backend.moneda import leer

            try:
                nuevo_costo = max(0.0, leer(self.tbl_ingreso.item(row, col).text()))
                it["costo"] = nuevo_costo
                it["subtotal"] = round(it["cantidad"] * nuevo_costo, 2)
            except ValueError:
                pass

        self._renderizar_tabla()

    def _limpiar_planilla(self):
        if not self._items:
            return
        resp = QMessageBox.question(
            self, "Limpiar Planilla", 
            "¿Desea vaciar los artículos escaneados actualmente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._items = []
            self._renderizar_tabla()
            self.enfocar_escaner()

    def _confirmar_ingreso(self):
        if not self._items:
            QMessageBox.warning(self, "Planilla vacía", "Por favor escanea al menos un producto antes de confirmar.")
            self.enfocar_escaner()
            return

        prov_data = self.cb_proveedor.currentData()
        prov_text = self.cb_proveedor.currentText().strip()
        prov = prov_data if (prov_data and prov_text == self.cb_proveedor.itemText(self.cb_proveedor.currentIndex())) else prov_text
        cond_pago = self.cb_pago.currentText().strip()

        ok, msg, resumen = RecepcionService.procesar_ingreso_mercaderia(
            proveedor_nombre=prov,
            items=self._items,
            condicion_pago=cond_pago,
            perfil=self.perfil
        )

        if ok:
            self._whatsapp_texto_ultimo = resumen.get("whatsapp_texto", "")
            QMessageBox.information(
                self, "✅ Ingreso a Stock y Remito Confirmado", 
                f"¡Mercadería ingresada y actualizada con éxito!\n\n"
                f"• Proveedor: {resumen.get('proveedor')}\n"
                f"• Artículos actualizados: {resumen.get('articulos_count')}\n"
                f"• Total bultos ingresados: {resumen.get('total_bultos')}\n"
                f"• Monto remito: {plata(resumen.get('total_monto'))}\n"
                f"• Condición de pago: {cond_pago}\n\n"
                f"👉 El remito ya figura en el Histórico de Compras y Cuentas Corrientes aquí abajo."
            )
            self._items = []
            self._renderizar_tabla()
            self.compra_guardada.emit()
            self.enfocar_escaner()
        else:
            QMessageBox.critical(self, "Error al ingresar", msg)

    def _copiar_whatsapp(self):
        txt = self._whatsapp_texto_ultimo
        if not txt:
            if self._items:
                prov = self.cb_proveedor.currentText().strip()
                cond_pago = self.cb_pago.currentText().strip()
                total_b = sum(it["cantidad"] for it in self._items)
                total_m = sum(it["subtotal"] for it in self._items)
                txt = RecepcionService.generar_whatsapp_conformidad(prov, self._items, total_b, total_m, cond_pago)
            else:
                QMessageBox.information(self, "Sin datos", "No hay mercadería escaneada para generar el comprobante.")
                return

        QApplication.clipboard().setText(txt)
        QMessageBox.information(
            self, "¡Copiado!", 
            "El comprobante de recepción conforme fue copiado al portapapeles.\nYa podés pegarlo en WhatsApp Web."
        )
