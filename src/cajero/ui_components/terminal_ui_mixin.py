import os
from datetime import datetime
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QHeaderView, QFrame, QAbstractItemView, QListWidget, QPushButton, QWidget, QGraphicsDropShadowEffect, QGridLayout, QComboBox, QDoubleSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from src.config import config
try:
    from src.ui_components.virtual_keyboard_paso5 import VirtualKeyboardPaso5 as VirtualKeyboard
    HAS_KEYBOARD = True
except:
    HAS_KEYBOARD = False

class TerminalUIMixin:
    def setup_ui(self):
        self.setStyleSheet("background-color: #F8FAFC; color: #333333; font-family: 'Inter', 'Segoe UI Variable', 'Segoe UI', sans-serif;")
        # Layout principal con márgenes para que nada toque los bordes ("el techo y el piso")
        # Layout principal con márgenes suaves
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(75)
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #3B82F6); 
                color: white; 
                border-radius: 12px;
            }
            QLabel { background: transparent; color: #F8FAFC; }
        """)
        header_layout = QHBoxLayout(self.header_frame)
        
        col1 = QVBoxLayout(); col1.setSpacing(0)
        self.lbl_estado = QLabel("Estado:           MAESTRA")
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_instalacion = QLabel("№ 0000-0000-0000")
        self.lbl_instalacion.setStyleSheet("font-weight: bold; font-size: 14px;")
        col1.addWidget(self.lbl_estado)
        col1.addWidget(self.lbl_instalacion)
        header_layout.addLayout(col1)
        
        header_layout.addSpacing(40)
        
        col2 = QVBoxLayout(); col2.setSpacing(0)
        
        # Fila para el indicador LED y el número de caja
        row_caja = QHBoxLayout()
        row_caja.setSpacing(8)
        row_caja.setContentsMargins(0, 0, 0, 0)
        
        # LED indicador circular (inicialmente verde)
        self.led_status = QLabel()
        self.led_status.setFixedSize(14, 14)
        self.led_status.setStyleSheet("background-color: #10B981; border-radius: 7px; border: 1.5px solid rgba(255,255,255,0.5);")
        row_caja.addWidget(self.led_status, 0, Qt.AlignVCenter)
        
        self.lbl_caja_num = QLabel("Caja №:        [01] SERVER")
        self.lbl_caja_num.setStyleSheet("font-weight: bold; font-size: 14px;")
        row_caja.addWidget(self.lbl_caja_num)
        row_caja.addStretch()
        
        col2.addLayout(row_caja)
        
        self.lbl_fecha = QLabel(f"Fecha:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.lbl_fecha.setStyleSheet("font-weight: bold; font-size: 14px;")
        col2.addWidget(self.lbl_fecha)
        header_layout.addLayout(col2)
        
        header_layout.addStretch()
        
        # --- CAMPANA DE ALERTAS ---
        self.btn_campana = QPushButton("🔔")
        self.btn_campana.setFixedSize(40, 40)
        self.btn_campana.setCursor(Qt.PointingHandCursor)
        self.btn_campana.setFocusPolicy(Qt.NoFocus)
        self.btn_campana.setStyleSheet("background: transparent; border: none; font-size: 24px;")
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        self.campana_op_effect = QGraphicsOpacityEffect(self.btn_campana)
        self.campana_op_effect.setOpacity(0.0) # Camuflado por defecto
        self.btn_campana.setGraphicsEffect(self.campana_op_effect)
        self.btn_campana.clicked.connect(self._click_campana_alertas)
        header_layout.addWidget(self.btn_campana)
        
        title = config.get('business_name', 'Punto de Venta [20.09.02]')
        self.lbl_terminal_title = QLabel(title)
        self._orig_title = title
        self.lbl_terminal_title.setStyleSheet("font-size: 26px; font-weight: bold;")
        header_layout.addWidget(self.lbl_terminal_title)
        
        # --- INDICADOR DE RED (HEARTBEAT) ---
        self.lbl_red_status = QLabel("⚫")
        self.lbl_red_status.setToolTip("Estado de Conexión LAN")
        self.lbl_red_status.setStyleSheet("font-size: 16px; margin-left: 10px; color: gray;")
        self.lbl_red_status.setCursor(Qt.PointingHandCursor)
        self.lbl_red_status.mousePressEvent = self._show_connection_info
        header_layout.addWidget(self.lbl_red_status)
        
        self.main_layout.addWidget(self.header_frame)
        
        # --- BARRA DE ALERTA STOCK MÍNIMO ---
        self.stock_alert_bar = QFrame()
        self.stock_alert_bar.setFixedHeight(36)
        self.stock_alert_bar.setStyleSheet("background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 6px;")
        self.stock_alert_bar.hide()
        sa_lay = QHBoxLayout(self.stock_alert_bar)
        sa_lay.setContentsMargins(15, 0, 15, 0)
        self.lbl_stock_alert = QLabel("🔔 Alerta de Stock: Hay productos por debajo del mínimo")
        self.lbl_stock_alert.setStyleSheet("color: #D97706; font-weight: bold; font-size: 14px; border: none;")
        sa_lay.addWidget(self.lbl_stock_alert)
        self.main_layout.addWidget(self.stock_alert_bar)

        
        # Inicializar barra de estado con datos reales
        self.refresh_status_bar()

        # --- CENTRO (TABLA Y FOOTER JUNTOS) ---
        self.central_frame = QFrame()
        self.central_frame.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #CBD5E1;")
        central_layout = QVBoxLayout(self.central_frame)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # --- TABLA CENTRAL ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "DESCRIPCION PRODUCTO", "PRECIO", "CANT", "DES. TOTAL", "TOTAL"])
        self.tabla.setStyleSheet("""
            QTableWidget { 
                background-color: white;
                alternate-background-color: #F8FAFC;
                color: #1E293B; 
                gridline-color: transparent;
                border: none; 
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: 19px; 
                font-weight: 800; 
                selection-background-color: #EFF6FF;
                selection-color: #1E3A8A; 
                outline: none; /* Elimina el feo cuadro punteado nativo al seleccionar una celda */
            }
            QTableWidget::item {
                padding: 8px 15px; 
                border-bottom: 1px solid #E2E8F0;
            }
            QTableWidget::item:hover {
                background-color: #F1F5F9;
            }
            QTableWidget::item:selected {
                background-color: #1E3A8A; 
                color: #FFFFFF;
                font-weight: 900;
            }
            QHeaderView::section { 
                background-color: #F8FAFC; 
                color: #475569; 
                border: none; 
                border-bottom: 3px solid #E2E8F0;
                padding: 16px 15px; 
                font-weight: 900; 
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed) # Bloquear columnas numéricas para evitar que Qt las exprima
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Solo la descripción se estira dinámicamente
        
        # Distribuir anchos de columna profesionales y bloqueados (Garantía Cero Truncamientos)
        self.tabla.setColumnWidth(0, 100) # ID / Barcode (100px)
        self.tabla.setColumnWidth(2, 280) # PRECIO (280px)
        self.tabla.setColumnWidth(3, 120) # CANT (120px)
        self.tabla.setColumnWidth(4, 250) # DES. TOTAL (250px)
        self.tabla.setColumnWidth(5, 350) # SUBTOTAL (350px)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(55) # Mayor respiro para los items (Evita que estén muy unidos)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.installEventFilter(self) # BINDING INDUSTRIAL PARA ENTER EN LA TABLA
        central_layout.addWidget(self.tabla)
        
        self.main_layout.addWidget(self.central_frame)

        # --- BOTTOM DASHBOARD ---
        self.dashboard_frame = QFrame()
        self.dashboard_frame.setFixedHeight(140)
        self.dashboard_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; border: 1px solid #CBD5E1;")
        dash_layout = QHBoxLayout(self.dashboard_frame)
        dash_layout.setContentsMargins(10, 5, 10, 5)
        
        # F1-Barcode
        f1_box = QFrame()
        f1_box.setFixedWidth(420)
        f1_box.setStyleSheet("border: none;")
        f1_l = QVBoxLayout(f1_box)
        f1_l.setContentsMargins(5, 15, 5, 15)
        f1_l.setSpacing(0)
        
        self.txt_scan = QLineEdit()
        self.txt_scan.setPlaceholderText("🔍 Código o Producto (F1)...")
        self.txt_scan.setStyleSheet("""
            QLineEdit {
                background: white; border: 3px solid #3B82F6; border-radius: 12px; 
                color: #1E3A8A; font-size: 34px; padding: 12px; font-weight: 900;
            }
        """)
        
        # Efecto de Brillo Industrial (Neon Glow)
        glow = QGraphicsDropShadowEffect(self.txt_scan)
        glow.setBlurRadius(20)
        glow.setColor(QColor(59, 130, 246, 150))
        glow.setOffset(0, 0)
        self.txt_scan.setGraphicsEffect(glow)

        self.txt_scan.textChanged.connect(self.actualizar_busqueda)
        self.txt_scan.returnPressed.connect(self.procesar_scan)
        
        f1_l.addWidget(self.txt_scan)
        dash_layout.addWidget(f1_box)
        
        # Overlay de Búsqueda
        self.list_results = QListWidget(self)
        self.list_results.setStyleSheet("background: white; border: 2px solid #437EE8; color: #333333; font-size: 22px; font-weight: bold;")
        self.list_results.itemClicked.connect(self.seleccionar_item_busqueda)
        self.list_results.installEventFilter(self)
        self.list_results.hide()
        
        # Cantidad (Oculto a petición para dar más espacio al total)
        self.lbl_cant_val = QLabel("0")
        self.lbl_cant_val.hide()
        # cant_box = QVBoxLayout()
        # cant_box.setSpacing(0)
        # lbl_cant_tit = QLabel("Cantidad")
        # lbl_cant_tit.setStyleSheet("color: #64748B; font-size: 24px; font-weight: bold; border: none;")
        # self.lbl_cant_val.setStyleSheet("font-size: 70px; color: #1C2E85; font-weight: bold; border: none;")
        # cant_box.addWidget(lbl_cant_tit)
        # cant_box.addWidget(self.lbl_cant_val)
        dash_layout.addStretch()
        
        # Ahorro Label (Contenedor para la animación de Ahorro / Descuento)
        self.lbl_ahorro_val = QLabel("")
        self.lbl_ahorro_val.setStyleSheet("font-size: 42px; color: #FF4500; font-weight: 900; border: none;")
        self.lbl_ahorro_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.ahorro_glow = QGraphicsDropShadowEffect(self.lbl_ahorro_val)
        self.ahorro_glow.setBlurRadius(20)
        self.ahorro_glow.setColor(QColor(255, 69, 0, 150)) # Brillo naranja vibrante
        self.ahorro_glow.setOffset(0, 0)
        self.lbl_ahorro_val.setGraphicsEffect(self.ahorro_glow)
        
        self.lbl_ahorro_val.hide()

        self.lbl_total_val = QLabel("0")
        self.lbl_total_val.setStyleSheet("font-size: 75px; color: #059669; font-weight: 900; border: none;")
        self.lbl_total_val.setAlignment(Qt.AlignRight)
        
        # Agrupar Ahorro y Total lado a lado en un contenedor horizontal perfectamente centrado verticalmente
        self.totales_container = QHBoxLayout()
        self.totales_container.setSpacing(35)
        self.totales_container.addWidget(self.lbl_total_val, alignment=Qt.AlignVCenter)
        self.totales_container.addWidget(self.lbl_ahorro_val, alignment=Qt.AlignVCenter)
        dash_layout.addLayout(self.totales_container)
        
        dash_layout.addSpacing(10)
        
        # Sidebar Resumen (Persistencia de última venta)
        self.side_box = QFrame()
        self.side_box.setFixedWidth(240)
        self.side_box.setStyleSheet("""
            QFrame {
                background: #f8fafc; 
                border: 1px solid #e2e8f0; 
                border-radius: 12px;
            }
            QLabel { border: none; background: transparent; }
        """)
        sl = QVBoxLayout(self.side_box)
        sl.setContentsMargins(15, 10, 15, 10)
        sl.setSpacing(5)
        
        self.lbl_side_cant = QLabel("CANTIDAD:       0.00")
        self.lbl_side_total = QLabel("TOTAL VENTA:    0.00")
        self.lbl_side_pagos = QLabel("PAGOS:          0.00")
        self.lbl_side_cambio = QLabel("CAMBIO:         0.00")
        
        for l in [self.lbl_side_cant, self.lbl_side_total, self.lbl_side_pagos, self.lbl_side_cambio]:
            l.setStyleSheet("font-size: 14px; color: #475569; font-weight: 800; font-family: 'Consolas', monospace;")
            sl.addWidget(l)
            
        # Resaltar Cambio
        self.lbl_side_cambio.setStyleSheet("font-size: 16px; color: #10b981; font-weight: 900; font-family: 'Consolas', monospace;")
        
        dash_layout.addWidget(self.side_box)
        
        self.en_venta = False
        self.main_layout.addWidget(self.dashboard_frame)
        
        # --- BARRA DE ESTADO / COMANDOS (EL PISO) ---
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(55) # Taller status bar for touch screens
        self.status_bar.setStyleSheet("background: #0F172A; border-top: 1px solid #334155;")
        sl = QHBoxLayout(self.status_bar); sl.setContentsMargins(15, 0, 5, 0)
        
        if HAS_KEYBOARD:
            self.btn_teclado = QPushButton("⌨️ TECLADO")
            self.btn_teclado.setFixedHeight(40)
            self.btn_teclado.setCursor(Qt.PointingHandCursor)
            self.btn_teclado.setFocusPolicy(Qt.NoFocus)
            self.btn_teclado.setStyleSheet("""
                QPushButton {
                    background: #1E293B; color: #F8FAFC; border-radius: 5px;
                    font-size: 12px; font-weight: bold; border: 1px solid #334155;
                    padding: 0px 12px;
                }
                QPushButton:hover { background: #334155; border-color: #475569; }
            """)
            self.btn_teclado.clicked.connect(self.toggle_keyboard)
            sl.addWidget(self.btn_teclado)
            sl.addSpacing(10)

        self.btn_theme = QPushButton()
        self.btn_theme.setFixedHeight(40)
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setFocusPolicy(Qt.NoFocus)
        self.btn_theme.setStyleSheet("""
            QPushButton {
                background: #1E293B; color: #F8FAFC; border-radius: 5px;
                font-size: 12px; font-weight: bold; border: 1px solid #334155;
                padding: 0px 12px;
            }
            QPushButton:hover { background: #334155; border-color: #475569; }
        """)
        self.btn_theme.clicked.connect(self.toggle_theme)
        sl.addWidget(self.btn_theme)
        sl.addSpacing(10)

        from src.updater.github_updater import get_local_version
        v_local = get_local_version()
        self.lbl_version = QLabel(f"🚀 COBRO FACIL {v_local}")
        self.lbl_version.setStyleSheet("color: #10B981; font-weight: 900; font-size: 11px; letter-spacing: 1px; border: none;") 
        sl.addWidget(self.lbl_version)
        sl.addSpacing(10)
        
        sl.addStretch(1)
        
        # --- BOTÓN TICKETS EN ESPERA ---
        self.btn_espera = QPushButton("⏳ 0 Tickets en Espera")
        self.btn_espera.setFixedHeight(40)
        self.btn_espera.setCursor(Qt.PointingHandCursor)
        self.btn_espera.setFocusPolicy(Qt.NoFocus)
        self.btn_espera.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #000000; border-radius: 5px;
                font-size: 13px; font-weight: 900; border: 1px solid #CBD5E1;
                padding: 0px 15px;
            }
            QPushButton:hover { background: #F1F5F9; }
        """)
        self.btn_espera.clicked.connect(self._swap_ticket_espera)
        sl.addWidget(self.btn_espera)
        
        sl.addStretch(1)
        
        # Scroll Area para los atajos del teclado (Previene descuadre en pantallas chicas)
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        scroll_area.setFixedHeight(44)
        
        hints_layout = QHBoxLayout()
        hints_layout.setSpacing(10) # More spacing between keyboard shortcut buttons
        hints_layout.setContentsMargins(0,0,0,0)
        
        hints_layout.addStretch() # Push buttons to the right side (from right to left)
        
        self.icon_lbl = QLabel("⌨️")
        self.icon_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; border: none; background: transparent;")
        hints_layout.addWidget(self.icon_lbl)
        
        btn_style = """
            QPushButton {
                background: #1E293B; 
                color: #F8FAFC; 
                border: 1px solid #334155; 
                border-radius: 5px;
                font-size: 13px; 
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover { 
                background: #334155; 
                border-color: #475569; 
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #0F172A;
            }
        """
        
        hints = [
            ("F1", self._do_busqueda, "Buscar Producto (F1)"),
            ("F3", self.abrir_historial_dia, "Ver Historial del Día (F3)"),
            ("F12", self.finalizar_venta, "Cobrar / Pagar Venta (F12)"),
            ("F5", self.abrir_retiro_efectivo, "Retiro de Efectivo (F5)"),
            ("F6", self.abrir_ingreso_efectivo, "Ingreso de Efectivo (F6)"),
            ("F7", self._leer_bascula, "Leer Báscula (F7)"),
            ("F8", self.bloquear_terminal, "Bloquear Terminal (F8)"),
            ("F4", self.abrir_cierre_caja, "Cierre de Turno / Caja (F4)"),
            ("F11", self.llamar_supervisor, "Llamar Supervisor (F11)")
        ]
        
        self.shortcut_buttons = []
        for text, func, tooltip in hints:
            btn = QPushButton(text)
            btn.setStyleSheet(btn_style)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setFixedSize(45, 40) # 45px width by 40px height
            btn.setToolTip(tooltip)
            btn.clicked.connect(func)
            hints_layout.addWidget(btn)
            self.shortcut_buttons.append(btn)
                
        # Widget contenedor para el layout de atajos
        hints_widget = QWidget()
        hints_widget.setLayout(hints_layout)
        hints_widget.setStyleSheet("background: transparent; border: none;")
        scroll_area.setWidget(hints_widget)
        
        sl.addWidget(scroll_area, 2) # Give it a stretch factor of 2 to occupy a large harmonious portion (approx. half the screen)
        sl.addSpacing(10)
        
        # Botón Candado
        self.btn_candado = QPushButton("🔒")
        self.btn_candado.setFixedSize(40, 40) # Square size 40x40
        self.btn_candado.setToolTip("Bloquear terminal (F8)")
        self.btn_candado.setCursor(Qt.PointingHandCursor)
        self.btn_candado.setStyleSheet("""
            QPushButton {
                background: #1E3A8A; color: white; border-radius: 5px;
                font-size: 14px; font-weight: bold; border: 1px solid #3B82F6;
            }
            QPushButton:hover { background: #EF4444; border-color: #EF4444; }
        """)
        self.btn_candado.clicked.connect(self.bloquear_terminal)
        self.btn_candado.setFocusPolicy(Qt.NoFocus)
        sl.addWidget(self.btn_candado)
        
        # Botón Manual Chatbot (Adorno)
        self.btn_chatbot = QPushButton("🤖")
        self.btn_chatbot.setFixedSize(40, 40) # Square size 40x40
        self.btn_chatbot.setToolTip("Asistente Virtual")
        self.btn_chatbot.setCursor(Qt.PointingHandCursor)
        self.btn_chatbot.setStyleSheet("""
            QPushButton {
                background: #10B981; color: white; border-radius: 5px;
                font-size: 14px; font-weight: bold; border: 1px solid #059669;
            }
            QPushButton:hover { background: #059669; }
        """)
        self.btn_chatbot.clicked.connect(self.toggle_chatbot)
        self.btn_chatbot.setFocusPolicy(Qt.NoFocus)
        sl.addWidget(self.btn_chatbot)
        
        self.main_layout.addWidget(self.status_bar)
        self.txt_scan.setFocus()
        QTimer.singleShot(500, self.txt_scan.setFocus) # Asegurar foco inicial
        self.txt_scan.installEventFilter(self) # Para monitoreo PRO
        
