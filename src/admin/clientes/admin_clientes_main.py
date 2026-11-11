from src.utils.qt_compat import qt_exec
from datetime import datetime
from src.logger import logger
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QMessageBox, QMenu, QToolButton,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QCursor, QAction
from src.repositories.cliente_repository import FIADO_EXPRESS_LIMITE_DEFAULT

from src.admin.clientes.theme import _CLI
from src.utils.letra import QSS_TITULO, vestir_id, vestir_nombre, vestir_numero

from src.admin.clientes.componentes.metric_card import MetricCard
from src.admin.clientes.componentes.dialogo_nuevo_cliente import DialogoNuevoCliente
from src.admin.clientes.componentes.dialogo_editar_cliente import DialogoEditarCliente
from src.admin.clientes.componentes.dialogo_historial_cliente import DialogoHistorialCliente
from src.admin.clientes.componentes.dialogo_cobros import DialogoCobros
from src.admin.clientes.componentes.dialogo_cuadre import DialogoCuadre

# Columnas: ID DNI Nombre Tipo Estado Deuda Mantenimiento Días Tarifa Acciones
_SORT_COLS = {0: "id", 1: "dni", 2: "nombre", 5: "deuda", 6: "mantenimiento", 7: "dias"}
_CRITICOS_DIAS = 30
_COL_ACCIONES = 9


class AdminClientes(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._filtro = "todos"
        self._cache_todas = []
        self._cache_query = None
        self._cache_fechas = {}
        self._cache_pagos = {}
        self._cache_movs = {}
        self._cache_intereses = {}
        self._mayor_id = None
        self._sort_key = "deuda"
        self._sort_asc = False
        self._timer_busqueda = QTimer(self)
        self._timer_busqueda.setSingleShot(True)
        self._timer_busqueda.setInterval(280)
        self._timer_busqueda.timeout.connect(lambda: self.cargar_clientes(forzar=True))
        self.initUI()

    def initUI(self):
        self.setStyleSheet(f"background: {_CLI['bg']};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)

        header_lay = QHBoxLayout()

        btn_back = QPushButton("VOLVER AL PANEL")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: white; color: {_CLI['text']}; font-weight: 800; border-radius: 10px;
                padding: 10px 20px; border: 1px solid {_CLI['border']}; font-size: 12px; letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: {_CLI['accent_light']}; color: {_CLI['accent']}; border-color: #BFDBFE; }}
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)

        header_lay.addWidget(btn_back)
        header_lay.addSpacing(15)

        tit_box = QVBoxLayout()
        tit_box.setSpacing(2)
        lbl_titulo = QLabel("CARTERA DE CLIENTES Y CRÉDITO")
        lbl_titulo.setStyleSheet(
            f"{QSS_TITULO} color: {_CLI['text']}; border: none;"
        )
        self.lbl_subtitulo = QLabel("Crédito barrial · interés simple por ticket")
        self.lbl_subtitulo.setStyleSheet(
            f"color: {_CLI['text_sec']}; font-size: 12px; font-weight: 700; border: none;"
        )
        tit_box.addWidget(lbl_titulo)
        tit_box.addWidget(self.lbl_subtitulo)
        header_lay.addLayout(tit_box)
        header_lay.addSpacing(12)

        self.lbl_politica = QLabel("")
        self.lbl_politica.setStyleSheet(
            "background: #EEF2FF; color: #3730A3; border: 1px solid #C7D2FE; "
            "border-radius: 8px; padding: 6px 12px; font-size: 11px; font-weight: 800;"
        )
        header_lay.addWidget(self.lbl_politica)

        self.btn_nuevo = QPushButton("+ NUEVO CLIENTE")
        self.btn_nuevo.setCursor(Qt.PointingHandCursor)
        self.btn_nuevo.setStyleSheet(f"""
            QPushButton {{
                background: {_CLI['accent']};
                color: white; padding: 12px 24px; font-weight: 900; border-radius: 10px; font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{ background: {_CLI['accent_hover']}; }}
        """)
        self.btn_nuevo.clicked.connect(self.nuevo_cliente)

        from src.central_red_global.motor_red import MotorRed
        motor_red = MotorRed()
        st = motor_red.obtener_estado_red()
        if st.get("is_master", True):
            badge_txt = "🖥️ BD Maestra (Servidor)"
            badge_css = "background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; font-size: 11px; font-weight: bold; border-radius: 8px; padding: 5px 12px;"
        else:
            host_ip = st.get("db_host", "LAN")
            badge_txt = f"⚡ Sincronizado en Tiempo Real con Maestra ({host_ip})"
            badge_css = "background: #DBEAFE; color: #1E40AF; border: 1px solid #BFDBFE; font-size: 11px; font-weight: bold; border-radius: 8px; padding: 5px 12px;"

        self.lbl_red_status = QLabel(badge_txt)
        self.lbl_red_status.setStyleSheet(badge_css)
        header_lay.addWidget(self.lbl_red_status)

        self.btn_auditoria = QPushButton("AUDITORÍA")
        self.btn_auditoria.setCursor(Qt.PointingHandCursor)
        self.btn_auditoria.setToolTip("Quién creó o cambió cada cliente, en qué PC y cuándo")
        self.btn_auditoria.setStyleSheet("""
            QPushButton {
                background: white; color: #1E40AF; font-weight: 900; border-radius: 10px;
                padding: 12px 18px; border: 1px solid #BFDBFE; font-size: 13px;
            }
            QPushButton:hover { background: #EFF6FF; }
        """)
        self.btn_auditoria.clicked.connect(self._abrir_auditoria)

        self.btn_planillas = QToolButton()
        self.btn_planillas.setText("PLANILLAS  ▾")
        self.btn_planillas.setCursor(Qt.PointingHandCursor)
        self.btn_planillas.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_planillas.setStyleSheet("""
            QToolButton {
                background: white; color: #0F172A; font-weight: 900; border-radius: 10px;
                padding: 12px 18px; border: 1px solid #CBD5E1; font-size: 13px;
            }
            QToolButton::menu-indicator { image: none; width: 0; }
            QToolButton:hover { background: #F8FAFC; border-color: #94A3B8; }
        """)
        menu_p = QMenu(self.btn_planillas)
        menu_p.setStyleSheet(
            "QMenu { background: white; border: 1px solid #CBD5E1; padding: 6px; }"
            "QMenu::item { padding: 10px 20px; font-weight: 800; color: #0F172A; }"
            "QMenu::item:selected { background: #EFF6FF; color: #1D4ED8; }"
        )
        act_cobros = QAction("Planilla de cobros (abonos)", menu_p)
        act_cobros.triggered.connect(self._abrir_cobros)
        act_cargos = QAction("Planilla de cargos (deuda)", menu_p)
        act_cargos.triggered.connect(self._abrir_cargos)
        menu_p.addAction(act_cobros)
        menu_p.addAction(act_cargos)
        self.btn_planillas.setMenu(menu_p)

        self.btn_tuerca = QPushButton("⚙")
        self.btn_tuerca.setCursor(Qt.PointingHandCursor)
        self.btn_tuerca.setFixedSize(46, 46)
        self.btn_tuerca.setToolTip("Ver cómo se calcula el interés mensual por ticket")
        self.btn_tuerca.setStyleSheet("""
            QPushButton {
                background: white; color: #3730A3; font-weight: 900; border-radius: 10px;
                border: 1px solid #C7D2FE; font-size: 18px;
            }
            QPushButton:hover { background: #EEF2FF; border-color: #A5B4FC; }
        """)
        self.btn_tuerca.clicked.connect(self._abrir_politicas)

        header_lay.addStretch()
        header_lay.addWidget(self.btn_auditoria)
        header_lay.addSpacing(8)
        header_lay.addWidget(self.btn_planillas)
        header_lay.addSpacing(10)
        header_lay.addWidget(self.btn_tuerca)
        header_lay.addSpacing(8)
        header_lay.addWidget(self.btn_nuevo)
        lay.addLayout(header_lay)
        self._refrescar_chip_politica()

        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(16)
        self.card_deuda = MetricCard(
            "Cartera en la calle", "", "#059669",
            hint="Clic: ver clientes con crédito activo",
        )
        self.card_activos = MetricCard(
            "Cuentas activas", "", "#2563EB",
            hint="Clic: filtrar cuentas con crédito",
        )
        self.card_mayor = MetricCard(
            "Cartera en riesgo", "", "#DC2626",
            hint="Clic: ver cuentas críticas (mora +30d o excedidas)",
        )
        self.card_cobros = MetricCard(
            "Cobros del mes", "", "#0D9488",
            hint="Clic: abrir planilla de cobros",
        )
        self.card_deuda.clicked.connect(lambda: self._kpi_filtro("deuda"))
        self.card_activos.clicked.connect(lambda: self._kpi_filtro("deuda"))
        self.card_mayor.clicked.connect(self._kpi_mayor)
        self.card_cobros.clicked.connect(self._abrir_cobros)
        cards_lay.addWidget(self.card_deuda)
        cards_lay.addWidget(self.card_activos)
        cards_lay.addWidget(self.card_mayor)
        cards_lay.addWidget(self.card_cobros)
        lay.addLayout(cards_lay)

        self.aviso_cuadre = QFrame()
        self.aviso_cuadre.setStyleSheet(
            "background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 12px;"
        )
        aviso_lay = QHBoxLayout(self.aviso_cuadre)
        aviso_lay.setContentsMargins(16, 10, 16, 10)
        self.lbl_cuadre = QLabel("")
        self.lbl_cuadre.setStyleSheet(
            "color: #92400E; font-weight: 800; font-size: 13px; background: transparent; border: none;"
        )
        self.btn_cuadre = QPushButton("CUADRAR")
        self.btn_cuadre.setCursor(Qt.PointingHandCursor)
        self.btn_cuadre.setStyleSheet(
            "background: #B45309; color: white; font-weight: 900; border: none; "
            "border-radius: 8px; padding: 8px 14px;"
        )
        self.btn_cuadre.clicked.connect(self._abrir_cuadre)
        aviso_lay.addWidget(self.lbl_cuadre)
        aviso_lay.addStretch()
        aviso_lay.addWidget(self.btn_cuadre)
        self.aviso_cuadre.hide()
        lay.addWidget(self.aviso_cuadre)

        panel_tabla = QFrame()
        panel_tabla.setStyleSheet(
            f"background: {_CLI['card']}; border: 1px solid {_CLI['border']}; border-radius: 18px;"
        )
        pt_lay = QVBoxLayout(panel_tabla)
        pt_lay.setContentsMargins(20, 20, 20, 20)

        bus_row = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre o DNI...")
        self.txt_buscar.setStyleSheet(f"""
            QLineEdit {{
                padding: 14px 16px; border: 1px solid {_CLI['border']}; border-radius: 10px;
                font-size: 14px; background: {_CLI['row_alt']}; color: {_CLI['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {_CLI['accent']}; background: white;
            }}
        """)
        self.txt_buscar.textChanged.connect(self._on_buscar_cambiado)
        bus_row.addWidget(self.txt_buscar, 1)

        self.lbl_estado = QLabel("")
        self.lbl_estado.setStyleSheet(
            f"color: {_CLI['text_sec']}; font-size: 12px; font-weight: 700; border: none; padding-left: 8px;"
        )
        bus_row.addWidget(self.lbl_estado)
        pt_lay.addLayout(bus_row)

        from PyQt6.QtWidgets import QButtonGroup
        self._chips = {}
        chips_lay = QHBoxLayout()
        chips_lay.setSpacing(6)
        chips_lay.setContentsMargins(0, 6, 0, 2)
        grupo = QButtonGroup(self)
        grupo.setExclusive(True)

        def _add_chip(clave, color, tip=""):
            chip = QPushButton()
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setStyleSheet(f"""
                QPushButton {{
                    background: white; color: {color}; border: 1px solid {_CLI['border']};
                    border-radius: 14px; padding: 5px 11px; font-weight: 800; font-size: 11px;
                }}
                QPushButton:hover {{ border-color: {color}; }}
                QPushButton:checked {{ background: {color}; color: white; border-color: {color}; }}
            """)
            chip.clicked.connect(lambda _=False, c=clave: self._elegir_filtro(c))
            if tip:
                chip.setToolTip(tip)
            grupo.addButton(chip)
            chips_lay.addWidget(chip)
            self._chips[clave] = chip

        for clave, color in (
            ("todos", "#334155"),
            ("deuda", "#059669"),
            ("al_dia", "#0284C7"),
            ("favor", "#2563EB"),
            ("express", "#D97706"),
        ):
            _add_chip(clave, color)

        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(22)
        sep.setStyleSheet(f"background: {_CLI['border']}; border: none;")
        chips_lay.addWidget(sep)

        _add_chip("criticos", "#7C2D12", f"Deuda y más de {_CRITICOS_DIAS} días sin pago")
        _add_chip("d30", "#B45309", "Deuda y más de 30 días desde el último pago")
        _add_chip("d60", "#C2410C", "Deuda y más de 60 días")
        _add_chip("d90", "#9A3412", "Deuda y más de 90 días")
        _add_chip("promesa", "#7C3AED", "Promesa de pago vencida")

        self._chips["todos"].setChecked(True)
        chips_lay.addStretch()
        pt_lay.addLayout(chips_lay)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(10)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "DNI", "Nombre", "Tipo", "Estado", "Deuda", "Mantenimiento",
            "Días", "Tarifa", "Acciones",
        ])
        for c in range(10):
            self.tabla.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.Interactive)
        self.tabla.horizontalHeader().setSectionResizeMode(_COL_ACCIONES, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(_COL_ACCIONES, 136)
        orig_tbl_resize = self.tabla.resizeEvent
        def _tbl_resize(ev):
            orig_tbl_resize(ev)
            self._ajustar_columnas()
        self.tabla.resizeEvent = _tbl_resize
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(54)
        self.tabla.horizontalHeader().setMinimumHeight(48)
        self.tabla.horizontalHeader().setSectionsClickable(True)
        self.tabla.horizontalHeader().setSortIndicatorShown(True)
        self.tabla.horizontalHeader().sectionClicked.connect(self._ordenar_por_columna)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                border: none; font-size: 13px; gridline-color: transparent;
                background: white; alternate-background-color: {_CLI['row_alt']};
                color: {_CLI['text']};
            }}
            QHeaderView::section {{
                font-weight: 900; border: none; padding: 8px 10px;
                background: {_CLI['header_bg']}; color: #334155; font-size: 12px;
                border-bottom: 2px solid {_CLI['accent']};
            }}
            QTableWidget::item {{ padding: 8px 10px; }}
            QTableWidget::item:selected {{ background: {_CLI['accent_light']}; color: #1E40AF; }}
        """)
        self.tabla.setToolTip("Clic en una fila para ver el historial · Clic en el encabezado para ordenar")
        self.tabla.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tabla.cellClicked.connect(self._on_fila_cliente_clic)
        pt_lay.addWidget(self.tabla)
        lay.addWidget(panel_tabla)

        self.cargar_clientes(forzar=True)

    def _on_buscar_cambiado(self, _texto=""):
        self.lbl_estado.setText("Buscando…")
        self._timer_busqueda.start()

    @staticmethod
    def _categoria(ficha):
        deuda = float(ficha.get("deuda_actual") or 0)
        if deuda > 0.009:
            return "deuda"
        if deuda < -0.009:
            return "favor"
        return "al_dia"

    def _elegir_filtro(self, clave):
        self._filtro = clave
        self._sync_kpi_activo()
        self._pintar_tabla(refrescar_extras=False)

    def _kpi_filtro(self, clave):
        self._filtro = clave
        if clave in self._chips:
            self._chips[clave].setChecked(True)
        self._sync_kpi_activo()
        self._pintar_tabla(refrescar_extras=False)

    def _refrescar_chip_politica(self):
        if hasattr(self, "lbl_politica"):
            try:
                base = float(cerebro.mantenimiento_pct())
                apal = float(cerebro.apalancamiento_pct())
                plazo = int(cerebro.plazo_dias_politica())
                if apal > 0:
                    txt = f"Interés simple · {base:g}% mensual (+{apal:g}% >{plazo}d)"
                else:
                    txt = f"Interés simple · {base:g}% mensual por ticket"
                self.lbl_politica.setText(txt)
            except Exception:
                self.lbl_politica.setText("Interés simple por ticket")

    def _kpi_mayor(self):
        self._kpi_filtro("criticos")

    def _sync_kpi_activo(self):
        self.card_deuda.set_activo(self._filtro == "deuda")
        self.card_activos.set_activo(self._filtro == "deuda")
        self.card_mayor.set_activo(self._filtro in ("criticos", "d30", "d60", "d90"))
        self.card_cobros.set_activo(False)

    @staticmethod
    def _fecha_cache(cache, cliente_id):
        if not cache:
            return None
        if cliente_id in cache:
            return cache[cliente_id]
        try:
            return cache.get(int(cliente_id))
        except (TypeError, ValueError):
            return cache.get(str(cliente_id))

    @staticmethod
    def _parse_fecha(valor):
        if valor is None:
            return None
        if isinstance(valor, datetime):
            return valor
        texto = str(valor).strip().split(".")[0]
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto[:19] if " " in texto else texto[:10], fmt)
            except ValueError:
                continue
        return None

    def _dias_sin_pago(self, ficha):
        """Días desde el último ABONO. Sin pago: desde el último cargo. Deuda 0 → -1."""
        deuda = float(ficha.get("deuda_actual") or 0)
        if deuda <= 0.009:
            return -1
        cid = ficha.get("id")
        ultima = self._fecha_cache(self._cache_pagos, cid) or self._fecha_cache(
            self._cache_fechas, cid
        )
        if not ultima:
            return 9999
        dt = self._parse_fecha(ultima)
        if dt is None:
            return 9999
        return (datetime.now() - dt).days

    def _dias_sin_movimiento(self, ficha):
        """Alias: aging / tarifa / chips usan días desde el último pago."""
        return self._dias_sin_pago(ficha)

    def _es_critico(self, ficha):
        try:
            limite = int(cerebro.plazo_dias_politica())
        except Exception:
            limite = _CRITICOS_DIAS
        return self._dias_sin_pago(ficha) > limite

    def _promesa_vencida(self, ficha):
        from src.clientes_fiado.cerebro.cerebro import cerebro

        return cerebro.promesa_vencida(ficha)

    def _pintar_chips(self, fichas):
        from src.clientes_fiado.cerebro.cerebro import cerebro

        cuentas = {
            "todos": len(fichas), "deuda": 0, "al_dia": 0, "favor": 0,
            "express": 0, "criticos": 0, "d30": 0, "d60": 0, "d90": 0, "promesa": 0,
        }
        for f in fichas:
            cuentas[self._categoria(f)] += 1
            if (f.get("tipo_cliente") or "").lower() == "express":
                cuentas["express"] += 1
            if self._es_critico(f):
                cuentas["criticos"] += 1
            dias = self._dias_sin_movimiento(f)
            if cerebro.aging_cumple(dias, "d30"):
                cuentas["d30"] += 1
            if cerebro.aging_cumple(dias, "d60"):
                cuentas["d60"] += 1
            if cerebro.aging_cumple(dias, "d90"):
                cuentas["d90"] += 1
            if self._promesa_vencida(f):
                cuentas["promesa"] += 1
        textos = {
            "todos": "Todos", "deuda": "🟢 Con saldo", "al_dia": "🔵 Al día",
            "favor": "🔹 Saldo a favor", "express": "⚡ Express",
            "criticos": "🔴 Críticos", "d30": "30+", "d60": "60+", "d90": "90+",
            "promesa": "Promesa vencida",
        }
        for clave, chip in self._chips.items():
            chip.setText(f"{textos[clave]} ({cuentas[clave]})")

    def _pasa_filtro(self, ficha):
        from src.clientes_fiado.cerebro.cerebro import cerebro

        if self._filtro == "todos":
            return True
        if self._filtro == "express":
            return (ficha.get("tipo_cliente") or "").lower() == "express"
        if self._filtro == "criticos":
            return self._es_critico(ficha)
        if self._filtro in ("d30", "d60", "d90"):
            return cerebro.aging_cumple(self._dias_sin_movimiento(ficha), self._filtro)
        if self._filtro == "promesa":
            return self._promesa_vencida(ficha)
        return self._categoria(ficha) == self._filtro

    @staticmethod
    def _dias_txt(n):
        return f"{n} día" if abs(n) == 1 else f"{n} días"

    @staticmethod
    def _limite_efectivo(ficha):
        limite = float(ficha.get("limite_credito") or 0)
        tipo = (ficha.get("tipo_cliente") or "regular").lower()
        if tipo == "express" and limite <= 0:
            return float(FIADO_EXPRESS_LIMITE_DEFAULT)
        return limite

    def _dias_corridos(self, ficha):
        deuda = float(ficha.get("deuda_actual") or 0)
        if deuda <= 0.009:
            return 0
        ultima = self._fecha_cache(self._cache_fechas, ficha.get("id"))
        dt = self._parse_fecha(ultima)
        if dt is None:
            return 0
        return (datetime.now() - dt).days

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ajustar_columnas()

    def _ajustar_columnas(self):
        if not hasattr(self, "tabla") or self.tabla.columnCount() < 10:
            return
        vw = self.tabla.viewport().width()
        if vw <= 100:
            return
        w_acc = 136
        disp = max(400, vw - w_acc)
        # Proporciones visuales armónicas y equilibradas (DNI antes de Nombre, sin huecos vacíos):
        # 0:ID (4.5%), 1:DNI (8.5%), 2:Nombre (22%), 3:Tipo (8%), 4:Estado (9%), 5:Deuda (15.5%), 6:Mantenimiento (15%), 7:Días (9%), 8:Tarifa (8.5%)
        props = [0.045, 0.085, 0.22, 0.08, 0.09, 0.155, 0.15, 0.09, 0.085]
        minimos = [55, 110, 180, 80, 95, 130, 125, 75, 60]
        anchos = [max(m, int(disp * p)) for p, m in zip(props, minimos)]
        diff = disp - sum(anchos)
        anchos[2] = max(minimos[2], anchos[2] + diff)
        for c in range(9):
            self.tabla.setColumnWidth(c, anchos[c])
        self.tabla.setColumnWidth(_COL_ACCIONES, w_acc)

    def _clave_orden(self, ficha):
        key = self._sort_key
        if key == "id":
            return int(ficha.get("id") or 0)
        if key == "dni":
            return str(ficha.get("dni") or "").casefold()
        if key == "nombre":
            return str(ficha.get("nombre") or "").casefold()
        if key == "deuda":
            cid = ficha.get("id")
            cap = float(ficha.get("deuda_actual") or 0)
            inte = float((self._cache_intereses or {}).get(cid) or 0)
            return cap + inte if cap > 0 else cap
        if key == "mantenimiento":
            cid = ficha.get("id")
            return float((self._cache_intereses or {}).get(cid) or 0)
        if key == "dias":
            return self._dias_corridos(ficha)
        return 0

    def _ordenar_por_columna(self, col):
        clave = _SORT_COLS.get(col)
        if not clave:
            return
        if self._sort_key == clave:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_key = clave
            self._sort_asc = clave in ("nombre", "id", "dni")
        self.tabla.horizontalHeader().setSortIndicator(
            col,
            Qt.SortOrder.AscendingOrder if self._sort_asc else Qt.SortOrder.DescendingOrder,
        )
        self._pintar_tabla(refrescar_extras=False)

    def cargar_clientes(self, forzar=False):
        from src.clientes_fiado.cerebro.cerebro import cerebro

        busqueda = self.txt_buscar.text().strip()
        if (
            not forzar
            and self._cache_todas is not None
            and busqueda == self._cache_query
        ):
            self._pintar_tabla(refrescar_extras=False)
            return

        try:
            clientes = cerebro.buscar(busqueda)
            cache_todas = [dict(c) for c in clientes]
            deudores_ids = [
                ficha["id"]
                for ficha in cache_todas
                if float(ficha.get("deuda_actual") or 0) > 0
            ]
            cache_fechas = cerebro.ultimos_cargos(deudores_ids)
            cache_pagos = cerebro.ultimos_abonos(deudores_ids)
            cache_movs = cerebro.ultimos_movimientos(deudores_ids)
            try:
                cache_intereses = cerebro.intereses_acumulados(deudores_ids)
            except Exception:
                logger.exception("[Admin clientes] No se pudo calcular interes en lote")
                cache_intereses = {}
            cache_todas = self._fusionar_deudas_locales(cache_todas)
        except Exception:
            logger.exception("[Admin clientes] No se pudo actualizar la cartera")
            self.lbl_estado.setText(
                "ERROR al actualizar · se conserva la última cartera disponible"
            )
            self.lbl_estado.setStyleSheet(
                "color: #B91C1C; font-size: 12px; font-weight: 900; border: none; padding-left: 8px;"
            )
            return

        self._cache_todas = cache_todas
        self._cache_query = busqueda
        self._cache_fechas = cache_fechas
        self._cache_pagos = cache_pagos
        self._cache_movs = cache_movs
        self._cache_intereses = cache_intereses
        self.lbl_estado.setText("")
        self.lbl_estado.setStyleSheet(
            f"color: {_CLI['text_sec']}; font-size: 12px; font-weight: 700; border: none; padding-left: 8px;"
        )
        self._pintar_tabla(refrescar_extras=True)

    def _fusionar_deudas_locales(self, fichas=None):
        """En esclava offline el listado viene del espejo; trae deuda/estado/promesa locales."""
        from src.clientes_fiado.cerebro.cerebro import cerebro
        from src.clientes_fiado.oficina.barrial.mantenimiento import aplicar_overlay_local

        destino = self._cache_todas if fichas is None else fichas
        ids = [f.get("id") for f in (destino or []) if f.get("id") is not None]
        if not ids:
            return destino
        locales = cerebro.fichas_locales(ids)
        if not locales:
            return destino
        for i, ficha in enumerate(destino or []):
            destino[i] = aplicar_overlay_local(ficha, locales)
        return destino

    def _pintar_tabla(self, refrescar_extras=True):
        from src.clientes_fiado.cerebro.cerebro import cerebro
        from src.clientes_fiado.oficina.huella.consulta import huella_texto

        todas = self._cache_todas or []
        self._pintar_chips(todas)
        fichas = [f for f in todas if self._pasa_filtro(f)]
        fichas = sorted(fichas, key=self._clave_orden, reverse=not self._sort_asc)
        fechas_cargo = self._cache_fechas or {}

        total_deuda = 0.0
        deudores = 0
        max_deuda = 0.0
        mayor_id = None
        mayor_nombre = ""
        for f in todas:
            cid = f.get("id")
            cap = float(f.get("deuda_actual") or 0)
            inte = float((self._cache_intereses or {}).get(cid) or 0)
            d = cap + inte if cap > 0 else cap
            if d > 0:
                total_deuda += d
                deudores += 1
                if d > max_deuda:
                    max_deuda = d
                    mayor_id = f.get("id")
                    mayor_nombre = str(f.get("nombre") or "")
        self._mayor_id = mayor_id

        self.tabla.setUpdatesEnabled(False)
        self.tabla.setRowCount(0)
        try:
            for i, c in enumerate(fichas):
                cid = c.get("id")
                capital = float(c.get("deuda_actual") or 0)
                # Si el cliente ya pagó o tiene saldo a favor, el mantenimiento es estrictamente 0
                interes = float((self._cache_intereses or {}).get(cid) or 0) if capital > 0.009 else 0.0
                deuda = capital + interes if capital > 0 else capital
                limite = self._limite_efectivo(c)
                disponible = limite - deuda
                dni = (c.get("dni") or "").strip()
                tipo = (c.get("tipo_cliente") or "regular").lower()
                tipo_txt = "Express" if tipo == "express" else "Regular"
                try:
                    plazo = int(c.get("plazo_dias") or 0)
                except (TypeError, ValueError):
                    plazo = 0

                self.tabla.insertRow(i)
                self.tabla.setRowHeight(i, 54)
                it_id = vestir_id(QTableWidgetItem(str(c["id"])))
                it_id.setData(Qt.ItemDataRole.UserRole, int(c["id"]))
                self.tabla.setItem(i, 0, it_id)

                if dni:
                    it_dni = vestir_id(QTableWidgetItem(dni))
                else:
                    it_dni = vestir_nombre(QTableWidgetItem("Sin DNI"))
                    it_dni.setForeground(QColor("#64748B"))
                    it_dni.setToolTip("Completá el DNI desde Editar")
                self.tabla.setItem(i, 1, it_dni)

                nombre_raw = str(c["nombre"] or "")
                nombre_vis = nombre_raw.title() if (nombre_raw.islower() or nombre_raw.isupper()) else nombre_raw
                it_nombre = vestir_nombre(QTableWidgetItem(nombre_vis))
                it_nombre.setToolTip(huella_texto(c))
                self.tabla.setItem(i, 2, it_nombre)

                it_tipo = vestir_nombre(QTableWidgetItem(tipo_txt))
                if tipo == "express":
                    it_tipo.setForeground(QColor("#059669"))
                self.tabla.setItem(i, 3, it_tipo)

                dias_pago = self._dias_sin_pago(c)
                if cerebro.esta_suspendido(c):
                    it_est = vestir_nombre(QTableWidgetItem("Suspendido"))
                    it_est.setForeground(QColor("#7C2D12"))
                elif self._promesa_vencida(c):
                    it_est = vestir_nombre(QTableWidgetItem("Promesa vencida"))
                    it_est.setForeground(QColor("#7C3AED"))
                    it_est.setToolTip(f"Acordó pagar: {c.get('promesa_fecha') or ''}")
                else:
                    txt_est = cerebro.aging_etiqueta(dias_pago)
                    it_est = vestir_nombre(QTableWidgetItem(txt_est))
                    if txt_est:
                        it_est.setForeground(QColor(cerebro.aging_color(dias_pago)))
                        it_est.setToolTip(f"{self._dias_txt(dias_pago)} sin pago")
                    else:
                        it_est.setForeground(QColor("#CBD5E1"))
                self.tabla.setItem(i, 4, it_est)

                # Columna 5: Deuda total (capital + mantenimiento acumulado)
                if capital > 0.009:
                    limite_critico = cerebro.plazo_dias_politica() if hasattr(cerebro, 'plazo_dias_politica') else _CRITICOS_DIAS
                    es_riesgo = (
                        dias_pago > limite_critico
                        or disponible < -0.009
                        or cerebro.esta_suspendido(c)
                        or self._promesa_vencida(c)
                    )
                    it_deuda = vestir_numero(QTableWidgetItem(f"${deuda:,.2f}"))
                    if es_riesgo:
                        it_deuda.setForeground(QColor("#DC2626"))
                        it_deuda.setToolTip(
                            f"Total a cobrar: ${deuda:,.2f} (Capital: ${capital:,.2f} + Mantenimiento: ${interes:,.2f})\n"
                            f"Estado: En riesgo ({self._dias_txt(dias_pago)} sin pago)"
                        )
                    else:
                        it_deuda.setForeground(QColor("#059669"))
                        it_deuda.setToolTip(
                            f"Total a cobrar: ${deuda:,.2f} (Capital: ${capital:,.2f} + Mantenimiento: ${interes:,.2f})\n"
                            f"Estado: Al día ({self._dias_txt(dias_pago)} sin pago)"
                        )
                elif capital < -0.009:
                    it_deuda = vestir_numero(QTableWidgetItem(f"+${abs(capital):,.2f} a favor"))
                    it_deuda.setForeground(QColor("#2563EB"))
                    it_deuda.setToolTip(f"Saldo a favor: ${abs(capital):,.2f}")
                else:
                    it_deuda = vestir_numero(QTableWidgetItem("$0.00"))
                    it_deuda.setForeground(QColor("#64748B"))
                    it_deuda.setToolTip("Cuenta sin deuda")
                self.tabla.setItem(i, 5, it_deuda)

                # Columna 6: Mantenimiento (interés devengado proyectado por ticket/cargos)
                if capital > 0.009 and interes > 0.009:
                    it_mant = vestir_numero(QTableWidgetItem(f"+${interes:,.2f}"))
                    it_mant.setForeground(QColor("#B45309"))
                    it_mant.setToolTip(
                        f"Mantenimiento devengado: +${interes:,.2f}\n"
                        f"Capital: ${capital:,.2f} + Mantenimiento: ${interes:,.2f} = Total a cobrar: ${deuda:,.2f}"
                    )
                elif capital > 0.009:
                    it_mant = vestir_nombre(QTableWidgetItem("—"))
                    it_mant.setForeground(QColor("#94A3B8"))
                    it_mant.setToolTip(f"Sin interés acumulado · Total a cobrar: ${capital:,.2f}")
                else:
                    it_mant = vestir_nombre(QTableWidgetItem("—"))
                    it_mant.setForeground(QColor("#CBD5E1"))
                    it_mant.setToolTip("Cuenta sin deuda activa (al día o saldo a favor)")
                self.tabla.setItem(i, 6, it_mant)

                # Columna 7: Días sin pago
                dias_sin = dias_pago
                if capital > 0.009:
                    it_dias = vestir_nombre(QTableWidgetItem(self._dias_txt(max(0, dias_sin))))
                    if dias_sin > 90:
                        it_dias.setForeground(QColor("#7C2D12"))
                    elif dias_sin > 60:
                        it_dias.setForeground(QColor("#9A3412"))
                    elif dias_sin > 30:
                        it_dias.setForeground(QColor("#B45309"))
                    else:
                        it_dias.setForeground(QColor("#334155"))
                    tip = "Días desde el último pago"
                    if plazo > 0:
                        tip = f"Plazo {plazo} días · {tip}"
                    it_dias.setToolTip(tip)
                elif capital < -0.009:
                    it_dias = vestir_nombre(QTableWidgetItem("—"))
                    it_dias.setForeground(QColor("#94A3B8"))
                else:
                    it_dias = vestir_nombre(QTableWidgetItem("—"))
                    it_dias.setForeground(QColor("#CBD5E1"))
                self.tabla.setItem(i, 7, it_dias)

                # Columna 8: Tarifa %
                if capital > 0.009:
                    tarifa = cerebro.tarifar_mantenimiento(capital, dias_sin)
                    pct_txt = f"{float(tarifa.get('pct_total') or 0):g}%"
                    it_tar = vestir_numero(QTableWidgetItem(pct_txt))
                    if tarifa.get("aplica_apal"):
                        it_tar.setForeground(QColor("#9A3412"))
                        it_tar.setToolTip(
                            f"{tarifa['pct_base']:g}% + {tarifa['pct_apal']:g}% apal "
                            f"(último pago) = ${float(tarifa['monto_total']):,.2f}"
                        )
                    else:
                        it_tar.setToolTip(
                            f"Mant. {tarifa['pct_base']:g}% → ${float(tarifa['monto_total']):,.2f}"
                        )
                else:
                    it_tar = vestir_nombre(QTableWidgetItem("—"))
                    it_tar.setForeground(QColor("#94A3B8"))
                    it_tar.setToolTip("Cuenta en 0: no aplica mantenimiento")
                self.tabla.setItem(i, 8, it_tar)

                # Columna 9: Acciones (Abonar recibe total 'deuda' = capital + interes)
                self.tabla.setCellWidget(
                    i, _COL_ACCIONES, self._celda_acciones(c, deuda, limite, dias_sin)
                )
        finally:
            self.tabla.setUpdatesEnabled(True)
            self._ajustar_columnas()

        aging_n30 = aging_n60 = aging_n90 = 0
        deuda_riesgo = 0.0
        cuentas_riesgo = 0
        for f in todas:
            cid = f.get("id")
            cap = float(f.get("deuda_actual") or 0)
            inte = float((self._cache_intereses or {}).get(cid) or 0)
            d = cap + inte if cap > 0 else cap
            dmov = self._dias_sin_movimiento(f)
            if d > 0.009:
                lim = self._limite_efectivo(f)
                es_riesgo = (
                    dmov > _CRITICOS_DIAS
                    or (lim - d < -0.009)
                    or cerebro.esta_suspendido(f)
                    or self._promesa_vencida(f)
                )
                if es_riesgo:
                    deuda_riesgo += d
                    cuentas_riesgo += 1
            if cerebro.aging_cumple(dmov, "d30"):
                aging_n30 += 1
            if cerebro.aging_cumple(dmov, "d60"):
                aging_n60 += 1
            if cerebro.aging_cumple(dmov, "d90"):
                aging_n90 += 1

        self.card_deuda.set_valor(
            total_deuda, True,
            subtitulo=f"{deudores} cuentas activas · colocación total",
        )
        self.card_activos.set_valor(
            deudores, False,
            subtitulo=f"de {len(todas)} clientes registrados",
        )
        self.card_mayor.set_valor(
            deuda_riesgo, True,
            subtitulo=f"{cuentas_riesgo} en riesgo/mora · mayor: {mayor_nombre.title() if mayor_nombre else '—'}",
        )
        if refrescar_extras:
            total_cobros = cerebro.total_cobros_mes()
            self.card_cobros.set_valor(
                total_cobros, True,
                subtitulo="Abonado este mes · clic para ver",
            )
            self._pintar_cuadre()
        self._sync_kpi_activo()
        if not (self.lbl_estado.text() or "").startswith("Mantenimiento auto:"):
            self.lbl_estado.setText(
                f"{len(fichas)} de {len(todas)}" if self._filtro != "todos" else f"{len(todas)} clientes"
            )

    def _celda_acciones(self, ficha, deuda, limite, dias_sin=-1):
        from src.clientes_fiado.cerebro.cerebro import cerebro

        cliente_id = ficha["id"]
        nombre = ficha.get("nombre") or ""
        suspendido = cerebro.esta_suspendido(ficha)

        acc_w = QWidget()
        acc_w.setStyleSheet("background: transparent;")
        acc_lay = QHBoxLayout(acc_w)
        acc_lay.setContentsMargins(4, 0, 4, 0)
        acc_lay.setSpacing(6)
        acc_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        btn_abonar = QPushButton("Abonar")
        btn_abonar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_abonar.setFixedSize(84, 34)
        btn_abonar.setToolTip("Cobrar · excedente queda a favor")
        btn_abonar.setStyleSheet(
            "QPushButton { background: #2563EB; color: #FFFFFF; border: none; "
            "border-radius: 6px; font-family: 'Segoe UI', sans-serif; font-size: 13px; "
            "font-weight: 800; padding: 0px 8px; text-align: center; }"
            "QPushButton:hover { background: #1D4ED8; }"
            "QPushButton:pressed { background: #1E40AF; }"
        )
        btn_abonar.clicked.connect(
            lambda _=False, cid=cliente_id, cnom=nombre, cdeu=deuda: self.abonar_deuda_admin(cid, cnom, cdeu)
        )
        acc_lay.addWidget(btn_abonar)

        mas = QToolButton()
        mas.setText("···")
        mas.setCursor(Qt.CursorShape.PointingHandCursor)
        mas.setFixedSize(34, 34)
        mas.setToolTip("Más acciones")
        mas.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        mas.setStyleSheet(
            "QToolButton { background: white; color: #475569; border: 1px solid #CBD5E1; "
            "border-radius: 6px; font-weight: 900; font-size: 14px; padding: 0; }"
            "QToolButton::menu-indicator { image: none; width: 0; }"
            "QToolButton:hover { background: #F8FAFC; border-color: #94A3B8; color: #0F172A; }"
        )
        menu = QMenu(mas)
        menu.setStyleSheet(
            "QMenu { background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 4px; }"
            "QMenu::item { padding: 7px 14px; font-weight: 700; color: #0F172A; border-radius: 4px; }"
            "QMenu::item:selected { background: #EFF6FF; color: #1D4ED8; }"
        )
        act_limite = QAction("Límite de crédito", menu)
        act_limite.triggered.connect(
            lambda _=False, cid=cliente_id, cnom=nombre, lim=limite: self.editar_limite_credito(cid, cnom, lim)
        )
        act_editar = QAction("Editar ficha", menu)
        act_editar.triggered.connect(
            lambda _=False, cid=cliente_id: self._abrir_editar_cliente(cid)
        )
        if suspendido:
            act_estado = QAction("Reactivar cuenta", menu)
            act_estado.triggered.connect(
                lambda _=False, cid=cliente_id, cnom=nombre: self._reactivar_cliente(cid, cnom)
            )
        else:
            act_estado = QAction("Suspender cuenta", menu)
            act_estado.triggered.connect(
                lambda _=False, cid=cliente_id, cnom=nombre: self._suspender_cliente(cid, cnom)
            )
        act_promesa = QAction("Promesa de pago…", menu)
        act_promesa.triggered.connect(
            lambda _=False, f=dict(ficha): self._abrir_promesa(f)
        )
        menu.addAction(act_limite)
        menu.addAction(act_editar)
        menu.addAction(act_estado)
        menu.addAction(act_promesa)
        mas.setMenu(menu)
        acc_lay.addWidget(mas)
        return acc_w

    def _pintar_cuadre(self):
        try:
            from src.clientes_fiado.cerebro.cerebro import cerebro

            huecos = cerebro.ventas_sin_cargo()
        except Exception:
            logger.exception("[Admin clientes] No se pudieron verificar ventas sin cargo")
            self.lbl_cuadre.setText(
                "No se pudieron verificar ventas a crédito pendientes. No significa que estén cuadradas."
            )
            self.btn_cuadre.setText("REINTENTAR")
            self.aviso_cuadre.setStyleSheet(
                "background: #FEE2E2; border: 1px solid #FCA5A5; border-radius: 12px;"
            )
            self.lbl_cuadre.setStyleSheet(
                "color: #991B1B; font-weight: 900; font-size: 13px; background: transparent; border: none;"
            )
            self.aviso_cuadre.show()
            return
        self.btn_cuadre.setText("CUADRAR")
        self.aviso_cuadre.setStyleSheet(
            "background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 12px;"
        )
        self.lbl_cuadre.setStyleSheet(
            "color: #92400E; font-weight: 800; font-size: 13px; background: transparent; border: none;"
        )
        if not huecos:
            self.aviso_cuadre.hide()
            return
        total = sum(float(fila.get("total") or 0) for fila in huecos)
        self.lbl_cuadre.setText(
            f"{len(huecos)} ventas a crédito sin cargo en la cuenta  ·  ${total:,.2f}"
        )
        self.aviso_cuadre.show()

    def _abrir_cuadre(self):
        if qt_exec(DialogoCuadre(self)):
            self.cargar_clientes(forzar=True)

    def _abrir_cobros(self):
        qt_exec(DialogoCobros(self))

    def _abrir_cargos(self):
        from src.admin.clientes.componentes.dialogo_cargos import DialogoCargos

        qt_exec(DialogoCargos(self))

    def _abrir_auditoria(self):
        from src.admin.clientes.componentes.dialogo_auditoria_clientes import DialogoAuditoriaClientes

        qt_exec(DialogoAuditoriaClientes(self))

    def _on_fila_cliente_clic(self, row, col):
        if col == _COL_ACCIONES:
            return
        item = self.tabla.item(row, 0)
        if not item:
            return
        cliente_id = item.data(Qt.ItemDataRole.UserRole)
        if cliente_id is None:
            try:
                cliente_id = int(item.text())
            except (TypeError, ValueError):
                return
        self._abrir_historial_cliente(int(cliente_id))

    def _abrir_historial_cliente(self, cliente_id):
        dlg = DialogoHistorialCliente(cliente_id, self)
        qt_exec(dlg)
        self.cargar_clientes(forzar=True)

    def _abrir_editar_cliente(self, cliente_id):
        dlg = DialogoEditarCliente(cliente_id, self)
        if qt_exec(dlg):
            self.cargar_clientes(forzar=True)

    def _suspender_cliente(self, cliente_id, nombre):
        from src.clientes_fiado.cerebro.cerebro import cerebro

        resp = QMessageBox.question(
            self,
            "Suspender cuenta",
            f"¿Suspender a {nombre}?\nEn caja no vende a fiado sin PIN de admin.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        if cerebro.suspender(cliente_id):
            self.cargar_clientes(forzar=True)
        else:
            QMessageBox.warning(self, "Error", "No se pudo suspender la cuenta.")

    def _reactivar_cliente(self, cliente_id, nombre):
        from src.clientes_fiado.cerebro.cerebro import cerebro

        if cerebro.reactivar(cliente_id):
            self.cargar_clientes(forzar=True)
        else:
            QMessageBox.warning(self, "Error", "No se pudo reactivar la cuenta.")

    def _abrir_promesa(self, ficha):
        from src.admin.clientes.componentes.dialogo_promesa import DialogoPromesa
        from src.clientes_fiado.cerebro.cerebro import cerebro

        cliente_id = ficha.get("id")
        nombre = ficha.get("nombre") or ""
        resultado = DialogoPromesa.pedir(
            cliente_id,
            nombre,
            ficha.get("promesa_fecha"),
            ficha.get("promesa_nota") or "",
            self,
        )
        if not resultado:
            return
        if resultado[0] == "limpiar":
            ok = cerebro.limpiar_promesa(cliente_id)
        else:
            ok = cerebro.fijar_promesa(cliente_id, resultado[1], resultado[2] if len(resultado) > 2 else "")
        if ok:
            self.cargar_clientes(forzar=True)
        else:
            QMessageBox.warning(self, "Error", "No se pudo guardar la promesa.")

    def _abrir_politicas(self):
        try:
            from src.central_red_global.sync_tienda.config_tienda import sincronizar_desde_maestra

            sincronizar_desde_maestra()
        except Exception:
            pass
        from src.admin.clientes.componentes.dialogo_politicas_credito import DialogoPoliticasCredito

        if DialogoPoliticasCredito.pedir(self):
            self._refrescar_chip_politica()
            self.cargar_clientes(forzar=True)

    def nuevo_cliente(self):
        dlg = DialogoNuevoCliente(self)
        if qt_exec(dlg):
            data = dlg.get_data()
            nombre = (data.get("nombre") or "").strip()
            if not nombre:
                QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
                return
            dni = data.get("dni")
            from src.clientes_fiado.cerebro.cerebro import cerebro

            existente = cerebro.hallar_duplicado(nombre, dni)
            if existente:
                resp = QMessageBox.question(
                    self,
                    "Cliente Existente",
                    f"Ya existe un cliente registrado como '{existente['nombre']}'.\n\n"
                    f"¿Desea actualizar los datos de este cliente existente en lugar de duplicarlo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if resp == QMessageBox.StandardButton.Yes:
                    cerebro.actualizar_existente(
                        existente["id"],
                        nombre,
                        data["telefono"],
                        data["limite_credito"],
                        dni or existente.get("dni"),
                    )
                    self.cargar_clientes(forzar=True)
                    return
                return

            cerebro.alta_regular(nombre, data["telefono"], data["limite_credito"], dni)
            self.cargar_clientes(forzar=True)

    def editar_limite_credito(self, cliente_id, nombre, limite_actual):
        from PyQt6.QtWidgets import QInputDialog
        nuevo, ok = QInputDialog.getDouble(
            self,
            "Límite de crédito",
            f"Cliente: {nombre}\nLímite actual: ${limite_actual:,.2f}\n\nNuevo límite ($):",
            limite_actual,
            0,
            99_999_999,
            2,
        )
        if ok and nuevo >= 0:
            from src.clientes_fiado.cerebro.cerebro import cerebro

            cerebro.fijar_limite(cliente_id, nuevo)
            QMessageBox.information(self, "Listo", f"Límite actualizado a ${nuevo:,.2f}")
            self.cargar_clientes(forzar=True)

    def abonar_deuda_admin(self, cliente_id, nombre, deuda_actual):
        from src.cajero.f6_centro_cobranzas import DialogoCentroCobranzas
        from src.clientes_fiado.cerebro.cerebro import cerebro

        cliente = cerebro.obtener(cliente_id) or {
            "id": cliente_id,
            "nombre": nombre,
            "deuda_actual": deuda_actual,
        }
        try:
            total_estimado = float(
                deuda_actual
                if deuda_actual is not None
                else cliente.get("deuda_actual") or 0
            )
        except (TypeError, ValueError):
            total_estimado = float(cliente.get("deuda_actual") or 0)
        sugerido = total_estimado if total_estimado > 0.009 else None
        dlg = DialogoCentroCobranzas(parent=self, perfil="Admin")
        dlg.abrir_para_cliente(cliente, sugerido, ir_a_pago=True)
        if not (qt_exec(dlg) and dlg.cliente_id):
            return
        resultado = getattr(dlg, "resultado", None)
        if resultado is None or not getattr(resultado, "ok", False):
            return
        try:
            win = self.window()
            pantallas = getattr(win, "screens", None) or []
            ventas = pantallas[1] if len(pantallas) > 1 else None
            if ventas is not None and hasattr(ventas, "_refrescar_notificaciones"):
                ventas._refrescar_notificaciones()
        except Exception:
            pass
        self.cargar_clientes(forzar=True)
