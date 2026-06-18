from src.utils.theme_manager import theme_manager
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QAbstractItemView, QMessageBox, QDialog,
    QFormLayout, QSplitter, QComboBox, QCheckBox,
    QDoubleSpinBox, QRadioButton, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

STYLE = """
QWidget {
    
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 13px;
    
}
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:1 #ea580c);
    border-bottom: 2px solid #0f172a;
    border-radius: 10px;
}
QLabel#titulo {
    color: #1e293b;
    background: transparent;
    font-size: 20px;
    font-weight: 900;
    letter-spacing: 1px;
}
QPushButton {
    background-color: white;
    
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    
    color: #1e293b;
    border-
}
QLineEdit, QComboBox, QDoubleSpinBox {
    background-color: white;
    
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #ea580c;
}
"""

class Admin2Ofertas(QWidget):
    request_dashboard = pyqtSignal()

    HEADERS = ["🗹", "ID / Cód.", "Producto", "Departamento", "Costo", "Precio Reg.", "Stock", "U. Oferta", "Cant. Promo", "Precio Promo"]

    def __init__(self):
        super().__init__()
        self.producto_seleccionado_id = None
        self.checked_product_ids = set()
        self.all_rows = []
        self.loaded_count = 0
        self._setup_ui()
        QTimer.singleShot(50, self._inicializar_datos)

    def _inicializar_datos(self):
        self._cargar_deptos()
        self.cargar_datos()

    def _setup_ui(self):
        self.setStyleSheet(STYLE)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── HEADER ────────────────────────────────────────
        hdr = QFrame(); hdr.setObjectName("header"); hdr.setFixedHeight(85)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(25, 0, 25, 0)
        
        btn_back = QPushButton("🔙 VOLVER AL PANEL")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2); color: white; font-weight: 800; border-radius: 10px; 
                padding: 10px 25px; border: 1px solid rgba(255, 255, 255, 0.4); font-size: 11px; letter-spacing: 1px;
            }
            QPushButton:hover { background: white;  }
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_back)
        hl.addSpacing(20)
        
        tit = QLabel("🏷️ MOTOR DE PROMOCIONES INTELIGENTE <span style='color: rgba(255,255,255,0.7);'>2026</span>")
        tit.setObjectName("titulo")
        tit.setStyleSheet("background: transparent;")
        hl.addWidget(tit); hl.addStretch()
        root.addWidget(hdr)

        # ── FILTRO SUPERIOR ──────────────────────────────
        fb = QFrame(); fb.setFixedHeight(60)
        fb.setStyleSheet("QFrame{border-bottom:1px solid #cbd5e1;}")
        fl = QHBoxLayout(fb); fl.setContentsMargins(15, 6, 15, 6); fl.setSpacing(12)
        
        ico_search = QLabel("🔍")
        ico_search.setStyleSheet(" font-size: 16px; background: transparent;")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, código o ID...")
        self.txt_buscar.setMinimumWidth(350)
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.cargar_datos)
        self.txt_buscar.textChanged.connect(lambda: self.search_timer.start(300))

        lbl_dep = QLabel("DEPARTAMENTO:")
        lbl_dep.setStyleSheet("font-weight:800;font-size:10px;letter-spacing:1px; background: transparent;")
        self.cmb_depto = QComboBox()
        self.cmb_depto.setMinimumWidth(180)
        self.cmb_depto.currentIndexChanged.connect(self.cargar_datos)

        fl.addWidget(ico_search)
        fl.addWidget(self.txt_buscar)
        fl.addSpacing(15)
        fl.addWidget(lbl_dep); fl.addWidget(self.cmb_depto)
        
        # Filtro de promociones
        fl.addSpacing(15)
        self.chk_ver_promos = QCheckBox("🔥 Ver Solo Promos")
        self.chk_ver_promos.setStyleSheet(" font-weight:800; font-size:11px; background: transparent;")
        self.chk_ver_promos.stateChanged.connect(self.cargar_datos)
        fl.addWidget(self.chk_ver_promos)
        
        # Botón de impresión masiva en lote (Libro)
        fl.addSpacing(15)
        self.btn_imprimir_masivo = QPushButton("📚 IMPRIMIR MASIVO (A4)")
        self.btn_imprimir_masivo.setCursor(Qt.PointingHandCursor)
        self.btn_imprimir_masivo.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:1 #0284c7);
                color: #1e293b; font-weight: 800; font-size: 11px; padding: 8px 15px; border-radius: 6px; border: none;
            }
            QPushButton:hover {  background-color: #3b82f6; color: white; }
            QPushButton:disabled {   }
        """)
        self.btn_imprimir_masivo.setEnabled(False)
        self.btn_imprimir_masivo.clicked.connect(self._imprimir_cartelera_masiva)
        fl.addWidget(self.btn_imprimir_masivo)

        # Botón para Crear Folleto Publicitario (PDF)
        fl.addSpacing(15)
        self.btn_crear_folleto = QPushButton("📰 CREAR FOLLETO (PDF)")
        self.btn_crear_folleto.setCursor(Qt.PointingHandCursor)
        self.btn_crear_folleto.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                color: #1e293b; font-weight: 800; font-size: 11px; padding: 8px 15px; border-radius: 6px; border: none;
            }
            QPushButton:hover {  background-color: #3b82f6; color: white; }
        """)
        self.btn_crear_folleto.clicked.connect(self._crear_folleto_pdf)
        fl.addWidget(self.btn_crear_folleto)
        
        # Botón de Asistente de Promo Caliente (A4)
        fl.addSpacing(15)
        self.btn_asistente_promo = QPushButton("🔥 ASISTENTE PROMO (A4)")
        self.btn_asistente_promo.setCursor(Qt.PointingHandCursor)
        self.btn_asistente_promo.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:1 #f97316);
                color: #1e293b; font-weight: 800; font-size: 11px; padding: 8px 15px; border-radius: 6px; border: none;
            }
            QPushButton:hover {  background-color: #3b82f6; color: white; }
            QPushButton:disabled {   }
        """)
        self.btn_asistente_promo.setEnabled(False)
        self.btn_asistente_promo.clicked.connect(self._configurar_ofertas_secuencial)
        fl.addWidget(self.btn_asistente_promo)
        
        fl.addStretch()
        root.addWidget(fb)

        # ── CUERPO PRINCIPAL CON SPLITTER ──────────────────
        cuerpo = QWidget()
        lay_body = QVBoxLayout(cuerpo)
        lay_body.setContentsMargins(15, 15, 15, 15)
        lay_body.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle {  width: 1px; }")

        # Tabla de productos (Izquierda)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(self.HEADERS))
        self.tabla.setHorizontalHeaderLabels(self.HEADERS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setShowGrid(True)
        self.tabla.setGridStyle(Qt.SolidLine)
        self.tabla.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                gridline-color: transparent;
                outline: none;
            }
            QTableWidget::item {
                padding: 4px; 
                border-bottom: 1px solid #F1F5F9;
            }
            QTableWidget::item:hover {
                background-color: #F8FAFC;
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF;
                color: #1D4ED8;
                border-bottom: 2px solid #3B82F6;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                font-weight: 900;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        col_widths = [35, 120, -1, 110, 80, 80, 80, 80, 80, 80]
        hh = self.tabla.horizontalHeader()
        for i, w in enumerate(col_widths):
            if w == -1:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Fixed)
                self.tabla.setColumnWidth(i, w)

        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.itemSelectionChanged.connect(self._actualizar_sel)
        self.tabla.itemChanged.connect(self._on_item_changed)
        splitter.addWidget(self.tabla)

        # Panel de Control Derecho (Scrollable)
        self.right_container = QScrollArea()
        self.right_container.setWidgetResizable(True)
        self.right_container.setStyleSheet("QScrollArea { border: none; background: white; }")
        
        self.panel_control = QFrame()
        self.panel_control.setObjectName("ControlCenter")
        self.panel_control.setStyleSheet("""
            QFrame#ControlCenter {
                background-color: #0F172A;
                border-left: 1px solid #1E293B;
            }
            QLabel { background: transparent; color: #F8FAFC; }
        """)
        lay_ctrl = QVBoxLayout(self.panel_control)
        lay_ctrl.setContentsMargins(20, 20, 20, 20)
        lay_ctrl.setSpacing(15)
        
        # Encabezado
        lbl_head = QLabel("⚙️ REGLAS DEL PRODUCTO")
        lbl_head.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: 900; letter-spacing: 1px;")
        lay_ctrl.addWidget(lbl_head)
        
        self.lbl_prod_nombre = QLabel("Seleccione un producto...")
        self.lbl_prod_nombre.setStyleSheet("color: #38BDF8; font-size: 18px; font-weight: 900;")
        self.lbl_prod_nombre.setWordWrap(True)
        lay_ctrl.addWidget(self.lbl_prod_nombre)
        
        self.lbl_prod_detalles = QLabel("ID: —  |  PLU: —")
        self.lbl_prod_detalles.setStyleSheet("color: #CBD5E1; font-size: 12px; font-family: 'Consolas', monospace; font-weight: bold;")
        lay_ctrl.addWidget(self.lbl_prod_detalles)
        
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("  max-height: 1px; background: #334155;")
        lay_ctrl.addWidget(sep)
        
        # Sección A: Ajustes rápidos
        lbl_sec_a = QLabel("📦 CONTROL DE STOCK")
        lbl_sec_a.setStyleSheet("color: #94A3B8; font-weight: 800; font-size: 11px; letter-spacing: 1px;")
        lay_ctrl.addWidget(lbl_sec_a)
        
        form_a = QFormLayout()
        form_a.setSpacing(8)
        
        self.txt_quick_precio = QDoubleSpinBox()
        self.txt_quick_precio.setRange(0, 9999999)
        self.txt_quick_precio.setDecimals(2)
        self.txt_quick_precio.setStyleSheet("font-size: 13px; padding: 6px; font-weight: bold;")
        
        self.txt_quick_costo = QDoubleSpinBox()
        self.txt_quick_costo.setRange(0, 9999999)
        self.txt_quick_costo.setDecimals(2)
        self.txt_quick_costo.setStyleSheet("font-size: 13px; padding: 6px;")
        
        self.txt_quick_stock = QDoubleSpinBox()
        self.txt_quick_stock.setRange(-9999, 999999)
        self.txt_quick_stock.setDecimals(2)
        self.txt_quick_stock.setStyleSheet("font-size: 13px; padding: 6px; font-weight: bold; ")
        
        form_a.addRow(QLabel("Precio Venta ($):"), self.txt_quick_precio)
        form_a.addRow(QLabel("Costo Compra ($):"), self.txt_quick_costo)
        form_a.addRow(QLabel("Stock Actual:"), self.txt_quick_stock)
        lay_ctrl.addLayout(form_a)
        
        # Botones de ajuste de stock
        lay_btns_stock = QHBoxLayout()
        btn_m10 = QPushButton("-10"); btn_m10.setStyleSheet("padding: 5px; font-size: 10px; font-weight: bold; ")
        btn_m1 = QPushButton("-1"); btn_m1.setStyleSheet("padding: 5px; font-size: 10px; font-weight: bold; ")
        btn_p1 = QPushButton("+1"); btn_p1.setStyleSheet("padding: 5px; font-size: 10px; font-weight: bold; ")
        btn_p10 = QPushButton("+10"); btn_p10.setStyleSheet("padding: 5px; font-size: 10px; font-weight: bold; ")
        
        btn_m10.clicked.connect(lambda: self._quick_stock_adjust(-10))
        btn_m1.clicked.connect(lambda: self._quick_stock_adjust(-1))
        btn_p1.clicked.connect(lambda: self._quick_stock_adjust(1))
        btn_p10.clicked.connect(lambda: self._quick_stock_adjust(10))
        
        lay_btns_stock.addWidget(btn_m10); lay_btns_stock.addWidget(btn_m1)
        lay_btns_stock.addWidget(btn_p1); lay_btns_stock.addWidget(btn_p10)
        lay_ctrl.addLayout(lay_btns_stock)
        
        self.btn_guardar_quick = QPushButton("💾 GUARDAR AJUSTES")
        self.btn_guardar_quick.setStyleSheet("""
            QPushButton {
                 color: #1e293b; font-weight: 800; font-size: 11px;
                padding: 10px; border-radius: 6px; border: none;
            }
            QPushButton:hover {  }
        """)
        self.btn_guardar_quick.clicked.connect(self._guardar_cambios_rapidos)
        lay_ctrl.addWidget(self.btn_guardar_quick)
        
        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine); sep2.setFrameShadow(QFrame.Sunken)
        sep2.setStyleSheet("  max-height: 1px;")
        lay_ctrl.addWidget(sep2)
        
        # Sección B: Promociones
        lbl_sec_b = QLabel("🏷️ REGLAS MATEMÁTICAS DE PROMOCIÓN")
        lbl_sec_b.setStyleSheet("color: #94A3B8; font-weight: 800; font-size: 11px; letter-spacing: 1px;")
        lay_ctrl.addWidget(lbl_sec_b)
        
        form_b = QFormLayout()
        form_b.setSpacing(8)
        
        self.sp_quick_cant_oferta = QDoubleSpinBox()
        self.sp_quick_cant_oferta.setRange(0, 99999)
        self.sp_quick_cant_oferta.setDecimals(2)
        self.sp_quick_cant_oferta.setStyleSheet("font-size: 13px; padding: 6px;")
        
        self.sp_quick_precio_oferta = QDoubleSpinBox()
        self.sp_quick_precio_oferta.setRange(0, 9999999)
        self.sp_quick_precio_oferta.setDecimals(2)
        self.sp_quick_precio_oferta.setStyleSheet("font-size: 13px; padding: 6px;  font-weight: bold;")

        self.sp_quick_oferta_relampago = QDoubleSpinBox()
        self.sp_quick_oferta_relampago.setRange(0, 9999999)
        self.sp_quick_oferta_relampago.setDecimals(2)
        self.sp_quick_oferta_relampago.setStyleSheet("font-size: 13px; padding: 6px;")

        self.sp_quick_oferta_promedio = QDoubleSpinBox()
        self.sp_quick_oferta_promedio.setRange(0, 9999999)
        self.sp_quick_oferta_promedio.setDecimals(2)
        self.sp_quick_oferta_promedio.setStyleSheet("font-size: 13px; padding: 6px;")
        self.sp_limite_relampago = QDoubleSpinBox()
        self.sp_limite_relampago.setRange(0, 9999999)
        self.sp_limite_relampago.setDecimals(0)
        self.sp_limite_relampago.setStyleSheet("font-size: 13px; padding: 6px;")
        self.lbl_ventas_relampago = QLabel("Vendidos: 0 / 0")
        self.lbl_ventas_relampago.setStyleSheet("color: #D97706; font-weight: bold;")
        
        form_b.addRow(QLabel("Oferta desde (Cant):"), self.sp_quick_cant_oferta)
        form_b.addRow(QLabel("Precio Of. Manual ($):"), self.sp_quick_precio_oferta)
        form_b.addRow(QLabel("Of. Relámpago ($):"), self.sp_quick_oferta_relampago)
        form_b.addRow(QLabel("Límite (uds):"), self.sp_limite_relampago)
        form_b.addRow(QLabel(""), self.lbl_ventas_relampago)
        form_b.addRow(QLabel("Of. Promedio ($):"), self.sp_quick_oferta_promedio)
        lay_ctrl.addLayout(form_b)
        
        # Caja de simulación de rentabilidad industrial
        self.group_simulador = QFrame()
        self.group_simulador.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 15px;
                margin-top: 5px;
            }
        """)
        lay_sim = QVBoxLayout(self.group_simulador)
        lay_sim.setSpacing(6)
        
        lbl_sim_tit = QLabel("📊 SIMULADOR DE MARGEN INDUSTRIAL")
        lbl_sim_tit.setStyleSheet("color: #E2E8F0; font-weight: 900; font-size: 12px; letter-spacing: 1px; border: none;")
        lay_sim.addWidget(lbl_sim_tit)
        
        self.lbl_margen_reg = QLabel("Margen Regular: —")
        self.lbl_margen_reg.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: bold; border: none;")
        lay_sim.addWidget(self.lbl_margen_reg)
        
        self.lbl_margen_promo = QLabel("Margen Promo: —")
        self.lbl_margen_promo.setStyleSheet("color: #34D399; font-size: 18px; font-weight: 900; border: none;")
        lay_sim.addWidget(self.lbl_margen_promo)
        
        self.lbl_ahorro_total = QLabel("Ahorro de Cliente: —")
        self.lbl_ahorro_total.setStyleSheet("color: #FBBF24; font-size: 16px; font-weight: bold; border: none;")
        lay_sim.addWidget(self.lbl_ahorro_total)
        
        self.lbl_semaforo = QLabel("Seleccione un producto...")
        self.lbl_semaforo.setStyleSheet("color: #E2E8F0; font-size: 11px; font-weight: 800; border: none;")
        self.lbl_semaforo.setAlignment(Qt.AlignCenter)
        lay_sim.addWidget(self.lbl_semaforo)
        
        lay_ctrl.addWidget(self.group_simulador)
        
        lay_promo_btns = QHBoxLayout()
        self.btn_activar_promo = QPushButton("🚀 ACTIVAR PROMO")
        self.btn_activar_promo.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: white; font-weight: 900; font-size: 12px;
                padding: 12px; border-radius: 8px; border: none; letter-spacing: 1px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        self.btn_activar_promo.clicked.connect(self._guardar_oferta_rapida)
        
        self.btn_quitar_promo = QPushButton("❌ QUITAR PROMO")
        self.btn_quitar_promo.setStyleSheet("""
            QPushButton {
                color: #EF4444; background: transparent; font-weight: bold; font-size: 12px;
                padding: 12px; border-radius: 8px; border: 2px solid #EF4444; letter-spacing: 1px;
            }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        self.btn_quitar_promo.clicked.connect(self._quitar_oferta_rapida)
        
        lay_promo_btns.addWidget(self.btn_activar_promo)
        lay_promo_btns.addWidget(self.btn_quitar_promo)
        lay_ctrl.addLayout(lay_promo_btns)
        
        self.btn_imprimir_quick_cartel = QPushButton("🖨️ IMPRIMIR CARTEL (A4)")
        self.btn_imprimir_quick_cartel.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:1 #f97316);
                color: #1e293b; font-weight: 900; font-size: 11px; padding: 11px; border-radius: 6px; border: none;
            }
            QPushButton:hover {  }
        """)
        self.btn_imprimir_quick_cartel.clicked.connect(self._imprimir_cartel_a4_rapido)
        lay_ctrl.addWidget(self.btn_imprimir_quick_cartel)
        
        lay_ctrl.addStretch()
        
        self.right_container.setWidget(self.panel_control)
        splitter.addWidget(self.right_container)
        splitter.setSizes([780, 420])
        
        lay_body.addWidget(splitter)
        root.addWidget(cuerpo)

        # ── Footer ───────────────────────────────────────
        ft = QFrame(); ft.setFixedHeight(34)
        ft.setStyleSheet("QFrame{border-top:1px solid #cbd5e1;}")
        fl2 = QHBoxLayout(ft); fl2.setContentsMargins(12, 0, 12, 0)
        self.lbl_total   = QLabel("0 productos")
        self.lbl_stock0  = QLabel("")
        self.lbl_sel     = QLabel("")
        for lbl in [self.lbl_total, self.lbl_stock0, self.lbl_sel]:
            lbl.setStyleSheet("font-size:11px; background: transparent;")
        fl2.addWidget(self.lbl_total)
        fl2.addSpacing(20); fl2.addWidget(self.lbl_stock0)
        fl2.addStretch();   fl2.addWidget(self.lbl_sel)
        root.addWidget(ft)

        self.panel_control.setEnabled(False)

        # Conexión dinámica del Simulador de Margen Industrial
        self.txt_quick_precio.valueChanged.connect(self._recargar_simulador)
        self.txt_quick_costo.valueChanged.connect(self._recargar_simulador)
        self.sp_quick_cant_oferta.valueChanged.connect(self._recargar_simulador)
        self.sp_quick_precio_oferta.valueChanged.connect(self._recargar_simulador)
        self.sp_quick_oferta_relampago.valueChanged.connect(self._recargar_simulador)
        self.sp_quick_oferta_promedio.valueChanged.connect(self._recargar_simulador)
        self.tabla.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)

    def _recargar_simulador(self):
        if not self.producto_seleccionado_id:
            self.lbl_margen_reg.setText("Margen Regular: —")
            self.lbl_margen_promo.setText("Margen Promo: —")
            self.lbl_ahorro_total.setText("Ahorro de Cliente: —")
            self.lbl_semaforo.setText("Seleccione un producto...")
            self.lbl_semaforo.setStyleSheet("font-size: 11px; font-weight: 800;  border: none; background-color: transparent; padding: 0;")
            return
            
        costo = self.txt_quick_costo.value()
        reg_precio = self.txt_quick_precio.value()
        promo_precio = self.sp_quick_precio_oferta.value()
        promo_cant = self.sp_quick_cant_oferta.value()
        
        # Margen Regular
        if reg_precio > 0:
            margen_reg = ((reg_precio - costo) / reg_precio) * 100
            self.lbl_margen_reg.setText(f"Margen Regular: {margen_reg:.1f}%")
        else:
            self.lbl_margen_reg.setText("Margen Regular: 0.0%")
            
        # Margen Promo & Ahorro
        if promo_precio > 0:
            margen_promo = ((promo_precio - costo) / promo_precio) * 100
            self.lbl_margen_promo.setText(f"Margen Promo: {margen_promo:.1f}%")
            
            ahorro = max(0.0, reg_precio - promo_precio) * promo_cant
            self.lbl_ahorro_total.setText(f"Ahorro Cliente por Compra: ${ahorro:.2f}")
            
            # Semáforo de Viabilidad Financiera
            if promo_precio <= costo:
                self.lbl_semaforo.setText("🚨 PÉRDIDA: ¡OFERTA POR DEBAJO DEL COSTO!")
                self.lbl_semaforo.setStyleSheet("font-size: 10px; font-weight: 900; background-color: #64748b; color: white;  border-radius: 4px; padding: 4px; border: none;")
            elif margen_promo < 10.0:
                self.lbl_semaforo.setText("⚠️ MARGEN CRÍTICO: RENTABILIDAD BAJA")
                self.lbl_semaforo.setStyleSheet("font-size: 10px; font-weight: 900;   border-radius: 4px; padding: 4px; border: none;")
            else:
                self.lbl_semaforo.setText("✅ PROMOCIÓN RENTABLE: RENTABILIDAD POSITIVA")
                self.lbl_semaforo.setStyleSheet("font-size: 10px; font-weight: 900; background-color: #64748b; color: white;  border-radius: 4px; padding: 4px; border: none;")
        else:
            self.lbl_margen_promo.setText("Margen Promo: —")
            self.lbl_ahorro_total.setText("Ahorro de Cliente: —")
            self.lbl_semaforo.setText("✅ Margen Regular Comercial")
            self.lbl_semaforo.setStyleSheet("font-size: 10px; font-weight: 900;   border-radius: 4px; padding: 4px; border: none;")

    def _cargar_deptos(self):
        self.cmb_depto.blockSignals(True)
        self.cmb_depto.clear()
        self.cmb_depto.addItem("— Todos los departamentos —", None)
        rows = db_manager.execute_query(
            "SELECT DISTINCT departamento FROM productos "
            "WHERE departamento IS NOT NULL ORDER BY departamento"
        ) or []
        for r in rows:
            dep = r['departamento']
            if dep:
                self.cmb_depto.addItem(dep, dep)
        self.cmb_depto.blockSignals(False)

    def cargar_datos(self):
        buscar = self.txt_buscar.text().strip()
        depto  = self.cmb_depto.currentData()
        solo_promos = self.chk_ver_promos.isChecked()

        q = "SELECT * FROM productos WHERE 1=1"
        p = []
        if buscar:
            q += " AND (nombre LIKE ? OR CAST(id AS TEXT) LIKE ? OR COALESCE(codigo,'') LIKE ?)"
            p += [f"%{buscar}%"] * 3
        if depto:
            q += " AND departamento=?"
            p.append(depto)
        if solo_promos:
            q += " AND cant_oferta > 0 AND precio_oferta > 0"
            
        q += " ORDER BY departamento, nombre"

        self.all_rows = db_manager.execute_query(q, tuple(p)) or []
        self.loaded_count = 0
        self.tabla.setRowCount(0)
        
        self._cargar_siguiente_pagina()

        # Calcular stock crítico de forma rápida de la memoria sin trabar la UI
        sin_stock = sum(1 for r in self.all_rows if (r['stock'] or 0.0) <= 0)

        n = len(self.all_rows)
        self.lbl_total.setText(f"📦 {n} PRODUCTOS EN LISTA")
        self.lbl_total.setStyleSheet(" font-weight: 800; background: transparent;")
        self.lbl_stock0.setText(
            f"⚠️ Stock Crítico: {sin_stock}" if sin_stock else "✅ Stock Saludable"
        )
        self.lbl_stock0.setStyleSheet(
            f"color:{'#ef4444' if sin_stock else '#10b981'}; font-size:11px; font-weight:bold; background: transparent;"
        )

    def _on_item_changed(self, item):
        if item.column() == 0:
            row = item.row()
            id_item = self.tabla.item(row, 1)
            if id_item:
                id_p = id_item.data(Qt.UserRole)
                if not id_p: id_p = id_item.text() # Fallback
                if item.checkState() == Qt.Checked:
                    self.checked_product_ids.add(str(id_p))
                else:
                    self.checked_product_ids.discard(str(id_p))
                
                # Actualizar habilitación de botón y leyenda de footer
                num_sel = len(self.checked_product_ids)
                self.btn_imprimir_masivo.setEnabled(num_sel > 0)
                self.btn_asistente_promo.setEnabled(num_sel > 0)
                self.lbl_sel.setText(f"Seleccionados: {num_sel}" if num_sel else "")

    def _cargar_siguiente_pagina(self):
        if self.loaded_count >= len(self.all_rows):
            return
            
        inicio = self.loaded_count
        fin = min(inicio + 50, len(self.all_rows))
        
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(fin)
        
        for i in range(inicio, fin):
            r = self.all_rows[i]
            dep   = r['departamento'] or ''
            stock = r['stock'] or 0.0
            uni   = (r['unidad'] or 'UN').upper()
            tipo  = "KILO" if uni == 'KG' else "UNIDAD"

            c_of = float(r['cant_oferta'] or 0.0)
            p_of = float(r['precio_oferta'] or 0.0)
            nombre_display = r['nombre'] or ''
            if c_of > 0 and p_of > 0:
                pass # Eliminamos la inyección basura al Master Data
            # Casilla de verificación en columna 0
            it_check = QTableWidgetItem()
            it_check.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if str(r['id']) in self.checked_product_ids:
                it_check.setCheckState(Qt.Checked)
            else:
                it_check.setCheckState(Qt.Unchecked)
            self.tabla.setItem(i, 0, it_check)

            cod = r['codigo'] or ''
            id_cod_text = f"[{r['id']}]  {cod}" if cod else f"[{r['id']}]"

            vals = [
                (id_cod_text,        Qt.AlignCenter),
                (nombre_display,     Qt.AlignLeft),
                (dep,                Qt.AlignLeft),
                (f"${r['costo']:.2f}", Qt.AlignRight),
                (f"${r['precio']:.2f}", Qt.AlignRight),
                (f"{stock:.2f}",     Qt.AlignRight),
                (tipo,               Qt.AlignCenter),
                (f"{c_of:g}" if c_of > 0 else "-", Qt.AlignCenter),
                (f"${p_of:.2f}" if p_of > 0 else "-", Qt.AlignRight),
            ]

            for j_val, (v, align) in enumerate(vals):
                j = j_val + 1
                it = QTableWidgetItem(v)
                if j == 1:
                    it.setData(Qt.UserRole, str(r['id'])) # Guardar ID puro internamente
                it.setTextAlignment(Qt.AlignVCenter | align)
                it.setForeground(QColor("#1e293b"))

                if j == 2 and c_of > 0 and p_of > 0:
                    it.setForeground(QColor("#ea580c")) # Naranja destacado para promos
                    it.setFont(QFont("Segoe UI", 9, QFont.Bold))

                if j == 6: # Stock
                    if stock <= 0:
                        it.setForeground(QColor("#ef4444"))
                    elif stock < 5:
                        it.setForeground(QColor("#f59e0b"))
                    else:
                        it.setForeground(QColor("#10b981"))

                self.tabla.setItem(i, j, it)
                
        self.loaded_count = fin
        self.tabla.blockSignals(False)

    def _al_hacer_scroll(self, value):
        bar = self.tabla.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() - 15:
            self._cargar_siguiente_pagina()

    def _actualizar_sel(self):
        num_sel = len(self.checked_product_ids)
        self.btn_imprimir_masivo.setEnabled(num_sel > 0)
        self.btn_asistente_promo.setEnabled(num_sel > 0)
        self.lbl_sel.setText(f"Seleccionados: {num_sel}" if num_sel else "")

        row = self.tabla.currentRow()
        if row == -1:
            self.producto_seleccionado_id = None
            self.lbl_prod_nombre.setText("Seleccione un producto...")
            self.lbl_prod_detalles.setText("ID: —  |  PLU: —")
            self.panel_control.setEnabled(False)
            self._recargar_simulador()
            return
            
        item_id = self.tabla.item(row, 1)
        if not item_id:
            self.producto_seleccionado_id = None
            self.lbl_prod_nombre.setText("Seleccione un producto...")
            self.lbl_prod_detalles.setText("ID: —  |  PLU: —")
            self.panel_control.setEnabled(False)
            self.lbl_sel.setText("")
            self._recargar_simulador()
            return
            
        id_p = item_id.data(Qt.UserRole)
        if not id_p: id_p = item_id.text()
        rows = db_manager.execute_query("SELECT * FROM productos WHERE id=?", (id_p,)) or []
        if not rows:
            self.producto_seleccionado_id = None
            self.lbl_prod_nombre.setText("Seleccione un producto...")
            self.lbl_prod_detalles.setText("ID: —  |  PLU: —")
            self.panel_control.setEnabled(False)
            self.lbl_sel.setText("")
            self._recargar_simulador()
            return
            
        p = rows[0]
        self.producto_seleccionado_id = p['id']
        self.lbl_prod_nombre.setText(p['nombre'])
        self.lbl_prod_detalles.setText(f"ID: {p['id']}  |  PLU: {p['codigo'] or 'Sin Código'}")
        
        # Bloquear señales dinámicas temporalmente para evitar recargas múltiples al asignar valores iniciales
        self.txt_quick_precio.blockSignals(True)
        self.txt_quick_costo.blockSignals(True)
        self.sp_quick_cant_oferta.blockSignals(True)
        self.sp_quick_precio_oferta.blockSignals(True)
        self.sp_quick_oferta_relampago.blockSignals(True)
        self.sp_quick_oferta_promedio.blockSignals(True)
        
        self.txt_quick_precio.setValue(float(p['precio'] if p['precio'] is not None else 0.0))
        self.txt_quick_costo.setValue(float(p['costo'] if p['costo'] is not None else 0.0))
        self.txt_quick_stock.setValue(float(p['stock'] if p['stock'] is not None else 0.0))
        
        self.sp_quick_cant_oferta.setValue(float(p['cant_oferta'] if p['cant_oferta'] is not None else 0.0))
        self.sp_quick_precio_oferta.setValue(float(p['precio_oferta'] if p['precio_oferta'] is not None else 0.0))
        self.sp_quick_oferta_relampago.setValue(float(p.get('precio_oferta_relampago') if p.get('precio_oferta_relampago') is not None else 0.0))
        self.sp_quick_oferta_promedio.setValue(float(p.get('precio_oferta_promedio') if p.get('precio_oferta_promedio') is not None else 0.0))
        self.sp_limite_relampago.blockSignals(True)
        self.sp_limite_relampago.setValue(float(p.get('limite_oferta_relampago') if p.get('limite_oferta_relampago') is not None else 0.0))
        ventas = p.get('ventas_oferta_relampago') or 0
        limite = p.get('limite_oferta_relampago') or 0
        self.lbl_ventas_relampago.setText(f"Vendidos: {int(ventas)} / {int(limite) if limite > 0 else '∞'}")
        self.sp_limite_relampago.blockSignals(False)
        
        self.txt_quick_precio.blockSignals(False)
        self.txt_quick_costo.blockSignals(False)
        
        self.sp_quick_cant_oferta.blockSignals(False)
        self.sp_quick_precio_oferta.blockSignals(False)
        self.sp_quick_oferta_relampago.blockSignals(False)
        self.sp_quick_oferta_promedio.blockSignals(False)
            
        self.panel_control.setEnabled(True)
        self.lbl_sel.setText("Seleccionado: 1")
        self._recargar_simulador()

    def _quick_stock_adjust(self, value):
        if not self.producto_seleccionado_id: return
        cur_val = self.txt_quick_stock.value()
        new_val = max(0.0, cur_val + value)
        self.txt_quick_stock.setValue(new_val)

    def _guardar_cambios_rapidos(self):
        if not self.producto_seleccionado_id: return
        precio = self.txt_quick_precio.value()
        costo = self.txt_quick_costo.value()
        stock = self.txt_quick_stock.value()
        
        ok = db_manager.execute_non_query(
            "UPDATE productos SET precio=?, costo=?, stock=? WHERE id=?",
            (precio, costo, stock, self.producto_seleccionado_id)
        )
        if ok:
            self.cargar_datos()
            self._re_select_product_by_id(self.producto_seleccionado_id)
            QMessageBox.information(self, "Ajuste Guardado", "¡Cambios rápidos aplicados con éxito!")
        else:
            QMessageBox.warning(self, "Error", "No se pudo actualizar el producto.")

    def _guardar_oferta_rapida(self):
        if not self.producto_seleccionado_id: return
        cant = self.sp_quick_cant_oferta.value()
        prec = self.sp_quick_precio_oferta.value()
        relampago = self.sp_quick_oferta_relampago.value()
        limite_relampago = self.sp_limite_relampago.value()
        promedio = self.sp_quick_oferta_promedio.value()
        
        if cant <= 0 and prec <= 0 and relampago <= 0 and promedio <= 0:
            QMessageBox.warning(self, "Error", "Debe configurar al menos un precio de oferta mayor a cero.")
            return
            
        ok = db_manager.execute_non_query(
            "UPDATE productos SET cant_oferta=?, precio_oferta=?, precio_oferta_relampago=?, precio_oferta_promedio=?, limite_oferta_relampago=? WHERE id=?",
            (cant, prec, relampago, promedio, limite_relampago, self.producto_seleccionado_id)
        )
        if ok:
            self.cargar_datos()
            self._re_select_product_by_id(self.producto_seleccionado_id)
            QMessageBox.information(self, "Oferta Activada", "¡Promociones guardadas y sincronizadas!")
        else:
            QMessageBox.warning(self, "Error", "No se pudieron activar las promociones.")

    def _quitar_oferta_rapida(self):
        if not self.producto_seleccionado_id: return
        ok = db_manager.execute_non_query(
            "UPDATE productos SET cant_oferta=0, precio_oferta=0, precio_oferta_relampago=0, precio_oferta_promedio=0, limite_oferta_relampago=0, ventas_oferta_relampago=0 WHERE id=?",
            (self.producto_seleccionado_id,)
        )
        if ok:
            self.sp_quick_cant_oferta.setValue(0.0)
            self.sp_quick_precio_oferta.setValue(0.0)
            self.sp_quick_oferta_relampago.setValue(0.0)
            self.sp_limite_relampago.setValue(0.0)
            self.lbl_ventas_relampago.setText("Vendidos: 0 / ∞")
            self.sp_quick_oferta_promedio.setValue(0.0)
            self.cargar_datos()
            self._re_select_product_by_id(self.producto_seleccionado_id)
            QMessageBox.information(self, "Oferta Quitada", "Promociones removidas con éxito.")
        else:
            QMessageBox.warning(self, "Error", "No se pudo quitar la promoción.")

    def _re_select_product_by_id(self, prod_id):
        self.tabla.blockSignals(True)
        for row in range(self.tabla.rowCount()):
            item = self.tabla.item(row, 1)
            if item:
                id_p = item.data(Qt.UserRole)
                if not id_p: id_p = item.text()
                if str(id_p) == str(prod_id):
                    self.tabla.selectRow(row)
                    self.tabla.setCurrentItem(item)
                    break
        self.tabla.blockSignals(False)

    def _imprimir_cartel_a4_rapido(self):
        if not self.producto_seleccionado_id:
            QMessageBox.warning(self, "Aviso", "Por favor, seleccione un producto de la lista primero.")
            return

        nombre = self.lbl_prod_nombre.text().replace("<b>Producto:</b> ", "").strip()
        id_p = str(self.producto_seleccionado_id)
        
        c_of = self.sp_quick_cant_oferta.value()
        p_of = self.sp_quick_precio_oferta.value()
        
        # Obtener unidad desde la BD
        rows = db_manager.execute_query("SELECT unidad FROM productos WHERE id=?", (id_p,))
        if rows and rows[0]['unidad'] and 'KG' in str(rows[0]['unidad']).upper():
            t_u = "Kilos"
        else:
            t_u = "Unidades"
        
        if c_of <= 0 or p_of <= 0:
            QMessageBox.warning(self, "Aviso", "⚠️ Para imprimir un cartel, el producto debe tener una promoción activa (Cantidad y Precio de Oferta mayores a cero).")
            return
            
        p_reg_val = self.txt_quick_precio.value()
        
        if t_u.lower() == "kilos":
            c_of_str = f"Desde {c_of:g} Kilos"
            es_kilos = True
        else:
            c_of_str = f"Llevando {int(c_of)} Unidades"
            es_kilos = False

        # Diálogo para elegir tamaño y leyenda comercial
        dlg = QDialog(self)
        dlg.setWindowTitle("Opciones de Impresión de Cartel")
        dlg.setFixedSize(400, 260)
        dlg.setStyleSheet("""
            QDialog { background: white;  font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton {  background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; }
            QPushButton:hover {  }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;  background: white; }
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        
        lay.addWidget(QLabel(f"<b>Producto:</b> {nombre}"))
        
        cmb_formato = QComboBox()
        cmb_formato.addItem("🎴 A6 Chico (4 por hoja - Recomendado)", "a6_grid")
        cmb_formato.addItem("🏷️ A8 Mini (8 por hoja - Especial Góndola)", "a8_grid")
        cmb_formato.addItem("📑 A5 Mediano (2 por hoja)", "a5_horizontal")
        cmb_formato.addItem("📄 A4 Grande (1 por hoja)", "a4_vertical")
        
        lay.addWidget(QLabel("<b>Tamaño / Distribución (Ahorro de papel):</b>"))
        lay.addWidget(cmb_formato)
        
        lay.addWidget(QLabel("<b>Leyenda de Promoción:</b>"))
        sug_leyenda = "¡OFERTA X KILO!" if es_kilos else (f"x{int(c_of)}" if c_of >= 2 else "¡OFERTA ESPECIAL!")
        txt_leyenda = QLineEdit(sug_leyenda)
        lay.addWidget(txt_leyenda)
        
        btn_ok = QPushButton("✔ Generar y Abrir Cartel")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        lay.addSpacing(10); lay.addWidget(btn_ok)

        if dlg.exec_():
            try:
                from src.services.etiquetas.renderer import EtiquetaRenderer, abrir_archivo_pdf
            except ImportError:
                try:
                    from services.etiquetas.renderer import EtiquetaRenderer, abrir_archivo_pdf
                except ImportError:
                    QMessageBox.critical(self, "Error", "No se pudo cargar el generador de etiquetas.")
                    return

            formato_sel = cmb_formato.currentData()
            
            repeticiones = 1
            if formato_sel == "a5_horizontal":
                repeticiones = 2
            elif formato_sel == "a6_grid":
                repeticiones = 4
            elif formato_sel == "a8_grid":
                repeticiones = 8

            item_oferta = {
                "id": id_p,
                "nombre": nombre,
                "precio_regular": f"{p_reg_val:.2f}",
                "tipo_promo": txt_leyenda.text().upper().strip(),
                "condicion_venta": c_of_str,
                "precio_oferta": f"{p_of:.2f}",
                "formato": formato_sel
            }
            
            lote = [item_oferta] * repeticiones
            
            try:
                ren = EtiquetaRenderer()
                pdf_path = ren.generar_pdf_ofertas(lote)
                abrir_archivo_pdf(pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo generar ni abrir el cartel: {e}")

    def _imprimir_cartelera_masiva(self):
        if not self.checked_product_ids:
            QMessageBox.warning(self, "Aviso", "Por favor, marque al menos un producto con la casilla [🗹].")
            return
            
        productos_promos = []
        placeholders = ",".join(["?"] * len(self.checked_product_ids))
        rows = db_manager.execute_query(
            f"SELECT * FROM productos WHERE id IN ({placeholders})",
            tuple(self.checked_product_ids)
        ) or []
        
        for p in rows:
            c_of = float(p['cant_oferta'] or 0.0)
            p_of = float(p['precio_oferta'] or 0.0)
            if c_of > 0 and p_of > 0:
                productos_promos.append(p)
                        
        if not productos_promos:
            QMessageBox.warning(
                self, "Aviso", 
                "⚠️ Ninguno de los productos marcados tiene una promoción activa en la base de datos.\n\n"
                "Para imprimir cartelera masiva, asegúrese de que tengan Cantidad y Precio de Oferta mayores a cero."
            )
            return
            
        dlg = QDialog(self)
        dlg.setWindowTitle("Impresión de Cartelera Masiva (Libro)")
        dlg.setFixedSize(450, 320)
        dlg.setStyleSheet("""
            QDialog { background: white;  font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton {  background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; }
            QPushButton:hover {  }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;  background: white; }
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        
        lbl_info = QLabel(
            f"📚 <b>Se detectaron {len(productos_promos)} promociones activas</b> de los productos seleccionados."
        )
        lbl_info.setWordWrap(True)
        lay.addWidget(lbl_info)
        
        lay.addWidget(QLabel("<b>Tamaño y Distribución de los Carteles:</b>"))
        cmb_formato = QComboBox()
        cmb_formato.addItem("🎴 A6 Chico (4 por hoja - Recomendado)", "a6_grid")
        cmb_formato.addItem("🏷️ A8 Mini (8 por hoja - Especial Góndola)", "a8_grid")
        cmb_formato.addItem("📑 A5 Mediano (2 por hoja)", "a5_horizontal")
        cmb_formato.addItem("📄 A4 Grande (1 por hoja)", "a4_vertical")
        lay.addWidget(cmb_formato)
        
        lay.addWidget(QLabel("<b>Leyenda Comercial por Defecto:</b>"))
        txt_leyenda = QLineEdit("🔥 SUPER OFERTA")
        lay.addWidget(txt_leyenda)
        
        lay.addSpacing(10)
        btn_ok = QPushButton(f"✔ Generar Libro de {len(productos_promos)} Páginas y Abrir")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        lay.addWidget(btn_ok)
        
        if dlg.exec_():
            try:
                from src.services.etiquetas.renderer import EtiquetaRenderer, abrir_archivo_pdf
            except ImportError:
                try:
                    from services.etiquetas.renderer import EtiquetaRenderer, abrir_archivo_pdf
                except ImportError:
                    QMessageBox.critical(self, "Error", "No se pudo cargar el generador de etiquetas.")
                    return

            formato_sel = cmb_formato.currentData()
            
            lote_ofertas = []
            for p in productos_promos:
                c_of = float(p['cant_oferta'] or 0.0)
                p_of = float(p['precio_oferta'] or 0.0)
                p_reg = float(p['precio'] or 0.0)
                
                try:
                    t_u = p['tipo_unidad_oferta']
                    if not t_u: t_u = "Unidades"
                except:
                    t_u = "Unidades"
                
                if t_u.lower() == "kilos":
                    c_of_str = f"Desde {c_of:g} Kilos"
                else:
                    c_of_str = f"Llevando {int(c_of)} Unidades"

                lote_ofertas.append({
                    "id": str(p['id']),
                    "nombre": p['nombre'],
                    "precio_regular": f"{p_reg:.2f}",
                    "tipo_promo": txt_leyenda.text().upper().strip(),
                    "condicion_venta": c_of_str,
                    "precio_oferta": f"{p_of:.2f}",
                    "formato": formato_sel
                })

            try:
                ren = EtiquetaRenderer()
                pdf_path = ren.generar_pdf_ofertas(lote_ofertas)
                abrir_archivo_pdf(pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo generar ni abrir la cartelera: {e}")

    def _crear_folleto_pdf(self):
        # Obtener todas las ofertas activas en la base de datos por defecto
        # (donde cant_oferta > 0 y precio_oferta > 0)
        rows_db = db_manager.execute_query(
            "SELECT * FROM productos WHERE cant_oferta > 0 AND precio_oferta > 0 ORDER BY departamento, nombre"
        ) or []
        
        has_checked = len(self.checked_product_ids) > 0
        
        # Diálogo de opciones del folleto
        dlg = QDialog(self)
        dlg.setWindowTitle("Creación de Folleto de Ofertas (PDF)")
        dlg.setFixedSize(480, 360)
        dlg.setStyleSheet("""
            QDialog { background: white;  font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton {  background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; font-size: 12px; }
            QPushButton:hover {  }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;  background: white; }
            QRadioButton { spacing: 8px; font-weight: bold; }
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        
        lbl_tit = QLabel("📰 CREAR VOLANTE PUBLICITARIO (PDF)")
        lbl_tit.setStyleSheet(" font-size: 15px; font-weight: 900; letter-spacing: 0.5px;")
        lay.addWidget(lbl_tit)
        
        # Formulario
        form = QFormLayout()
        form.setSpacing(10)
        
        txt_titulo = QLineEdit("🔥 GRAN BARATILLO DE OFERTAS 🔥")
        txt_titulo.setPlaceholderText("Título del folleto...")
        txt_titulo.setMinimumWidth(260)
        
        txt_negocio = QLineEdit("MINI-SÚPER ELITE")
        # Leer el nombre del negocio desde config.json (fuente correcta de configuración)
        try:
            from src.config import config as _cfg
            nombre_neg = _cfg.get("business_name", "")
            if nombre_neg:
                txt_negocio.setText(nombre_neg.upper())
        except Exception:
            pass
            
        cmb_diseno = QComboBox()
        cmb_diseno.addItem("🖼️ Grilla de Tarjetas (6 por Pág.)", "grilla")
        cmb_diseno.addItem("📋 Lista de Precios Compacta", "lista")
        
        form.addRow("<b>Título Principal:</b>", txt_titulo)
        form.addRow("<b>Nombre del Negocio:</b>", txt_negocio)
        form.addRow("<b>Diseño del PDF:</b>", cmb_diseno)
        lay.addLayout(form)
        
        # Opciones de inclusión
        lay.addWidget(QLabel("<b>¿Qué productos incluir?</b>"))
        lay_inc = QVBoxLayout()
        rb_all = QRadioButton(f"Todas las promociones vigentes ({len(rows_db)} detectadas)")
        rb_all.setChecked(True)
        
        rb_sel = QRadioButton(f"Solo los productos marcados [🗹] ({len(self.checked_product_ids)} seleccionados)")
        rb_sel.setEnabled(has_checked)
        if has_checked:
            rb_sel.setChecked(True)
            
        lay_inc.addWidget(rb_all)
        lay_inc.addWidget(rb_sel)
        lay.addLayout(lay_inc)
        
        btn_ok = QPushButton("✔ Generar Volante PDF y Abrir")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        lay.addSpacing(10)
        lay.addWidget(btn_ok)
        
        if dlg.exec_():
            # Determinar qué productos procesar
            productos_a_procesar = []
            if rb_sel.isChecked():
                # Filtrar de la base de datos los seleccionados
                placeholders = ",".join(["?"] * len(self.checked_product_ids))
                rows_filtradas = db_manager.execute_query(
                    f"SELECT * FROM productos WHERE id IN ({placeholders})",
                    tuple(self.checked_product_ids)
                ) or []
                for p in rows_filtradas:
                    # Deben tener promo activa
                    c_of = float(p['cant_oferta'] or 0.0)
                    p_of = float(p['precio_oferta'] or 0.0)
                    if c_of > 0 and p_of > 0:
                        productos_a_procesar.append(p)
            else:
                productos_a_procesar = rows_db
                
            if not productos_a_procesar:
                QMessageBox.warning(
                    self, "Aviso",
                    "⚠️ No hay productos con ofertas activas que cumplan con la selección."
                )
                return
                
            # Mapear a formato del renderizador
            lote_ofertas = []
            for p in productos_a_procesar:
                c_of = float(p['cant_oferta'] or 0.0)
                p_of = float(p['precio_oferta'] or 0.0)
                p_reg = float(p['precio'] or 0.0)
                
                try:
                    t_u = p['tipo_unidad_oferta'] or "Unidades"
                except:
                    t_u = "Unidades"
                
                if t_u.lower() == "kilos":
                    c_of_str = f"Desde {c_of:g} Kilos"
                else:
                    c_of_str = f"Llevando {int(c_of)} Unidades"
                    
                lote_ofertas.append({
                    "id": str(p['id']),
                    "nombre": p['nombre'],
                    "precio_regular": f"{p_reg:.2f}",
                    "condicion_venta": c_of_str,
                    "precio_oferta": f"{p_of:.2f}"
                })
                
            try:
                from src.services.etiquetas.renderer import EtiquetaRenderer, abrir_archivo_pdf
                ren = EtiquetaRenderer()
                pdf_path = ren.generar_pdf_folleto_ofertas(
                    lote_ofertas=lote_ofertas,
                    titulo_folleto=txt_titulo.text().strip(),
                    negocio=txt_negocio.text().strip(),
                    diseno_tipo=cmb_diseno.currentData()
                )
                abrir_archivo_pdf(pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo al generar folleto PDF: {e}")

    def _configurar_ofertas_secuencial(self):
        if not self.checked_product_ids:
            QMessageBox.warning(self, "Aviso", "Por favor, marque al menos un producto con la casilla [🗹].")
            return
            
        placeholders = ",".join(["?"] * len(self.checked_product_ids))
        seleccionados = db_manager.execute_query(
            f"SELECT * FROM productos WHERE id IN ({placeholders})",
            tuple(self.checked_product_ids)
        ) or []
        
        if not seleccionados:
            QMessageBox.warning(self, "Aviso", "No se encontraron los productos seleccionados.")
            return

        # LÍMITE INDUSTRIAL DE SEGURIDAD CONTRA TRABAS
        LIMIT_MAX = 50
        if len(seleccionados) > LIMIT_MAX:
            QMessageBox.warning(
                self, 
                "Límite de Impresión Excedido", 
                f"⚠️ Lote de Impresión Demasiado Grande\n\n"
                f"El límite de seguridad es de {LIMIT_MAX} etiquetas.\n"
                f"Seleccionaste: {len(seleccionados)} etiquetas."
            )
            return

        negocio_default = "MACIEL"
        try:
            from src.config import config as _cfg
            nombre_neg = _cfg.get("business_name", "")
            if nombre_neg:
                negocio_default = nombre_neg.upper()
        except Exception:
            pass

        # Diálogo para Rubro y Negocio global del asistente
        dlg_marca = QDialog(self)
        dlg_marca.setWindowTitle("Configuración de Marca")
        dlg_marca.setFixedSize(380, 200)
        dlg_marca.setStyleSheet("""
            QDialog { background: white;  font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton {  background-color: #3b82f6; color: white; font-weight: bold; padding: 8px; border-radius: 6px; }
            QPushButton:hover {  }
            QLineEdit { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; }
        """)
        lay_m = QVBoxLayout(dlg_marca)
        lay_m.addWidget(QLabel("<b>Rubro Comercial:</b>"))
        txt_rub = QLineEdit("CARNICERÍA")
        lay_m.addWidget(txt_rub)
        lay_m.addWidget(QLabel("<b>Nombre de Negocio:</b>"))
        txt_neg = QLineEdit(negocio_default)
        lay_m.addWidget(txt_neg)
        
        btn_m_ok = QPushButton("✔ Siguiente")
        btn_m_ok.clicked.connect(dlg_marca.accept)
        lay_m.addWidget(btn_m_ok)
        
        if not dlg_marca.exec_():
            return
            
        rubro = txt_rub.text().strip().upper() or "CARNICERÍA"
        negocio = txt_neg.text().strip().upper() or "MACIEL"

        lote_ofertas = []
        for idx, prod in enumerate(seleccionados, 1):
            dlg = QDialog(self)
            dlg.setWindowTitle(f"Calibrador de Oferta ({idx}/{len(seleccionados)})")
            dlg.setFixedSize(480, 360)
            
            dlg.setStyleSheet("""
                QDialog {   font-family: 'Segoe UI', sans-serif; }
                QLabel {  }
                QLineEdit, QComboBox { background-color: white;  padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; }
                QLineEdit:focus, QComboBox:focus { border: 2px solid #ea580c; }
                QRadioButton {  font-size: 13px; }
                QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:1 #f97316); color: white; font-weight: bold; padding: 12px 24px; border-radius: 8px; border: none; font-size: 13px; }
                QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c2410c, stop:1 #ea580c); }
            """)
            
            lay = QVBoxLayout(dlg)
            lay.setContentsMargins(25, 25, 25, 25)
            lay.setSpacing(20)
            
            header_frame = QFrame()
            header_frame.setStyleSheet("background-color: white; border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px;")
            hf_lay = QVBoxLayout(header_frame)
            hf_lay.setContentsMargins(10, 10, 10, 10)
            hf_lay.setSpacing(6)
            
            lbl_prod = QLabel(f"<span style=' font-size:11px; font-weight:bold;'>PROCESANDO</span><br><span style='font-size:16px; font-weight:900;'>{prod['nombre']}</span>")
            lbl_prod.setWordWrap(True)
            lbl_pr = QLabel(f"<span style=''>Precio Regular:</span> <span style=' font-weight:bold;'>${prod['precio']:.2f}</span>")
            hf_lay.addWidget(lbl_prod)
            hf_lay.addWidget(lbl_pr)
            
            lay.addWidget(header_frame)
            
            form = QFormLayout()
            form.setSpacing(12)
            
            cmb_tipo = QComboBox()
            cmb_tipo.addItems(["OFERTA", "SUPER OFERTA", "x2", "x3", "LLEVAS 2 PAGAS 1", "LLEVAS 3 PAGAS 2", "PROMO ESPECIAL"])
            cmb_tipo.setEditable(True)
            
            sug_p = prod['precio_oferta'] if (prod['precio_oferta'] and prod['precio_oferta'] > 0) else prod['precio']
            txt_precio_of = QLineEdit(f"{sug_p:.2f}")
            
            cmb_formato = QComboBox()
            cmb_formato.addItem("🎴 A6 Chico (4 por hoja - Recomendado)", "a6_grid")
            cmb_formato.addItem("🏷️ A8 Mini (8 por hoja - Especial Góndola)", "a8_grid")
            cmb_formato.addItem("📑 A5 Mediano (2 por hoja)", "a5_horizontal")
            cmb_formato.addItem("📄 A4 Grande (1 por hoja)", "a4_vertical")
            
            form.addRow("Tipo de Promoción:", cmb_tipo)
            form.addRow("Precio de Oferta ($):", txt_precio_of)
            form.addRow("Tamaño / Distribución:", cmb_formato)
            lay.addLayout(form)
            
            lay.addStretch()
            
            bx_btn = QHBoxLayout()
            btn_ok = QPushButton("Calibrar Siguiente Producto ➡" if idx < len(seleccionados) else "🏭 Iniciar Prensa Industrial (PDF)")
            btn_ok.setCursor(Qt.PointingHandCursor)
            btn_ok.clicked.connect(dlg.accept)
            bx_btn.addStretch(); bx_btn.addWidget(btn_ok)
            lay.addLayout(bx_btn)
            
            if dlg.exec_():
                lote_ofertas.append({
                    "id": str(prod["id"]),
                    "nombre": prod["nombre"],
                    "precio_regular": f"{prod['precio']:.2f}",
                    "tipo_promo": cmb_tipo.currentText().upper(),
                    "precio_oferta": txt_precio_of.text().replace("$", "").strip(),
                    "formato": cmb_formato.currentData()
                })
            else:
                return
            
        if lote_ofertas:
            try:
                from src.services.etiquetas.renderer import EtiquetaRenderer, abrir_archivo_pdf
                renderer = EtiquetaRenderer()
                pdf_path = renderer.generar_pdf_ofertas(lote_ofertas, rubro=rubro, negocio=negocio)
                abrir_archivo_pdf(pdf_path)
            except Exception as ex:
                QMessageBox.critical(self, "Error", f"Fallo al construir PDF de ofertas: {ex}")
