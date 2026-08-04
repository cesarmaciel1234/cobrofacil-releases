import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QFrame, QGridLayout,
    QDateEdit, QComboBox, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate

try:
    from src.config import config
    from src.utils.theme_manager import theme_manager
    from src.cerebro_global.cierre_caja_cerebro import MotorCierre, etiqueta_modo, normalizar_modo
    from src.ui_global.cierre_diario_ui.componentes.metric_card import MetricCard
    from src.ui_global.cierre_diario_ui.componentes.panel_arqueo import PanelArqueo
except ImportError:
    from config import config
    from utils.theme_manager import theme_manager
    from cerebro_global.cierre_caja_cerebro import MotorCierre, etiqueta_modo, normalizar_modo
    from src.ui_global.cierre_diario_ui.componentes.metric_card import MetricCard
    from src.ui_global.cierre_diario_ui.componentes.panel_arqueo import PanelArqueo

def fmt_moneda(val):
    try:
        return f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"${val}"

class ClickableMetricCard(MetricCard):
    clicked = pyqtSignal()
    
    def __init__(self, titulo, icon, color="#3B82F6", parent=None):
        super().__init__(titulo, icon, color, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self.styleSheet() + """
            QFrame#MetricCard:hover {
                background: #F1F5F9;
                border: 1px solid #94A3B8;
            }
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class DetallesDialog(QDialog):
    def __init__(self, titulo, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setFixedSize(450, 400)
        self.setStyleSheet("QDialog { background: white; }")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(25, 25, 25, 25)
        lay.setSpacing(15)
        
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E293B;")
        lay.addWidget(lbl_tit)
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(15)
        
        row = 0
        total = 0.0
        for desc, valor, is_negative in items:
            lbl_d = QLabel(desc)
            lbl_d.setStyleSheet("font-size: 15px; color: #475569; font-weight: bold;")
            
            val_fmt = f"{'-' if is_negative else '+'}{fmt_moneda(abs(valor))}"
            lbl_v = QLabel(val_fmt)
            if is_negative:
                lbl_v.setStyleSheet("font-size: 15px; font-weight: bold; color: #EF4444;")
                total -= abs(valor)
            else:
                lbl_v.setStyleSheet("font-size: 15px; font-weight: bold; color: #10B981;")
                total += abs(valor)
                
            lbl_v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(lbl_d, row, 0)
            grid.addWidget(lbl_v, row, 1)
            row += 1
            
        lay.addLayout(grid)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #E2E8F0; margin-top: 10px; margin-bottom: 10px;")
        lay.addWidget(line)
        
        h_tot = QHBoxLayout()
        lbl_t = QLabel("TOTAL CALCULADO:")
        lbl_t.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A;")
        lbl_tv = QLabel(fmt_moneda(total))
        lbl_tv.setStyleSheet("font-size: 18px; font-weight: 900; color: #0F172A;")
        lbl_tv.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        h_tot.addWidget(lbl_t)
        h_tot.addWidget(lbl_tv)
        lay.addLayout(h_tot)
        
        lay.addStretch()
        
        btn_cerrar = QPushButton("Cerrar Detalles")
        btn_cerrar.setFixedHeight(45)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9; color: #475569; font-weight: bold; font-size: 15px; border-radius: 8px; border: 1px solid #CBD5E1;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        btn_cerrar.clicked.connect(self.accept)
        lay.addWidget(btn_cerrar)

class CierreGlobalUI(QWidget):
    request_dashboard = pyqtSignal()
    turno_cerrado = pyqtSignal()

    def __init__(self, parent_main=None, is_terminal=False):
        super().__init__(parent_main)
        self.is_terminal = is_terminal
        self.parent_main = parent_main
        current = config.current_user or {}
        self.user = current.get("username", "Admin")
        self.rol = current.get("rol", "ADMIN").upper()
        self.modo_vista = "cajero"
        self.datos_actuales = {}
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setObjectName("CierreGlobalRoot")
        self.setStyleSheet("QWidget#CierreGlobalRoot { background: #F8FAFC; }") # Claro/Blanco
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── HEADER ESTILO PASO 7 CON CONTROLES DE DASHBOARD ───
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background: #1E3A8A;") # Azul oscuro
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(30, 0, 30, 0)
        h_lay.setSpacing(15)
        
        self.btn_back = QPushButton("← Volver")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet("color: white; background: transparent; border: 1px solid white; border-radius: 8px; padding: 5px 15px; font-weight: bold;")
        self.btn_back.clicked.connect(self.request_dashboard.emit)
        h_lay.addWidget(self.btn_back)
        
        lbl_tit = QLabel("💎 CAJAFACIL PRO - CONTROL DE CIERRE")
        lbl_tit.setStyleSheet("color: white; font-size: 20px; font-weight: 900;")
        h_lay.addWidget(lbl_tit)
        
        h_lay.addStretch()
        
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setDisplayFormat("dd/MM/yyyy")
        self.date_picker.setFixedWidth(130)
        self.date_picker.setStyleSheet("font-size: 14px; padding: 5px; background: white; color: black; border-radius: 5px;")
        self.date_picker.dateChanged.connect(self._load_data)
        h_lay.addWidget(self.date_picker)

        self.btn_ayer = QPushButton("Ayer")
        self.btn_ayer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ayer.setToolTip("Ver cortes registrados de ayer por cajero")
        self.btn_ayer.setStyleSheet(
            "background: #F8FAFC; color: #1E3A8A; border: none; border-radius: 5px; "
            "padding: 8px 12px; font-weight: bold;"
        )
        self.btn_ayer.clicked.connect(self._ir_a_ayer)
        h_lay.addWidget(self.btn_ayer)
        if self.is_terminal or self.rol not in ("ADMIN", "JEFE"):
            self.btn_ayer.hide()
            self.date_picker.hide()

        self.btn_corte_cajero = QPushButton("👤 Corte Cajero")
        self.btn_corte_cajero.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_corte_cajero.setStyleSheet("background: #3B82F6; color: white; border: none; border-radius: 5px; padding: 8px 15px; font-weight: bold;")
        self.btn_corte_cajero.clicked.connect(lambda: self._cambiar_modo("cajero"))
        h_lay.addWidget(self.btn_corte_cajero)

        self.btn_corte_admin = QPushButton("🏢 Corte Admin")
        self.btn_corte_admin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_corte_admin.setStyleSheet("background: #10B981; color: white; border: none; border-radius: 5px; padding: 8px 15px; font-weight: bold;")
        self.btn_corte_admin.clicked.connect(lambda: self._cambiar_modo("dia"))
        h_lay.addWidget(self.btn_corte_admin)

        self.combo_caja = QComboBox()
        self.combo_caja.addItem("Todas (consolidado)", None)
        try:
            for cid in MotorCierre.listar_cajas():
                self.combo_caja.addItem(f"Caja {cid}", cid)
        except Exception:
            for i in range(1, 6):
                self.combo_caja.addItem(f"Caja {i}", i)
        self.combo_caja.setStyleSheet("font-size: 14px; padding: 5px; background: white; color: black; border-radius: 5px;")
        self.combo_caja.currentIndexChanged.connect(self._load_data)
        self.combo_caja.setToolTip(
            "Consolidado = solo lectura (estilo cadena).\n"
            "Para arqueo/corte Z elegí una caja concreta."
        )

        if self.rol not in ["ADMIN", "JEFE"] or self.is_terminal:
            self.combo_caja.hide()
            self.btn_corte_admin.hide()

        h_lay.addWidget(self.combo_caja)
        
        self.btn_imprimir = QPushButton("🖨️")
        self.btn_imprimir.setToolTip("Imprimir Reporte")
        self.btn_imprimir.setStyleSheet("background: white; color: #1E3A8A; border: none; border-radius: 5px; padding: 8px 12px; font-size: 16px;")
        self.btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir.clicked.connect(self._imprimir_reporte)
        h_lay.addWidget(self.btn_imprimir)
        
        root.addWidget(header)

        # ─── MAIN BODY ───
        body = QHBoxLayout()
        body.setContentsMargins(24, 16, 24, 16)
        body.setSpacing(20)

        # Izquierda: Métricas
        v_met = QVBoxLayout()
        v_met.setSpacing(10)
        
        self.card_efec = ClickableMetricCard("Ventas Efectivo", "💰", "#10B981")
        self.card_efec.setToolTip("Click para ver detalles")
        self.card_efec.clicked.connect(lambda: self._mostrar_detalles("Ventas Efectivo", [
            ("Ventas Directas en Efectivo", self.datos_actuales.get("v_efectivo", 0), False),
            ("Abonos en Efectivo", self.datos_actuales.get("abonos_efectivo", 0), False),
            ("Devoluciones Efectivo", self.datos_actuales.get("devoluciones_efectivo", 0), True)
        ]))
        
        self.card_tarj = ClickableMetricCard("Ventas Digital", "💳", "#3B82F6")
        self.card_tarj.setToolTip("Click para ver detalles")
        self.card_tarj.clicked.connect(lambda: self._mostrar_detalles("Ventas Digital (Desglose)", [
            ("Tarjetas de Crédito/Débito", self.datos_actuales.get("v_tarjeta", 0), False),
            ("Transferencias / QR", self.datos_actuales.get("v_trans", 0), False),
            ("Vales de Despensa", self.datos_actuales.get("v_vales", 0), False),
            ("Cheques", self.datos_actuales.get("v_cheque", 0), False)
        ]))
        
        self.card_fiado = ClickableMetricCard("Ventas a Fiado", "👥", "#F59E0B")
        self.card_fiado.setToolTip("Click para ver detalles")
        self.card_fiado.clicked.connect(lambda: self._mostrar_detalles("Ventas a Crédito (Fiado)", [
            ("Crédito Otorgado (A cobrar)", self.datos_actuales.get("v_credito", 0), False)
        ]))
        
        self.card_fondo = ClickableMetricCard("Fondo Apertura", "🏁", "#6366F1")
        self.card_fondo.setToolTip("Dinero inicial en caja")
        
        self.card_movs = ClickableMetricCard("Movimientos Extra", "↔️", "#8B5CF6")
        self.card_movs.setToolTip("Click para ver entradas y salidas")
        self.card_movs.clicked.connect(lambda: self._mostrar_detalles("Entradas y Salidas de Caja", [
            ("Entradas Manuales", self.datos_actuales.get("entradas_efectivo", 0), False),
            ("Salidas Manuales", self.datos_actuales.get("salidas_efectivo", 0), True)
        ]))
        
        self.card_totales = ClickableMetricCard("Ganancia Estimada", "📈", "#14B8A6")
        self.card_totales.setToolTip("Click para ver resumen neto")
        self.card_totales.clicked.connect(lambda: self._mostrar_detalles("Resumen del Turno", [
            ("Ventas Totales Brutas", self.datos_actuales.get("v_totales", 0), False),
            ("Ganancia Estimada (Neto)", self.datos_actuales.get("ganancia_estimada", 0), False)
        ]))
        
        cards = [self.card_efec, self.card_tarj, self.card_fiado, self.card_fondo, self.card_movs]
        if self.rol == "JEFE":
            cards.append(self.card_totales)
        else:
            self.card_totales.hide()
            
        for c in cards:
            v_met.addWidget(c)
        v_met.addStretch(1)

        body.addLayout(v_met, 3)

        # Derecha: tablas (compactas) + arqueo (prioridad de espacio)
        v_arq = QVBoxLayout()
        v_arq.setSpacing(10)

        self.panel_arq = PanelArqueo(self)
        self.panel_arq.setStyleSheet("""
            QFrame#PanelArq {
                background: white; border: 1px solid #E2E8F0; border-radius: 16px;
            }
            QLabel#PanelArqTitEsp {
                font-weight: 900; font-size: 15px; color: #475569;
            }
            QLabel#PanelArqValEsp {
                font-weight: 900; font-size: 36px; color: #3B82F6;
                background: #EFF6FF; border-radius: 12px;
                padding: 14px 12px; min-height: 72px;
            }
            QLabel#PanelArqTitFis {
                font-weight: 900; font-size: 13px; color: #475569; margin-top: 4px;
            }
            QLineEdit#PanelArqValFis {
                font-weight: 900; font-size: 30px; color: #1E40AF;
                border: 2px solid #60A5FA; border-radius: 12px;
                padding: 10px 12px; min-height: 56px;
            }
            QLineEdit#PanelArqValFis:focus { border: 3px solid #2563EB; }

            QFrame#FrameDif { border: 2px solid #E2E8F0; border-radius: 12px; margin-top: 4px; }
            QFrame#FrameDif[estado="sobrante"] { border-color: #10B981; background: #ECFDF5; }
            QFrame#FrameDif[estado="faltante"] { border-color: #EF4444; background: #FEF2F2; }
            QFrame#FrameDif[estado="sos"] { border-color: #B91C1C; background: #FCA5A5; }

            QLabel#FrameDifTit { font-weight: 900; font-size: 16px; color: #334155; }
            QLabel#FrameDifVal { font-weight: 900; font-size: 20px; }
            QFrame#FrameDif[estado="sobrante"] QLabel#FrameDifVal { color: #047857; }
            QFrame#FrameDif[estado="faltante"] QLabel#FrameDifVal { color: #B91C1C; }
            QFrame#FrameDif[estado="sos"] QLabel#FrameDifVal { color: white; }
        """)

        self.lbl_multi_hint = QLabel("")
        self.lbl_multi_hint.setWordWrap(True)
        self.lbl_multi_hint.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #9A3412; background: #FFF7ED; "
            "border: 1px solid #FDBA74; border-radius: 8px; padding: 8px 10px;"
        )
        self.lbl_multi_hint.hide()

        _tbl_css = (
            "QTableWidget { background: white; border: 1px solid #E2E8F0; border-radius: 8px; "
            "font-size: 12px; color: #0F172A; gridline-color: #E2E8F0; } "
            "QTableWidget::item { padding: 6px 8px; } "
            "QHeaderView::section { background: #F1F5F9; font-weight: 800; padding: 8px; "
            "border: none; border-right: 1px solid #E2E8F0; }"
        )

        self.tabla_cajas = QTableWidget(0, 5)
        self.tabla_cajas.setHorizontalHeaderLabels(
            ["Caja", "Estado", "Cajero", "Ventas", "Efectivo esp."]
        )
        self.tabla_cajas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_cajas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_cajas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_cajas.setMinimumHeight(72)
        self.tabla_cajas.setMaximumHeight(130)
        self.tabla_cajas.verticalHeader().setVisible(False)
        self.tabla_cajas.setShowGrid(False)
        self.tabla_cajas.setStyleSheet(_tbl_css)
        self.tabla_cajas.hide()
        self.tabla_cajas.cellDoubleClicked.connect(self._on_tabla_caja_dbl)

        self.lbl_hist = QLabel("Cortes registrados del día (por cajero)")
        self.lbl_hist.setStyleSheet("font-size: 13px; font-weight: 900; color: #334155;")
        self.tabla_hist = QTableWidget(0, 7)
        self.tabla_hist.setHorizontalHeaderLabels(
            ["Hora", "Cajero", "Caja", "Tipo", "Físico", "Esperado", "Dif."]
        )
        self.tabla_hist.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_hist.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_hist.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_hist.setMinimumHeight(72)
        self.tabla_hist.setMaximumHeight(140)
        self.tabla_hist.verticalHeader().setVisible(False)
        self.tabla_hist.setShowGrid(False)
        self.tabla_hist.setStyleSheet(
            _tbl_css.replace("#F1F5F9", "#EEF2FF")
        )
        self.tabla_hist.cellDoubleClicked.connect(self._on_hist_dbl)

        # Historial de cortes: solo admin/jefe (no en terminal / perfil cajero)
        self._hist_visible = (
            not self.is_terminal and self.rol in ("ADMIN", "JEFE")
        )
        if not self._hist_visible:
            self.lbl_hist.hide()
            self.tabla_hist.hide()

        v_arq.addWidget(self.lbl_multi_hint, 0)
        v_arq.addWidget(self.tabla_cajas, 0)
        v_arq.addWidget(self.lbl_hist, 0)
        v_arq.addWidget(self.tabla_hist, 0)
        v_arq.addWidget(self.panel_arq, 1)
        body.addLayout(v_arq, 7)
        
        root.addLayout(body)

        # ─── FOOTER ───
        footer = QFrame()
        footer.setFixedHeight(90)
        footer.setStyleSheet("background: #1E3A8A;")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(30, 0, 30, 0)
        
        self.lbl_modo_activo = QLabel("")
        self.lbl_modo_activo.setStyleSheet("color: white; font-size: 16px;")
        f_lay.addWidget(self.lbl_modo_activo)
        
        f_lay.addStretch()
        
        self.btn_cierre = QPushButton("🏁 FINALIZAR CORTE CAJERO")
        self.btn_cierre.setFixedSize(340, 55)
        self.btn_cierre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cierre.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white; font-weight: 900; font-size: 17px;
                border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_cierre.clicked.connect(self._on_click_finalizar)
        f_lay.addWidget(self.btn_cierre)
        self._actualizar_texto_boton_cierre()
        
        root.addWidget(footer)
        
        QTimer.singleShot(100, self.panel_arq.focus_fisico)

    def _mostrar_detalles(self, titulo, items):
        dlg = DetallesDialog(titulo, items, self)
        dlg.exec()

    def _cambiar_modo(self, modo):
        self.modo_vista = normalizar_modo(modo)
        self._actualizar_texto_boton_cierre()
        self._load_data()

    def _actualizar_texto_boton_cierre(self):
        if normalizar_modo(self.modo_vista) == "dia":
            self.btn_cierre.setText("🏁 FINALIZAR CORTE DEL DÍA")
        else:
            self.btn_cierre.setText("🏁 FINALIZAR CORTE CAJERO")

    def _on_click_finalizar(self):
        self._realizar_corte(self.modo_vista)

    def _ir_a_ayer(self):
        self.date_picker.setDate(QDate.currentDate().addDays(-1))

    def _caja_id_para_corte(self):
        if self.modo_vista == "cajero" or self.is_terminal:
            return config.get("caja_id", 1)
        return self.combo_caja.currentData()

    def _cargar_historial_cortes(self, fecha_str: str):
        """Tabla de cortes ya hechos ese día (solo admin/jefe)."""
        if not getattr(self, "_hist_visible", False):
            self.lbl_hist.hide()
            self.tabla_hist.hide()
            return
        try:
            self.lbl_hist.show()
            self.tabla_hist.show()
            caja_sel = None
            if self.combo_caja.currentData() is not None:
                caja_sel = self.combo_caja.currentData()

            if self.modo_vista == "dia" and caja_sel is None:
                cortes = MotorCierre.listar_cortes_del_dia(fecha_str=fecha_str)
            else:
                cortes = MotorCierre.listar_cortes_del_dia(
                    fecha_str=fecha_str, caja_id=caja_sel
                )

            self.tabla_hist.setRowCount(len(cortes))
            es_hoy = fecha_str == QDate.currentDate().toString("yyyy-MM-dd")
            self.lbl_hist.setText(
                f"Cortes registrados — {fecha_str}"
                + (" (hoy)" if es_hoy else "")
                + f" · {len(cortes)} registro(s)"
            )
            for i, c in enumerate(cortes):
                dif = c.get("diferencia")
                dif_s = fmt_moneda(dif) if dif is not None else "—"
                esp = c.get("esperado")
                esp_s = fmt_moneda(esp) if esp is not None else "—"
                vals = [
                    c.get("hora") or "",
                    c.get("usuario") or "—",
                    f"Caja {c.get('caja_id')}",
                    c.get("tipo_label") or "",
                    fmt_moneda(c.get("fisico", 0)),
                    esp_s,
                    dif_s,
                ]
                for col, text in enumerate(vals):
                    it = QTableWidgetItem(str(text))
                    it.setData(Qt.ItemDataRole.UserRole, c)
                    self.tabla_hist.setItem(i, col, it)
        except Exception as e:
            print(f"Error historial cortes: {e}")
            self.tabla_hist.setRowCount(0)

    def _on_hist_dbl(self, row, _col):
        """Detalle de un corte histórico."""
        try:
            it = self.tabla_hist.item(row, 0)
            c = it.data(Qt.ItemDataRole.UserRole) if it else None
            if not isinstance(c, dict):
                return
            dlg_items = [
                (f"Tipo: {c.get('tipo_label')} · {c.get('fecha')}", 0, False),
                ("Físico contado", float(c.get("fisico") or 0), False),
            ]
            if c.get("esperado") is not None:
                dlg_items.append(("Esperado", float(c["esperado"]), False))
            if c.get("diferencia") is not None:
                d = float(c["diferencia"])
                dlg_items.append(("Diferencia", abs(d), d < 0))
            if c.get("total_ventas") is not None:
                dlg_items.append(("Total ventas", float(c["total_ventas"]), False))
            self._mostrar_detalles(
                f"Corte · {c.get('usuario')} · Caja {c.get('caja_id')}",
                dlg_items,
            )
        except Exception as e:
            print(e)

    def _on_tabla_caja_dbl(self, row, _col):
        """Doble clic en consolidado → selecciona esa caja para arqueo."""
        try:
            item = self.tabla_cajas.item(row, 0)
            if not item:
                return
            cid = int(item.data(Qt.ItemDataRole.UserRole) or 0)
            if cid <= 0:
                return
            idx = self.combo_caja.findData(cid)
            if idx >= 0:
                self.combo_caja.setCurrentIndex(idx)
        except Exception:
            pass

    def _set_modo_consolidado(self, activo: bool, datos: dict | None = None):
        """Consolidado multi-caja: métricas sí, arqueo/cierre no (regla cadena)."""
        if activo:
            self.lbl_multi_hint.setText(
                "Vista consolidada de tienda (multi-caja).\n"
                f"Abiertas: {datos.get('cajas_abiertas', 0) if datos else 0} · "
                f"Cerradas: {datos.get('cajas_cerradas', 0) if datos else 0}.\n"
                "Elegí una caja en el combo (o doble clic en la tabla) para arqueo y corte Z."
            )
            self.lbl_multi_hint.show()
            self.tabla_cajas.show()
            self.panel_arq.setEnabled(False)
            self.btn_cierre.setEnabled(False)
            self.btn_cierre.setText("⚠ Elegí una caja para cortar")
            filas = (datos or {}).get("por_caja") or []
            self.tabla_cajas.setRowCount(len(filas))
            for i, f in enumerate(filas):
                c0 = QTableWidgetItem(f"Caja {f.get('caja_id')}")
                c0.setData(Qt.ItemDataRole.UserRole, f.get("caja_id"))
                c1 = QTableWidgetItem(str(f.get("estado") or ""))
                c2 = QTableWidgetItem(str(f.get("usuario") or "—"))
                c3 = QTableWidgetItem(fmt_moneda(f.get("v_totales", 0)))
                c4 = QTableWidgetItem(fmt_moneda(f.get("v_caja_total", 0)))
                for col, it in enumerate((c0, c1, c2, c3, c4)):
                    self.tabla_cajas.setItem(i, col, it)
        else:
            self.lbl_multi_hint.hide()
            self.tabla_cajas.hide()
            self.tabla_cajas.setRowCount(0)
            self.panel_arq.setEnabled(True)
            self.btn_cierre.setEnabled(True)
            self._actualizar_texto_boton_cierre()

    def _load_data(self):
        try:
            fecha_str = self.date_picker.date().toString("yyyy-MM-dd")
            caja_id_filter = None
            cajero_filter = None
            modo_text = "Todos los cajeros"
            consolidado = False

            if self.modo_vista == "cajero":
                cajero_filter = self.user
                caja_id_filter = config.get("caja_id", 1)
                modo_text = f"Turno de {self.user.capitalize()} · Caja {caja_id_filter}"
            else:
                caja_sel = self.combo_caja.currentData()
                if caja_sel is not None:
                    caja_id_filter = caja_sel
                    modo_text = f"Corte Z · {self.combo_caja.currentText()}"
                else:
                    consolidado = True
                    modo_text = "Consolidado multi-caja (solo lectura)"

            fecha_display = self.date_picker.date().toString("dd MMM yyyy")
            self.lbl_modo_activo.setText(f"Mostrando: <b>{modo_text}</b> | {fecha_display}")

            datos = MotorCierre.obtener_datos_cierre_diario(
                fecha_str=fecha_str, cajero=cajero_filter, caja_id=caja_id_filter
            )
            self.datos_actuales = datos

            self.card_efec.revelar(datos.get("v_efectivo", 0))
            v_digital = (
                datos.get("v_tarjeta", 0)
                + datos.get("v_trans", 0)
                + datos.get("v_vales", 0)
                + datos.get("v_cheque", 0)
            )
            self.card_tarj.revelar(v_digital)
            self.card_fiado.revelar(datos.get("v_credito", 0))
            self.card_fondo.revelar(datos.get("fondo", 0))

            movs = datos.get("entradas_efectivo", 0) - datos.get("salidas_efectivo", 0)
            self.card_movs.revelar(movs)

            self.card_totales.revelar(datos.get("ganancia_estimada", 0))
            self.panel_arq.set_esperado(datos.get("v_caja_total", 0))

            self._set_modo_consolidado(consolidado or bool(datos.get("multi_caja")), datos)
            self._cargar_historial_cortes(fecha_str)

            # Fecha pasada: solo consulta (no cortar el pasado)
            es_hoy = fecha_str == QDate.currentDate().toString("yyyy-MM-dd")
            if not es_hoy and not consolidado:
                self.panel_arq.setEnabled(False)
                self.btn_cierre.setEnabled(False)
                self.btn_cierre.setText("📅 Solo historial (fecha pasada)")
            elif es_hoy and not consolidado:
                self.panel_arq.setEnabled(True)
                self.btn_cierre.setEnabled(True)
                self._actualizar_texto_boton_cierre()

        except Exception as e:
            print(f"Error cargando datos de corte: {e}")

    def _imprimir_reporte(self, quiet: bool = False):
        try:
            from src.hardware.printer import printer_manager

            d = self.datos_actuales or {}
            fisico, dif = self.panel_arq.get_fisico_y_dif()
            modo_print = "turno" if normalizar_modo(self.modo_vista) == "cajero" else "dia"
            datos_z = {
                "fondo": d.get("fondo", 0),
                "turno_efectivo": d.get("v_efectivo", 0),
                "turno_tarjeta": d.get("v_tarjeta", 0) + d.get("v_trans", 0),
                "turno_total": d.get("v_totales", 0),
                "dia_tarjeta": d.get("v_tarjeta", 0) + d.get("v_trans", 0),
                "dia_total": d.get("v_totales", 0),
                "efectivo_esperado": self.panel_arq.esperado,
                "esperado": self.panel_arq.esperado,
                "modo": modo_print,
            }
            ok = printer_manager.imprimir_ticket_z(self.user, fisico, dif, datos_z)
            if quiet:
                return bool(ok)
            if ok is False:
                QMessageBox.warning(
                    self,
                    "Impresora",
                    "No se pudo imprimir el ticket Z.\nRevisá la impresora; el corte se puede hacer igual.",
                )
            else:
                QMessageBox.information(self, "Imprimir", "Ticket de cierre enviado a la impresora.")
        except Exception as e:
            if quiet:
                return False
            QMessageBox.warning(self, "Impresora", f"No se pudo imprimir:\n{e}")
            return False
        return True

    def _realizar_corte(self, modo="cajero"):
        modo_n = normalizar_modo(modo)
        caja_id = self._caja_id_para_corte()
        if caja_id is None:
            QMessageBox.warning(
                self,
                "Multi-caja",
                "En modo cadena el corte se hace por caja.\n\n"
                "Elegí una caja en el combo (o doble clic en la tabla consolidada)\n"
                "e ingresá el efectivo físico de esa terminal.",
            )
            return

        esperado = self.panel_arq.esperado
        fisico, dif = self.panel_arq.get_fisico_y_dif()
        etiqueta = etiqueta_modo(modo_n)

        msg = (
            f"¿Confirmar {etiqueta} — Caja {caja_id}?\n\n"
            f"Esperado: ${esperado:,.2f}\n"
            f"Físico: ${fisico:,.2f}\n"
            f"Diferencia: ${dif:,.2f}"
        )
        res = QMessageBox.question(
            self,
            "Confirmar Cierre",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if res != QMessageBox.StandardButton.Yes:
            return
        try:
            exito = MotorCierre.cerrar_caja(
                username=self.user,
                caja_id=caja_id,
                fisico=fisico,
                dif=dif,
                esperado=esperado,
                t_total=self.datos_actuales.get("v_totales", 0.0),
                modo=modo_n,
            )
            if exito:
                try:
                    self._imprimir_reporte(quiet=True)
                except Exception:
                    pass
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"{etiqueta.capitalize()} registrado. Las ventas del turno quedaron cerradas.",
                )
                self.turno_cerrado.emit()
                if self.is_terminal:
                    pass
                else:
                    # Admin multi-caja: quedarse para cortar la siguiente terminal
                    try:
                        self.combo_caja.setCurrentIndex(0)
                    except Exception:
                        pass
                    self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
