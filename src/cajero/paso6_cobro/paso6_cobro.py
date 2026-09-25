from src.utils.qt_compat import qt_exec
import hashlib
import os
from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QGridLayout,
    QWidget, QApplication, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QKeyEvent, QKeySequence, QShortcut
from src.base_de_datos.database import db_manager
from src.config import config
from src.hardware.cash_drawer import drawer_manager

try:
    from src.ui_components.virtual_keyboard import VirtualKeyboard
    HAS_KEYBOARD = True
except Exception as e:
    import logging
    logging.warning(f"Módulo de teclado virtual no disponible en Paso6Cobro: {e}")
    HAS_KEYBOARD = False

from src.cajero.paso6_cobro.componentes_paso6_cobro.teclado_numerico.teclado_numerico_lateral import TecladoNumericoLateral
from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago import (
    SelectorMetodoPago,
    atender_pagina_metodos,
    es_flecha,
    marcar_tarjeta,
    metodo_con_flecha,
)
from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago.tarjeta.medida import (
    BARRA,
    PIE,
    medida_hoja,
)
from src.cajero.paso6_cobro.componentes_paso6_cobro.resumen_vuelto.resumen_vuelto import ResumenVuelto
from src.cajero.paso6_cobro.componentes_paso6_cobro.logica.cobro_controller import CobroController

from src.cajero.paso6_cobro.componentes_paso6_cobro.generador_iconos.generador_iconos import ensure_icons

# Ejecutar proceso autogenerador
ensure_icons()

class Paso6Cobro(QDialog):
    """
    PASO 6: VENTANA DE COBRO ELITE 2026
    Diseño premium, sombras cinemáticas y lógica infalible.
    """
    def __init__(self, total, items_carrito, parent=None):
        super().__init__(parent)
        import uuid
        self.request_id = str(uuid.uuid4())
        self.total_original = total
        self.total_final = total
        self.items_carrito = items_carrito
        self.descuento_porcentaje = 0.0
        self.recargo_porcentaje = 0.0

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._panel_w, self._panel_h = self._medida_panel()

        self.current_metodo = "Efectivo"
        self.setup_ui()
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso6")
        except:
            pass
        self.apply_glow()

    def _medida_panel(self):
        """La ventana de cobro. El gris de alrededor es el que tapa el paso 5."""
        parent = self.parent()
        ancho = parent.width() if parent is not None else 1280
        alto = parent.height() if parent is not None else 800
        return min(1360, max(720, ancho - 24)), min(920, max(560, alto - 24))

    def _cubrir_paso5(self):
        parent = self.parent()
        if parent is None:
            return
        origen = parent.mapToGlobal(parent.rect().topLeft())
        self.setGeometry(origen.x(), origen.y(), parent.width(), parent.height())

    def showEvent(self, event):
        self._cubrir_paso5()
        super().showEvent(event)
        if hasattr(self, "btn_f11"):
            self._ajustar_botones_mp()
        if hasattr(self, "aviso_toast"):
            self.aviso_toast.ubicar()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#334155"))
        painter.end()


    def apply_glow(self):
        # Se elimina QGraphicsDropShadowEffect para rendimiento.
        pass

    def apply_theme(self):
        theme = config.get("theme", "light")
        self.main_frame.setObjectName("Paso6Main")
        self.main_frame.setProperty("theme", theme)
        self.main_frame.style().unpolish(self.main_frame)
        self.main_frame.style().polish(self.main_frame)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget(self)
        self.stack.setObjectName("Paso6Stack")
        self.stack.setFixedSize(self._panel_w, self._panel_h)
        self.stack.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout.addWidget(self.stack, 0, Qt.AlignmentFlag.AlignCenter)

        # PÁGINA 0: SELECCIÓN DE MÉTODO
        self.page_method = QFrame()
        self.page_method.setObjectName("Paso6MetodosContainer")
        self.page_method.setStyleSheet("QFrame#Paso6MetodosContainer { background: transparent; }")
        self.page_method.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        outer_lay = QVBoxLayout(self.page_method)
        outer_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("Paso6Metodos")
        hoja = medida_hoja(self._panel_w, self._panel_h)
        card.setFixedSize(hoja["hoja_w"], hoja["hoja_h"])
        card.setStyleSheet("QFrame#Paso6Metodos { background: #FFFFFF; border-radius: 24px; border: 1px solid #CBD5E1; }")
        page_method_lay = QVBoxLayout(card)
        page_method_lay.setContentsMargins(0, 0, 0, 0)
        page_method_lay.setSpacing(0)
        outer_lay.addWidget(card)

        barra = QFrame()
        barra.setObjectName("Paso6MetodoBarra")
        barra.setFixedHeight(BARRA)
        barra.setStyleSheet("QFrame#Paso6MetodoBarra { background: #0F172A; border-top-left-radius: 24px; border-top-right-radius: 24px; }")
        barra_lay = QHBoxLayout(barra)
        barra_lay.setContentsMargins(32, 0, 32, 0)
        lbl_title = QLabel("Método de pago")
        lbl_title.setObjectName("Paso6MetodoTitulo")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        barra_lay.addSpacing(16)
        barra_lay.addWidget(lbl_title, 1)
        self.luz_tpv_metodos = QLabel()
        self.luz_tpv_metodos.setFixedSize(16, 16)
        lbl_tpv_metodos = QLabel("TPV")
        lbl_tpv_metodos.setStyleSheet(
            "color: #E2E8F0; font-size: 14px; font-weight: 800; letter-spacing: 1px; "
            "background: transparent; border: none;"
        )
        barra_lay.addWidget(lbl_tpv_metodos, 0, Qt.AlignmentFlag.AlignVCenter)
        barra_lay.addSpacing(8)
        barra_lay.addWidget(self.luz_tpv_metodos, 0, Qt.AlignmentFlag.AlignVCenter)
        page_method_lay.addWidget(barra)

        self.selector_metodos = SelectorMetodoPago(
            self, hoja["ancho"], hoja["alto"], hoja["sep"]
        )
        self.selector_metodos.metodo_seleccionado.connect(self.procesar_click_metodo)
        self.btns = self.selector_metodos.get_botones()
        page_method_lay.addSpacing(hoja["aire"])
        page_method_lay.addWidget(self.selector_metodos, 0, Qt.AlignmentFlag.AlignHCenter)
        page_method_lay.addSpacing(hoja["aire"])

        estilo_pie = (
            "QPushButton { background-color: #FFFFFF; color: #0F172A; "
            "border: 1px solid #E2E8F0; border-radius: 10px; font-size: 18px; font-weight: 800; } "
            "QPushButton:hover { background-color: #F8FAFC; border-color: #CBD5E1; }"
        )

        btn_cancelar = QPushButton("Volver al carrito")
        btn_cancelar.setObjectName("Paso6Volver")
        btn_cancelar.setFixedHeight(64)
        btn_cancelar.setFixedWidth(220)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet(estilo_pie)
        btn_cancelar.clicked.connect(self.reject)


        # Botón de Otras Opciones (Fiado, Clientes)
        self.btn_otras = QPushButton("Otras opciones")
        self.btn_otras.setObjectName("Paso6Otras")
        self.btn_otras.setFixedHeight(64)
        self.btn_otras.setFixedWidth(220)
        self.btn_otras.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_otras.setStyleSheet(estilo_pie)

        # Crear Menú Desplegable
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        menu_otras = QMenu(self)
        menu_otras.setStyleSheet("""
            QMenu { background-color: #FFFFFF; border: 2px solid #E2E8F0; border-radius: 8px; font-size: 18px; font-weight: bold; color: #334155; padding: 5px; }
            QMenu::item { padding: 10px 30px; border-radius: 4px; }
            QMenu::item:selected { background-color: #F1F5F9; color: #0F172A; }
        """)

        act_fiado = QAction("Fiado", self)
        act_fiado.triggered.connect(lambda: self.procesar_click_metodo("Fiado"))
        menu_otras.addAction(act_fiado)

        act_clientes = QAction("Cuenta corriente", self)
        act_clientes.triggered.connect(lambda: self.procesar_click_metodo("Clientes"))
        menu_otras.addAction(act_clientes)

        self.btn_otras.setMenu(menu_otras)

        pie = QFrame()
        pie.setObjectName("Paso6MetodoPie")
        pie.setFixedHeight(PIE)
        pie.setStyleSheet("QFrame#Paso6MetodoPie { background: #F8FAFC; border-bottom-left-radius: 24px; border-bottom-right-radius: 24px; border-top: 1px solid #E2E8F0; }")
        lay_btn = QHBoxLayout(pie)
        lay_btn.setContentsMargins(32, 0, 32, 0)
        lay_btn.addStretch()
        lay_btn.addWidget(btn_cancelar)
        lay_btn.addSpacing(16)
        lay_btn.addWidget(self.btn_otras)
        lay_btn.addStretch()
        page_method_lay.addWidget(pie)
        self.stack.addWidget(self.page_method)

        # PÁGINA 1: COBRO
        self.main_frame = QFrame()
        self.main_frame.setObjectName("Paso6Main")
        self.stack.addWidget(self.main_frame)

        main_lay = QHBoxLayout(self.main_frame)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # --- SECCIÓN IZQUIERDA: PAGO (75%) ---
        left_panel = QWidget()
        self.left_panel = left_panel
        left_panel.setObjectName("LeftPanelCobro")
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        # HEADER AZUL "COBRAR" (Estilo transparente premium)
        barra_cobro = QFrame()
        barra_cobro.setFixedHeight(64)
        barra_cobro.setStyleSheet("background: transparent; border: none;")
        lay_cobro = QHBoxLayout(barra_cobro)
        lay_cobro.setContentsMargins(8, 0, 28, 0)
        self.header = QLabel("COBRO")
        self.header.setObjectName("CobroHeader")
        lay_cobro.addWidget(self.header)
        lay_cobro.addStretch()
        self.lbl_tpv = QLabel("TPV")
        self.lbl_tpv.setStyleSheet(
            "color: #64748B; font-size: 16px; font-weight: 800; letter-spacing: 1.2px; "
            "background: transparent; border: none;"
        )
        self.luz_tpv = QLabel()
        self.luz_tpv.setFixedSize(16, 16)
        lay_cobro.addWidget(self.lbl_tpv)
        lay_cobro.addSpacing(8)
        lay_cobro.addWidget(self.luz_tpv, 0, Qt.AlignmentFlag.AlignVCenter)
        left_lay.addWidget(barra_cobro)

        # CONTENIDO IZQUIERDO
        content_lay = QVBoxLayout()
        content_lay.setContentsMargins(28, 8, 28, 8)
        content_lay.setSpacing(10)

        self.lbl_precio_real = QLabel("")
        self.lbl_precio_real.setObjectName("PrecioLista")
        self.lbl_precio_real.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fuente_lista = QFont("Segoe UI", 16)
        fuente_lista.setBold(True)
        fuente_lista.setStrikeOut(True)
        self.lbl_precio_real.setFont(fuente_lista)
        self.lbl_precio_real.setStyleSheet(
            "color: #EF4444; font-size: 22px; font-weight: 800; background: transparent; border: none;"
        )
        self.lbl_precio_real.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_precio_real.setMinimumHeight(28)
        self.lbl_precio_real.hide()
        self.lbl_total = QLabel(self._monto(self.total_original))
        self.lbl_total.setObjectName("CobroTotal")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caja_total = QVBoxLayout()
        caja_total.setSpacing(0)
        caja_total.addWidget(self.lbl_precio_real)
        caja_total.addWidget(self.lbl_total)
        content_lay.addLayout(caja_total)

        from src.cajero.paso6_cobro.qr_en_cobro.panel import PanelQrCobro
        self.panel_qr = PanelQrCobro(self)
        self.panel_qr.pago_listo.connect(self._cerrar_venta_por_qr)
        self.panel_qr.cambio_modo.connect(self._vista_monto_qr)
        self.panel_qr.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_lay.addWidget(self.panel_qr, 1)
        from src.cajero.paso6_cobro.tarjeta_en_cobro.panel import PanelTarjetaCobro
        self.panel_tarjeta = PanelTarjetaCobro(self)
        self.panel_tarjeta.pago_listo.connect(self._cerrar_venta_por_tarjeta)
        self.panel_tarjeta.cambio.connect(self._aviso_tarjeta)
        content_lay.addWidget(self.panel_tarjeta, 0)
        from src.cajero.paso6_cobro.mixto_en_cobro.panel import PanelMixtoCobro
        self.panel_mixto = PanelMixtoCobro(self)
        self.panel_mixto.cambio.connect(self._tomar_mixto)
        self.panel_mixto.aviso.connect(self._avisar)
        for caja in self.panel_mixto.campos():
            caja.installEventFilter(self)
        content_lay.addWidget(self.panel_mixto)
        from src.cajero.paso6_cobro.monto_en_cobro.panel import PanelMontoCobro
        self.panel_monto = PanelMontoCobro(self)
        content_lay.addWidget(self.panel_monto, 0)
        self._qr_monto_timer = QTimer(self)
        self._qr_monto_timer.setSingleShot(True)
        self._qr_monto_timer.timeout.connect(self._refrescar_qr_si_vivo)
        self._tarjeta_monto_timer = QTimer(self)
        self._tarjeta_monto_timer.setSingleShot(True)
        self._tarjeta_monto_timer.timeout.connect(self._refrescar_tarjeta)
        from src.cajero.paso6_cobro.aviso_en_cobro.toast import AvisoCobro, EsperaPoint
        self.aviso_toast = AvisoCobro(left_panel)
        self.espera_point = EsperaPoint(left_panel)
        from src.clientes_fiado.interfaz.cobro.hoja import HojaCuentaCobro
        self.hoja_cuenta = HojaCuentaCobro(left_panel)
        self.hoja_cuenta.listo.connect(self._cuenta_lista)
        self.hoja_cuenta.cancelado.connect(self._cuenta_cancelada)
        self._point_en_curso = False
        self._emergencia_pendiente = False
        self._atajo_f9 = QShortcut(QKeySequence(Qt.Key.Key_F9), self)
        self._atajo_f9.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._atajo_f9.activated.connect(self._emergencia)

        self.aviso_monto = QLabel("INGRESÁ EL MONTO RECIBIDO")
        self.aviso_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aviso_monto.setFixedHeight(84)
        self.aviso_monto.setStyleSheet(
            "background: #FEF3C7; color: #92400E; font-size: 32px; font-weight: 900; "
            "letter-spacing: 1px; border: 3px solid #F59E0B; border-radius: 14px; padding: 12px;"
        )
        self.aviso_monto.hide()
        self.panel_monto.zona_pago.contenido.addWidget(self.aviso_monto)

        # La lista se carga al abrir Fiado o Clientes, no al pintar el cobro.
        self.lista_clientes = []
        self._clientes_cargados = False


        # Inputs de Pago
        grid_inputs = QGridLayout()
        grid_inputs.setSpacing(15)
        grid_inputs.setColumnStretch(0, 1)
        grid_inputs.setColumnStretch(1, 2)

        self.lbl_input1 = QLabel("Monto Recibido:")
        self.lbl_input1.setObjectName("InputLabel")
        grid_inputs.addWidget(self.lbl_input1, 0, 0)

        self.txt_pago = QLineEdit("")
        self.txt_pago.setObjectName("InputPago")
        self.txt_pago.setFixedHeight(88)
        self.txt_pago.setStyleSheet("font-size: 40px; font-weight: 900; border-radius: 12px; border: 2px solid #CBD5E1; color: #0F172A; background: #FFFFFF;")
        self.txt_pago.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_pago.setPlaceholderText("$0.00")
        self.txt_pago.textChanged.connect(self.calcular_vuelto)
        self.txt_pago.returnPressed.connect(self.intentar_finalizar)
        self.txt_pago.installEventFilter(self)
        grid_inputs.addWidget(self.txt_pago, 0, 1)

        self.lbl_input2 = QLabel("Otro Medio:")
        self.lbl_input2.setObjectName("InputLabel")
        grid_inputs.addWidget(self.lbl_input2, 1, 0)

        self.txt_otro = QLineEdit("0.00")
        self.txt_otro.setObjectName("InputPago")
        self.txt_otro.setFixedHeight(72)
        self.txt_otro.setStyleSheet("font-size: 32px; font-weight: 900; border-radius: 12px; border: 2px solid #CBD5E1; color: #0F172A; background: #FFFFFF;")
        self.txt_otro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_otro.textChanged.connect(self.calcular_vuelto)
        self.txt_otro.returnPressed.connect(self.intentar_finalizar)
        self.txt_otro.installEventFilter(self)
        grid_inputs.addWidget(self.txt_otro, 1, 1)
        self.lbl_input2.hide(); self.txt_otro.hide()

        from PyQt6.QtWidgets import QComboBox
        self.lbl_cliente = QLabel("CLIENTE:")
        self.lbl_cliente.setObjectName("InputLabel")
        self.cmb_cliente = QComboBox()
        self.cmb_cliente.setObjectName("CmbClienteCobro")

        self.lbl_cliente.hide()
        self.cmb_cliente.hide()

        grid_inputs.addWidget(self.lbl_cliente, 2, 0)
        grid_inputs.addWidget(self.cmb_cliente, 2, 1)
        self.panel_monto.zona_pago.contenido.addLayout(grid_inputs)
        from src.cajero.paso6_cobro.transferencia_en_cobro.panel import PanelAliasCobro
        self.panel_alias = PanelAliasCobro(self)
        self.panel_monto.zona_pago.contenido.addWidget(self.panel_alias, 1)

        # NUEVA LÍNEA HORIZONTAL DE MODIFICADORES COMPACTA
        grid_desc_rec = QGridLayout()
        grid_desc_rec.setSpacing(8)

        # REDONDEO
        lay_lbl_desc = QHBoxLayout()
        lay_lbl_desc.setContentsMargins(0,0,0,0)
        self.lbl_desc = QLabel("Redondeo:")
        self.lbl_desc.setObjectName("InputLabel")
        self.btn_tipo_desc = QPushButton("$")
        self.btn_tipo_desc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tipo_desc.setFixedSize(32, 32)
        self.btn_tipo_desc.setStyleSheet("QPushButton { background: #E2E8F0; color: #1E293B; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #CBD5E1; }")
        self.btn_tipo_desc.clicked.connect(self._toggle_tipo_desc)
        lay_lbl_desc.addWidget(self.lbl_desc)
        lay_lbl_desc.addWidget(self.btn_tipo_desc)
        lay_lbl_desc.addStretch()
        grid_desc_rec.addLayout(lay_lbl_desc, 0, 0)
        
        self.txt_desc = QLineEdit("")
        self.txt_desc.setObjectName("InputDesc")
        self.txt_desc.setFixedHeight(48)
        self.txt_desc.setStyleSheet("font-size: 20px; font-weight: bold; border-radius: 8px; border: 1px solid #CBD5E1;")
        self.txt_desc.setPlaceholderText("0.00")
        self.txt_desc.textChanged.connect(self.on_descuento_changed)
        self.txt_desc.installEventFilter(self)
        grid_desc_rec.addWidget(self.txt_desc, 0, 1)

        # RECARGO
        lay_lbl_rec = QHBoxLayout()
        lay_lbl_rec.setContentsMargins(0,0,0,0)
        self.lbl_rec = QLabel("Recargo:")
        self.lbl_rec.setObjectName("InputLabel")
        self.btn_tipo_rec = QPushButton("$")
        self.btn_tipo_rec.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tipo_rec.setFixedSize(32, 32)
        self.btn_tipo_rec.setStyleSheet("QPushButton { background: #E2E8F0; color: #1E293B; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #CBD5E1; }")
        self.btn_tipo_rec.clicked.connect(self._toggle_tipo_rec)
        lay_lbl_rec.addWidget(self.lbl_rec)
        lay_lbl_rec.addWidget(self.btn_tipo_rec)
        lay_lbl_rec.addStretch()
        grid_desc_rec.addLayout(lay_lbl_rec, 0, 2)

        self.txt_rec = QLineEdit("")
        self.txt_rec.setObjectName("InputRec")
        self.txt_rec.setFixedHeight(48)
        self.txt_rec.setStyleSheet("font-size: 20px; font-weight: bold; border-radius: 8px; border: 1px solid #CBD5E1;")
        self.txt_rec.setPlaceholderText("0.00")
        self.txt_rec.textChanged.connect(self.on_recargo_changed)
        self.txt_rec.installEventFilter(self)
        grid_desc_rec.addWidget(self.txt_rec, 0, 3)

        # NUEVO: Neto a cobrar destacado abajo
        self.lbl_neto = QLabel(f"NETO: $ {self.total_final:,.2f}")
        self.lbl_neto.setObjectName("NetoLabel")
        self.lbl_neto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_neto.setStyleSheet(
            "color: #1E3A8A; font-size: 28px; font-weight: 800; background: transparent; border: none;"
        )
        self.lbl_neto.hide()
        self.panel_monto.zona_estado.contenido.addWidget(self.lbl_neto)

        # Vuelto (Extraído modularmente)
        self.resumen_vuelto = ResumenVuelto(self)
        self.resumen_vuelto.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.panel_monto.zona_estado.contenido.addWidget(self.resumen_vuelto)

        # Barra de Estado Mercado Pago con animación
        self.lbl_mp_status = QLabel("")
        self.lbl_mp_status.setObjectName("LblMpStatus")
        self.lbl_mp_status.setProperty("estado", "info")
        self.lbl_mp_status.setStyleSheet("background: #E0F2FE; color: #0284C7; font-size: 20px; font-weight: 900; border-radius: 12px; padding: 10px; margin-top: 10px;")
        self.lbl_mp_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mp_status.setWordWrap(True)
        self.lbl_mp_status.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
        self.lbl_mp_status.style().polish(self.lbl_mp_status)
        self.lbl_mp_status.hide()
        self.panel_monto.zona_estado.contenido.addWidget(self.lbl_mp_status)
        self.btn_aviso_mp = QPushButton("Cajero silencioso")
        self.btn_aviso_mp.setCheckable(True)
        self.btn_aviso_mp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_aviso_mp.setFixedHeight(54)
        self.btn_aviso_mp.setStyleSheet("QPushButton { background: transparent; color: #64748B; font-size: 15px; font-weight: 700; border: none; } QPushButton:hover { color: #1E293B; } QPushButton:checked { color: #2563EB; font-weight: 800; }")
        self.btn_aviso_mp.clicked.connect(self._alternar_aviso_mp)
        self.btn_aviso_mp.hide()
        self.panel_monto.zona_estado.contenido.addWidget(self.btn_aviso_mp)

        self.timer_mp = QTimer(self)
        self.timer_mp.timeout.connect(self.verificar_pago_mp_automatico)

        # Timer para el spinner y zoom
        self.mp_spinner_idx = 0
        self.mp_font_size = 20
        self.mp_font_dir = 1
        self.mp_spinner_chars = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]
        self.timer_spinner = QTimer(self)
        self.timer_spinner.timeout.connect(self._actualizar_spinner_mp)

        self.content_lay = content_lay
        self.hueco_pie = QWidget()
        self.hueco_pie.setMinimumHeight(0)
        content_lay.addWidget(self.hueco_pie, 1)
        self._idx_qr = content_lay.indexOf(self.panel_qr)
        self._idx_tarjeta = content_lay.indexOf(self.panel_tarjeta)
        self._idx_monto = content_lay.indexOf(self.panel_monto)
        self._idx_hueco = content_lay.indexOf(self.hueco_pie)
        content_lay.addLayout(grid_desc_rec)
        content_lay.addSpacing(8)

        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #E2E8F0;")
        line.setFixedHeight(2)
        content_lay.addWidget(line)
        content_lay.addSpacing(5)

        # Indicador de método seleccionado y botón volver (Movido al pie)
        lay_metodo_activo = QHBoxLayout()
        self.lbl_metodo_activo = QLabel("Método: Ninguno")
        self.lbl_metodo_activo.setStyleSheet("font-size: 22px; font-weight: bold; color: #3B82F6; background: transparent;")

        btn_cambiar_metodo = QPushButton("← Cambiar (Esc)")
        btn_cambiar_metodo.setStyleSheet("background: #E2E8F0; color: #1E293B; font-weight: bold; border-radius: 8px; padding: 0 15px;")
        btn_cambiar_metodo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cambiar_metodo.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        lay_metodo_activo.addWidget(self.lbl_metodo_activo)
        lay_metodo_activo.addStretch()
        lay_metodo_activo.addWidget(btn_cambiar_metodo)

        content_lay.addLayout(lay_metodo_activo)
        left_lay.addLayout(content_lay)
        main_lay.addWidget(left_panel, 11)

        # --- SECCIÓN DERECHA: ACCIONES (~35%) ---
        theme = config.get("theme", "light")
        right_panel = QFrame()
        right_panel.setObjectName("RightPanel")
        self.right_panel = right_panel
        right_panel.setMinimumWidth(400)
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(12, 24, 12, 24)
        right_lay.setSpacing(6)

        def create_action_btn(fn_key, subtitle, callback, style="default"):
            btn = QPushButton(f"{fn_key}\n{subtitle}")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.setProperty("action_type", style)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            return btn

        def columna_fija():
            caja = QFrame()
            caja.setObjectName("ColumnaAccion")
            caja.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            lay = QVBoxLayout(caja)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(5)
            return caja, lay

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(5)
        fila_acciones.setContentsMargins(0, 0, 0, 0)
        col_imprime, lay_imprime = columna_fija()
        col_registra, lay_registra = columna_fija()
        col_ajuste, lay_ajuste = columna_fija()
        for col in (col_imprime, col_registra, col_ajuste):
            fila_acciones.addWidget(col, 1)

        lay_imprime.addWidget(create_action_btn("F1", "imprime", lambda: self._elegir_cierre("imprime"), style="primary"), 1)
        self.btn_f2 = create_action_btn("F2", "sin ticket", lambda: self._elegir_cierre("cierra"), style="default")
        self.pila_f2 = QStackedWidget()
        self.pila_f2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_f2.setMinimumHeight(78)
        self.btn_ultimo_mixto = create_action_btn("F12", "último monto", self.corroborar_ultimo_monto, style="default")
        self.pila_f2.addWidget(self.btn_f2)
        self.pila_f2.addWidget(self.btn_ultimo_mixto)
        lay_registra.addWidget(self.pila_f2, 1)
        self.btn_descuento = create_action_btn("F3", "redondeo", self.abrir_descuento, style="default")
        lay_ajuste.addWidget(self.btn_descuento, 1)

        self.btn_recargo = create_action_btn("F4", "recargo", self.abrir_recargo, style="default")
        lay_imprime.addWidget(self.btn_recargo, 1)
        self.pila_point = QStackedWidget()
        self.pila_point.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_point.setMinimumHeight(78)
        self.btn_f11 = create_action_btn("F11", "Point MP", lambda: self.procesar_pago_mercadopago_point(), style="default")
        self.pila_point.addWidget(self.btn_f11)
        self.pila_point.addWidget(QWidget())
        lay_registra.addWidget(self.pila_point, 1)
        self.pila_extra = QStackedWidget()
        self.pila_extra.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pila_extra.setMinimumHeight(78)
        self.btn_f12 = create_action_btn("F12", "Verif QR", lambda: self.verificar_transferencia_mp(), style="default")
        self.btn_ultimo = create_action_btn("F12", "último monto", self.corroborar_ultimo_monto, style="default")
        self.pila_extra.addWidget(self.btn_f12)
        self.pila_extra.addWidget(self.btn_ultimo)
        self.pila_extra.addWidget(QWidget())
        lay_ajuste.addWidget(self.pila_extra, 1)

        right_lay.addLayout(fila_acciones, 2)

        # Teclado numérico extraído modularmente
        self.teclado_lateral = TecladoNumericoLateral(self)
        self.teclado_lateral.key_clicked.connect(self.on_teclado_key_clicked)
        right_lay.addWidget(self.teclado_lateral, 0)
        right_lay.addStretch(1)

        main_lay.addWidget(right_panel, 6)
        self.apply_theme()

        # Aplicar método inicial pero mantener en página 0
        self.stack.setCurrentIndex(0)
        self.set_metodo("Efectivo")
        self.recargar_total_final()
        self._pintar_luz_tpv()

        # Foco inicial en la ventana para capturar teclado en la selección de método
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def procesar_click_metodo(self, key):
        if key not in ("Fiado", "Clientes"):
            # Efectivo, tarjeta, QR y mixto abren la hoja del monto.
            self.stack.setCurrentIndex(1)
            if key != "Mixto":
                self.txt_pago.setFocus()

        if key == "Clientes":
            self.stack.setCurrentIndex(1)
            self._activar_cliente_express()
            return
        elif key == "Fiado":
            self.stack.setCurrentIndex(1)
            self._activar_fiado_express()
            return
        else:
            self.set_metodo(key)

    def apply_theme(self):
        theme = config.get("theme", "light")
        self.main_frame.setProperty("theme", theme)
        self.main_frame.style().unpolish(self.main_frame)
        self.main_frame.style().polish(self.main_frame)

        self.page_method.setProperty("theme", theme)
        self.page_method.style().unpolish(self.page_method)
        self.page_method.style().polish(self.page_method)

        # La actualización de color "Vuelto" estático ahora se maneja en estilos.qss mediante QFrame#Paso6Main[theme="..."] QLabel#LblVueltoTit
        self.resumen_vuelto.lbl_vuelto_tit.setObjectName("LblVueltoTit")

    def set_metodo(self, key):
        self._mixto_pasos = None
        self._mixto_esperando_qr = False
        self._mixto_espera_transferencia = None
        self._mixto_confirmado = False
        self._ticket_al_pagar = None
        metodo_previo = self.current_metodo
        if getattr(self, "_point_en_curso", False) and key != metodo_previo:
            self.espera_point.soltar()
        marcar_tarjeta(self, key)
        self._ajustar_botones_mp()
        if key not in ("QR", "Mixto"):
            self.lbl_input1.show()
            self.txt_pago.show()
        self.lbl_neto.hide()

        if key == "Mixto":
            if hasattr(self, "panel_qr"):
                self.panel_qr.ocultar()
            self.lbl_input1.hide()
            self.txt_pago.hide()
            self.lbl_input2.hide()
            self.txt_otro.hide()
            self.lbl_cliente.hide()
            self.cmb_cliente.hide()
            self.lbl_mp_status.hide()
            self.timer_mp.stop()
            self.timer_spinner.stop()
            self.panel_mixto.mostrar(self.total_final)
            self.valores_mixtos = self.panel_mixto.valores()
        elif key == "Tarjeta":
            self.lbl_input1.hide()
            self.txt_pago.hide()
            self.lbl_input2.hide()
            self.txt_otro.hide()
            self.lbl_cliente.hide()
            self.cmb_cliente.hide()
            self.txt_pago.setText(self._monto(self.total_final))
            self.lbl_mp_status.hide()
            self.timer_mp.stop()
            self.timer_spinner.stop()
        elif key in ["Transferencia", "QR"]:
            self.lbl_input1.setText("PAGA CON ($):")
            self.lbl_input2.hide(); self.txt_otro.hide()
            self.lbl_cliente.hide(); self.cmb_cliente.hide()
            # Autocompletar monto para medios electrónicos (evita errores y agiliza)
            self.txt_pago.setText(self._monto(self.total_final))

            if key == "Transferencia":
                self.lbl_input1.hide()
                self.txt_pago.hide()
                self.panel_alias.mostrar()
                self.lbl_mp_status.setText(f" {self.mp_spinner_chars[0]} ESCUCHANDO MERCADO PAGO EN TIEMPO REAL... (${self.total_final:.2f})")
                theme = config.get("theme", "light")
                if theme == "dark":
                    self.lbl_mp_status.setProperty("estado", "waiting")
                    self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
                    self.lbl_mp_status.style().polish(self.lbl_mp_status)
                else:
                    self.lbl_mp_status.setProperty("estado", "waiting")
                    self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
                    self.lbl_mp_status.style().polish(self.lbl_mp_status)
                self.lbl_mp_status.show()
                self._pintar_aviso_mp()
                self.btn_aviso_mp.show()
                from src.services.mp_escucha import EscuchaMP
                EscuchaMP.asegurar()
                self.timer_mp.start(1000)
                self.timer_spinner.start(60) # Gira y palpita rápido
            else:
                if hasattr(self, "panel_alias"):
                    self.panel_alias.ocultar()
                self.lbl_mp_status.hide()
                if hasattr(self, "btn_aviso_mp"):
                    self.btn_aviso_mp.hide()
                self.timer_mp.stop()
                self.timer_spinner.stop()
        elif key == "Clientes":
            if metodo_previo != "Clientes":
                self._revertir_tras_fiado = metodo_previo or "Efectivo"
            self.lbl_input1.hide()
            self.txt_pago.hide()
            self.lbl_input2.hide()
            self.txt_otro.hide()
            self.lbl_cliente.hide()
            self.cmb_cliente.hide()
            self.txt_pago.setText(self._monto(self.total_final))
            self.txt_pago.setReadOnly(True)
            self.lbl_mp_status.hide()
            self.timer_mp.stop()
        elif key == "Fiado":
            if metodo_previo != "Fiado":
                self._revertir_tras_fiado = metodo_previo or "Efectivo"
            self.lbl_input1.hide()
            self.txt_pago.hide()
            self.lbl_input2.hide()
            self.txt_otro.hide()
            self.lbl_cliente.hide()
            self.cmb_cliente.hide()
            self.txt_pago.setText(self._monto(self.total_final))
            self.txt_pago.setReadOnly(True)
            self.lbl_mp_status.hide()
            self.timer_mp.stop()
        else:
            self.lbl_input1.setText("PAGA CON ($):")
            self.lbl_input2.hide(); self.txt_otro.hide()
            self.lbl_cliente.hide(); self.cmb_cliente.hide()
            self.txt_pago.setReadOnly(False)
            # Limpiar para forzar ingreso manual y cálculo de vuelto real
            self.txt_pago.clear()
            self.lbl_mp_status.hide()
            self.timer_mp.stop()
        if key != "Mixto" and hasattr(self, "panel_mixto"):
            self.panel_mixto.ocultar()
        if key == "QR" and hasattr(self, "panel_qr"):
            self._pintar_luz_tpv()
            if not self._tpv_qr_listo():
                self._vista_monto_qr("manual")
                self.panel_qr.ofrecer_foto()
            else:
                self._vista_monto_qr("buscando")
                self.panel_qr.mostrar(self.total_final, forzar=True)
        elif hasattr(self, "panel_qr"):
            self.panel_qr.ocultar()
        if key == "Tarjeta":
            self._pintar_luz_tpv()
            if hasattr(self, "panel_tarjeta"):
                self.panel_tarjeta.ocultar()
            if self._tpv_point_listo() and not getattr(self, "_point_en_curso", False):
                QTimer.singleShot(0, self._cobrar_tarjeta_point)
        elif hasattr(self, "panel_tarjeta"):
            self.panel_tarjeta.ocultar()
        if key not in ("Fiado", "Clientes") and hasattr(self, "hoja_cuenta"):
            self.hoja_cuenta.ocultar()
        if key != "Transferencia" and hasattr(self, "btn_aviso_mp"):
            self.btn_aviso_mp.hide()
        if key != "Transferencia" and hasattr(self, "panel_alias"):
            self.panel_alias.ocultar()
        self.calcular_vuelto()
        self._ajustar_botones_mp()
        self._ajustar_contenedor_monto()
        if key == "Mixto":
            self.panel_mixto.campo_foco().setFocus()
            return
        if key == "Tarjeta":
            self.setFocus()
            return
        if key == "Transferencia":
            self.setFocus()
            return
        if key in ("Fiado", "Clientes"):
            self.setFocus()
            return
        if getattr(self, "stack", None) and self.stack.currentIndex() == 0:
            self.setFocus()
            return
        self.txt_pago.setFocus()
        self.txt_pago.selectAll()

    def _asegurar_lista_clientes(self):
        """Una sola lectura de clientes, la primera vez que hace falta Fiado o Clientes."""
        if getattr(self, "_clientes_cargados", False):
            return
        self._clientes_cargados = True
        try:
            from src.clientes_fiado.cerebro.cerebro import cerebro

            filas = cerebro.listar()
        except Exception:
            filas = []
        self.lista_clientes = filas
        self.cmb_cliente.blockSignals(True)
        self.cmb_cliente.clear()
        for c in filas:
            try:
                disp = float(c["limite_credito"]) - float(c["deuda_actual"])
                self.cmb_cliente.addItem(f"{c['nombre']} (Disp: ${disp:,.2f})", c["id"])
            except Exception:
                continue
        self.cmb_cliente.blockSignals(False)

    def _activar_cliente_express(self):
        """Clic en Clientes: la misma hoja del cobro, no una ventana oscura."""
        if self.current_metodo != "Clientes":
            self._revertir_tras_fiado = self.current_metodo or "Efectivo"
        self.stack.setCurrentIndex(1)
        self.set_metodo("Clientes")
        self._mostrar_hoja_cuenta("Clientes")

    def _abrir_cliente_express(self, revertir_a="Efectivo"):
        """Cliente en la hoja del cobro. El nombre se pide dos veces."""
        if self.current_metodo != "Clientes":
            self._revertir_tras_fiado = revertir_a if revertir_a != "Clientes" else "Efectivo"
            self._activar_cliente_express()
            return
        self._mostrar_hoja_cuenta("Clientes")

    def _activar_fiado_express(self):
        """Clic en Fiado: la misma hoja del cobro, no una ventana oscura."""
        if self.current_metodo != "Fiado":
            self._revertir_tras_fiado = self.current_metodo or "Efectivo"
        self.stack.setCurrentIndex(1)
        self.set_metodo("Fiado")
        self._mostrar_hoja_cuenta("Fiado")

    def _abrir_fiado_express(self, revertir_a="Efectivo"):
        """Abre el fiado en la hoja del cobro."""
        return self._abrir_fiado_express_original(revertir_a)

    def _abrir_fiado_express_original(self, revertir_a="Efectivo"):
        """Fiado en la hoja del cobro. El DNI se pide dos veces."""
        if self.current_metodo != "Fiado":
            self._revertir_tras_fiado = revertir_a if revertir_a != "Fiado" else "Efectivo"
            self._activar_fiado_express()
            return
        self._mostrar_hoja_cuenta("Fiado")

    def _reabrir_cuenta(self):
        if self.current_metodo == "Clientes":
            self._abrir_cliente_express(getattr(self, "_revertir_tras_fiado", "Efectivo"))
        else:
            self._abrir_fiado_express(getattr(self, "_revertir_tras_fiado", "Efectivo"))

    def _mostrar_hoja_cuenta(self, modo):
        self._asegurar_lista_clientes()
        self._fiado_flujo_activo = True
        self._fiado_cliente_id = None
        self.stack.setCurrentIndex(1)
        self.hoja_cuenta.abrir(modo, self.total_final)

    def _cuenta_lista(self, cliente_id):
        self._fiado_cliente_id = int(cliente_id)
        idx = self.cmb_cliente.findData(self._fiado_cliente_id)
        if idx >= 0:
            self.cmb_cliente.setCurrentIndex(idx)
        self.txt_pago.setText(self._monto(self.total_final))
        self._fiado_flujo_activo = False
        QTimer.singleShot(80, lambda: self.finalizar(imprimir=False))

    def _cuenta_cancelada(self):
        if getattr(self, "_cuenta_cerrando", False):
            return
        self._cuenta_cerrando = True
        try:
            self._fiado_flujo_activo = False
            self._fiado_cliente_id = None
            rev = getattr(self, "_revertir_tras_fiado", "Efectivo") or "Efectivo"
            if rev in ("Fiado", "Clientes"):
                rev = "Efectivo"
            self.hoja_cuenta.ocultar()
            self.stack.setCurrentIndex(0)
            self.set_metodo(rev)
            self.setFocus()
        finally:
            self._cuenta_cerrando = False

    def _monto(self, valor):
        return f"${float(valor):,.2f}"

    def calcular_vuelto(self):
        if self.current_metodo != "Efectivo":
            self.resumen_vuelto.hide()
            self.aviso_monto.hide()
            return
        self.resumen_vuelto.show()
        self.aviso_monto.hide()
        self.txt_pago.setStyleSheet(
            "font-size: 40px; font-weight: 900; border-radius: 12px; "
            "border: 2px solid #CBD5E1; color: #0F172A; background: #FFFFFF;"
        )
        try:
            p1_t = self.txt_pago.text().replace('$', '').replace(',', '').strip()
            p2_t = self.txt_otro.text().replace('$', '').replace(',', '').strip()
            p1 = float(p1_t) if p1_t else 0

            if self.current_metodo == "Mixto" and hasattr(self, 'valores_mixtos'):
                p1 = self.valores_mixtos.get("efectivo", 0)
                p2 = (
                    self.valores_mixtos.get("tarjeta", 0)
                    + self.valores_mixtos.get("mercadopago", 0)
                    + self.valores_mixtos.get("qr", 0)
                )
            else:
                p2 = float(p2_t) if p2_t and self.current_metodo == "Mixto" else 0
            total_pagado = p1 + p2
            vuelto = total_pagado - self.total_final

            # Usamos el componente modular para actualizar el vuelto
            self.resumen_vuelto.actualizar_vuelto(vuelto)
        except: pass

    def _actualizar_spinner_mp(self):
        try:
            self.mp_spinner_idx = (self.mp_spinner_idx + 1) % len(self.mp_spinner_chars)
            char = self.mp_spinner_chars[self.mp_spinner_idx]
            monto_escucha = getattr(self, "_mixto_espera_transferencia", None)
            if monto_escucha is None:
                monto_escucha = self.total_final

            self.lbl_mp_status.setStyleSheet("background: #E0F2FE; color: #0284C7; font-size: 20px; font-weight: 900; border-radius: 12px; padding: 10px; margin-top: 10px;")
            self.lbl_mp_status.setText(f" {char} ESCUCHANDO MERCADO PAGO EN TIEMPO REAL... (${monto_escucha:.2f})")
            if getattr(self, "_mixto_espera_transferencia", None) is not None and hasattr(self, "panel_mixto"):
                from src.utils.dinero import redondear_dinero

                parte = redondear_dinero(self.panel_mixto.valores().get("mercadopago") or 0)
                if abs(parte - float(monto_escucha)) > 0.009:
                    self._tomar_mixto(self.panel_mixto.valores())
                    return
                self.panel_mixto.estado.setText(
                    f"{char} Escuchando transferencia ${monto_escucha:,.2f}"
                )
                self.panel_mixto.estado.setStyleSheet(
                    "color: #0EA5E9; font-size: 20px; font-weight: 800; background: transparent; border: none;"
                )
        except Exception as e:
            pass

    def verificar_pago_mp_automatico(self):
        try:
            import time
            from src.admin.mercadopago.mercadopago_main import Admin10MP
            if hasattr(Admin10MP, 'ultimo_pago_detectado') and Admin10MP.ultimo_pago_detectado is not None:
                pago = Admin10MP.ultimo_pago_detectado
                ahora = time.time()

                # Validar que el pago haya ocurrido hace menos de 90 segundos
                if ahora - pago['timestamp'] <= 90:
                    from src.cajero.paso6_cobro.vinculo_mp.libro import asociado
                    if asociado(pago.get("id")):
                        Admin10MP.ultimo_pago_detectado = None
                        return
                    monto_pago = pago['monto']
                    esperado = getattr(self, "_mixto_espera_transferencia", None)
                    if esperado is None:
                        esperado = self.total_final
                    if abs(monto_pago - esperado) > 0.05:
                        if getattr(self, "_mp_oferta_id", None) != str(pago.get("id")):
                            self._mp_oferta_id = str(pago.get("id"))
                            self._ofrecer_vinculo(pago.get("id"), monto_pago, pago.get("nombre"))
                        return
                    Admin10MP.ultimo_pago_detectado = None
                    self._mp_pago_usado = {"id": pago.get("id"), "monto": monto_pago}

                    self.timer_mp.stop()
                    self.timer_spinner.stop()

                    self.lbl_mp_status.setStyleSheet("background: #DCFCE7; color: #166534; font-size: 20px; font-weight: 900; border-radius: 12px; padding: 10px; margin-top: 10px;")

                    self.lbl_mp_status.setText(f"✅ ¡PAGO DE {pago['nombre'].upper()} DETECTADO Y APROBADO!")
                    theme = config.get("theme", "light")
                    if theme == "dark":
                        self.lbl_mp_status.setProperty("estado", "success")
                        self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
                        self.lbl_mp_status.style().polish(self.lbl_mp_status)
                    else:
                        self.lbl_mp_status.setProperty("estado", "success")
                        self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
                        self.lbl_mp_status.style().polish(self.lbl_mp_status)

                    if getattr(self, "_mixto_espera_transferencia", None) is not None:
                        self._mixto_espera_transferencia = None
                        self.lbl_mp_status.hide()
                        self._mixto_i += 1
                        QTimer.singleShot(200, self._seguir_mixto)
                    else:
                        QTimer.singleShot(1500, self._cerrar_como_eligio)
        except Exception as e:
            print(f"Error verificando auto-pago MP: {e}")

    def _validar_pago(self):
        """ Centraliza la validación para evitar redundancias y errores de arqueo. """
        p1_t = self.txt_pago.text().replace('$', '').replace(',', '').strip()
        p2_t = self.txt_otro.text().replace('$', '').replace(',', '').strip()

        if not p1_t:
            if self.current_metodo == "Mixto":
                p1_t = "0"
            elif self.current_metodo in ("Tarjeta", "Transferencia", "QR"):
                self.txt_pago.setText(self._monto(self.total_final))
                p1_t = f"{self.total_final:.2f}"
            else:
                self._avisar("Debe ingresar con cuánto pagó.")
                self.txt_pago.setStyleSheet(
                    "font-size: 40px; font-weight: 900; border-radius: 12px; "
                    "border: 3px solid #F59E0B; color: #0F172A; background: #FFFBEB;"
                )
                self.txt_pago.setFocus()
                return None
        else:
            self.aviso_monto.hide()

        if self.current_metodo in ("Fiado", "Clientes"):
            from src.clientes_fiado.cerebro.cerebro import cerebro

            cliente_id = getattr(self, "_fiado_cliente_id", None) or self.cmb_cliente.currentData()
            if not cliente_id:
                if not getattr(self, "_fiado_flujo_activo", False):
                    self._reabrir_cuenta()
                else:
                    QMessageBox.warning(self, "Clientes", "No se seleccionó cliente.")
                return None
            c = cerebro.obtener(cliente_id)
            if not c:
                QMessageBox.warning(self, "Clientes", "Cliente no encontrado.")
                return None
            disp = cerebro.credito_disponible(c)
            p1_float = float(p1_t) if p1_t else 0
            if p1_float > disp + 0.01:
                QMessageBox.warning(self, "Clientes", f"Crédito insuficiente.\nDisp: ${disp:.2f}\nReq: ${p1_float:.2f}")
                return None

        p1, p2 = CobroController.validar_monto_suficiente(
            self.current_metodo,
            self.total_final,
            p1_t,
            p2_t,
            getattr(self, 'valores_mixtos', None)
        )

        if p1 is None and p2 is None:
            if self.current_metodo != "Mixto" and not p1_t.strip().replace('.', '', 1).isdigit():
                self._avisar("El monto ingresado no es válido.")
            else:
                # Si falta dinero y no es mixto, ofrecer pasarse a Mixto
                if self.current_metodo == "Mixto":
                    return None
                try:
                    p1_val = float(p1_t) if p1_t else 0.0
                except ValueError:
                    p1_val = 0.0
                self.set_metodo("Mixto")
                self.panel_mixto.txt_efectivo.setText(f"{p1_val:.2f}")
                self.panel_mixto.txt_efectivo.setFocus()
            return None

        return (p1, p2)

    def intentar_finalizar(self):
        if getattr(self, "_point_en_curso", False):
            return
        if self.current_metodo == "Tarjeta":
            if self.panel_tarjeta.bloquea_enter():
                return
            self.txt_pago.setText(self._monto(self.total_final))
            self.finalizar(imprimir=False)
            return
        if self.current_metodo == "Mixto":
            self._entrar_mixto(False)
            return
        if self.current_metodo in ("Fiado", "Clientes"):
            if getattr(self, "_fiado_flujo_activo", False):
                return
            if getattr(self, "_fiado_cliente_id", None):
                self.finalizar(imprimir=False)
            else:
                self._reabrir_cuenta()
            return
        if self.current_metodo == "QR" and self.panel_qr.bloquea_enter():
            return
        vals = self._validar_pago()
        if vals:
            # Enter se comporta como F2 (Solo registrar, sin imprimir) para máxima velocidad
            self.finalizar(imprimir=False)

    def recargar_total_final(self):
        monto_desc = getattr(self, 'descuento_monto', 0.0)
        monto_rec = getattr(self, 'recargo_monto', 0.0)

        from src.utils.dinero import redondear_dinero
        self.total_final = redondear_dinero(max(0.0, self.total_original - monto_desc + monto_rec))
        oferta = abs(float(getattr(self, "descuentaso_oferta", 0.0) or 0.0))
        lista = redondear_dinero(self.total_original + oferta)
        self.lbl_total.setText(self._monto(self.total_final))
        if hasattr(self, "hoja_cuenta") and self.hoja_cuenta.isVisible():
            self.hoja_cuenta.fijar_monto(self.total_final)
        if abs(lista - self.total_final) > 0.009:
            self.lbl_precio_real.setText(
                f'<span style="color:#EF4444; text-decoration:line-through;">{self._monto(lista)}</span>'
            )
            self.lbl_precio_real.show()
        else:
            self.lbl_precio_real.hide()

        # El neto destacado de abajo se actualiza en caliente
        self.lbl_neto.setText(f"NETO A PAGAR: ${self.total_final:,.2f}")
        if (
            self.current_metodo == "QR"
            and hasattr(self, "panel_qr")
            and self.panel_qr._modo in ("buscando", "esperando")
        ):
            self._qr_monto_timer.start(500)
        if self.current_metodo == "Mixto" and hasattr(self, "panel_mixto"):
            self.panel_mixto.fijar_total(self.total_final)
        if self.current_metodo == "Tarjeta" and hasattr(self, "panel_tarjeta") and self.panel_tarjeta.isVisible():
            self._tarjeta_monto_timer.start(500)

        # Actualizar visualización del botón de Descuento (Premium UX!)
        _btn_compact = "border-radius: 8px; font-weight: 900; font-size: 14px; border: none; padding: 8px 12px;"
        if getattr(self, 'descuento_monto', 0.0) > 0:
            self.btn_descuento.setText(f"F3\n-${self.descuento_monto:,.0f}")
            self.btn_descuento.setStyleSheet(f"background: #047857; color: white; {_btn_compact}")
        else:
            self.btn_descuento.setText("F3\nredondeo")
            self.btn_descuento.setStyleSheet(f"background: #10B981; color: white; {_btn_compact}")

        if getattr(self, 'recargo_monto', 0.0) > 0:
            self.btn_recargo.setText(f"F4\n+${self.recargo_monto:,.0f}")
            self.btn_recargo.setStyleSheet(f"background: #B45309; color: white; {_btn_compact}")
        else:
            self.btn_recargo.setText("F4\nrecargo")
            self.btn_recargo.setStyleSheet(f"background: #F59E0B; color: white; {_btn_compact}")

        # Si el método es electrónico, actualizar el autocompletado del pago de inmediato
        foto_qr = self.current_metodo == "QR" and getattr(self.panel_qr, "_modo", "") == "foto"
        if self.current_metodo in ["Tarjeta", "Transferencia"] or (
            self.current_metodo == "QR" and not foto_qr
        ):
            self.txt_pago.setText(self._monto(self.total_final))

        self.calcular_vuelto()

    def _toggle_tipo_desc(self):
        if self.btn_tipo_desc.text() == "$":
            self.btn_tipo_desc.setText("%")
        else:
            self.btn_tipo_desc.setText("$")
        self.on_descuento_changed(self.txt_desc.text())

    def _toggle_tipo_rec(self):
        if self.btn_tipo_rec.text() == "$":
            self.btn_tipo_rec.setText("%")
        else:
            self.btn_tipo_rec.setText("$")
        self.on_recargo_changed(self.txt_rec.text())

    def on_descuento_changed(self, text):
        try:
            txt = text.strip()
            if not txt:
                self.descuento_monto = 0.0
            elif txt.endswith('%') or (hasattr(self, 'btn_tipo_desc') and self.btn_tipo_desc.text() == "%"):
                val = float(txt.replace('%', ''))
                self.descuento_monto = self.total_original * (max(0, min(100, val)) / 100.0)
            else:
                val = float(txt.replace('$', '').strip())
                self.descuento_monto = max(0.0, val)
            self.recargar_total_final()
        except ValueError:
            pass

    def on_recargo_changed(self, text):
        try:
            txt = text.strip()
            if not txt:
                self.recargo_monto = 0.0
            elif txt.endswith('%') or (hasattr(self, 'btn_tipo_rec') and self.btn_tipo_rec.text() == "%"):
                val = float(txt.replace('%', ''))
                self.recargo_monto = self.total_original * (max(0, val) / 100.0)
            else:
                val = float(txt.replace('$', '').strip())
                self.recargo_monto = max(0.0, val)
            self.recargar_total_final()
        except ValueError:
            pass

    def abrir_descuento(self):
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0: return
        self.txt_desc.setFocus()
        self.txt_desc.selectAll()

    def abrir_recargo(self):
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0: return
        self.txt_rec.setFocus()
        self.txt_rec.selectAll()

    def _frase_ticket(self, modo):
        if modo == "cierra":
            return "Sin ticket. Al pagar, la venta se cierra sola. Si el cliente lo pide, F1."
        if modo == "fiscal":
            return "Al pagar se imprime el ticket fiscal."
        return "Al pagar se imprime el ticket."

    def _elegir_cierre(self, modo):
        """F1 imprime al pagar. F2 cierra sin ticket. F10 es el fiscal.
        Si todavía se espera el cobro, el clic no cierra: avisa una vez y queda elegido."""
        if modo == "fiscal":
            config._load_config()
            if not config.get("facturacion_afip_global", False):
                self._avisar("La facturación AFIP está apagada. F1 imprime el ticket común.")
                return
        if self._frase_espera():
            if getattr(self, "_ticket_al_pagar", None) == modo:
                return
            self._ticket_al_pagar = modo
            self._mixto_imprimir = modo != "cierra"
            self._avisar(self._frase_ticket(modo))
            return
        if modo == "fiscal":
            self.set_metodo("Efectivo")
            self.finalizar(True, force_fiscal=True)
        elif modo == "cierra":
            self.finalizar(False)
        else:
            self.finalizar(True)

    def _cerrar_como_eligio(self):
        modo = getattr(self, "_ticket_al_pagar", None) or "imprime"
        if modo == "cierra":
            self.finalizar(False)
        elif modo == "fiscal":
            self.finalizar(True, force_fiscal=True)
        else:
            self.finalizar(True)

    def finalizar_fiscal_efectivo(self):
        self._elegir_cierre("fiscal")

    def finalizar(self, imprimir=True, force_fiscal=False, emergencia=False):
        if not emergencia:
            if getattr(self, "_point_en_curso", False):
                return
            if (
                self.current_metodo == "Tarjeta"
                and hasattr(self, "panel_tarjeta")
                and self.panel_tarjeta.bloquea_enter()
                and not getattr(self, "_tarjeta_cerrando", False)
            ):
                return
            if self.current_metodo == "Mixto" and not getattr(self, "_mixto_cerrando", False):
                self._entrar_mixto(imprimir)
                return
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0:
            if self.current_metodo not in ("Mixto", "Fiado", "Clientes"):
                return
        if getattr(self, '_procesando_pago', False):
            return

        vals = self._validar_pago()
        if not vals: return

        self._procesando_pago = True
        p1, p2 = vals

        try:
            from src.cajero.cajero_activo import CajeroActivo
            cajero_secundario = CajeroActivo.nombre if CajeroActivo.numero == 2 else ''
            cajero_actual = dict(config.current_user).get('username', 'cajero') if config.current_user else 'cajero'
            cliente_id = getattr(self, "_fiado_cliente_id", None) or self.cmb_cliente.currentData()

            from src.cajero.paso6_cobro.motor_pagos.motor_principal import MotorPrincipalCobros

            datos_orden = {
                "total_final": self.total_final,
                "p1": p1,
                "p2": p2,
                "items_carrito": self.items_carrito,
                "cajero": cajero_actual,
                "cajero_sec": cajero_secundario,
                "descuento": getattr(self, 'descuento_monto', 0.0),
                "recargo": getattr(self, 'recargo_monto', 0.0),
                "oferta": getattr(self, 'descuentaso_oferta', 0.0),
                "nombre_pendiente": getattr(self, 'nombre_pendiente', None),
                "cliente_id": cliente_id,
                "imprimir": imprimir,
                "force_fiscal": force_fiscal,
                "request_id": getattr(self, "request_id", None),
                "mp_pago": getattr(self, "_mp_pago_usado", None),
                "mp_pagos": list(getattr(self, "_mp_pagos", None) or []),
            }

            exito, mensaje = MotorPrincipalCobros.iniciar_transaccion(
                metodo=self.current_metodo,
                datos_ui=datos_orden
            )

            if exito:
                self.accept()
            else:
                self._procesando_pago = False
                self.btn_cobrar.setEnabled(True)
                self.btn_cancelar.setEnabled(True)
                QMessageBox.critical(self, "Error al cobrar", mensaje)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self._procesando_pago = False
            self.btn_cobrar.setEnabled(True)
            self.btn_cancelar.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Excepción crítica al cobrar:\n{e}\n\n{tb}")

    def imprimir_ticket(self, id_v, abrir_manual=False, force_fiscal=False):
        # Este método ha sido movido a CobroController.procesar_cajon_impresion
        # Lo dejamos aquí por retrocompatibilidad temporal si otras partes lo llaman directamente
        pass

    def reject(self):
        try:
            self.timer_mp.stop()
        except Exception:
            pass
        if getattr(self, "_point_en_curso", False):
            self.espera_point.soltar()
        try:
            from src.notificaciones.motor.estado import publicar

            publicar("cobro_cancelado", "⛔ COBRO CANCELADO", segundos=10)
        except Exception:
            pass
        super().reject()

    def eventFilter(self, watched, event):
        # Evitar fallos de inicialización si los widgets aún no se han creado en setup_ui
        if not hasattr(self, 'txt_pago') or not hasattr(self, 'txt_otro') or not hasattr(self, 'txt_desc') or not hasattr(self, 'txt_rec'):
            return super().eventFilter(watched, event)

        campos = [self.txt_pago, self.txt_otro, self.txt_desc, self.txt_rec]
        mixto = getattr(self, "panel_mixto", None)
        if mixto is not None:
            campos.extend(mixto.campos())
        if watched in campos and event.type() == QEvent.Type.KeyPress:
            k = event.key()
            if getattr(self, "stack", None) and self.stack.currentIndex() == 0 and es_flecha(k):
                marcar_tarjeta(self, metodo_con_flecha(self, k))
                return True
            if event.isAutoRepeat() and k in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                return True # Bloquear auto-repeat ENTER en los campos de texto

            # LAS FLECHAS YA NO CAMBIAN EL MÉTODO (Lógica nueva)
            # Solo permiten moverse dentro del QLineEdit
            elif event.type() == QEvent.Type.FocusOut:
                # Si pierde el foco hacia algo que no sea un botón interno, no ocultar
                pass
                return False

            # Asegurarnos de que las teclas de función (F1-F12) se procesen siempre, aunque el cursor esté en el casillero
            if k == Qt.Key.Key_F11:
                if self.btn_f11.isVisible():
                    self.procesar_pago_mercadopago_point()
                return True
            elif k == Qt.Key.Key_F12:
                self._tecla_f12()
                return True
            elif k == Qt.Key.Key_F1:
                self._elegir_cierre("imprime")
                return True
            elif k == Qt.Key.Key_F2:
                self._elegir_cierre("cierra")
                return True
            elif k == Qt.Key.Key_F10:
                self._elegir_cierre("fiscal")
                return True
            elif k == Qt.Key.Key_F9:
                self._emergencia()
                return True

        return super().eventFilter(watched, event)



    def _tpv_point_listo(self):
        config._load_config()
        token = str(config.get("mp_access_token", "") or "").strip()
        device = str(config.get("mp_device_id", "") or "").strip()
        return bool(token and device)

    def _pos_qr(self):
        pos = str(config.get("mp_qr_pos_external_id", "") or "").strip()
        if not pos:
            pos = str(config.get("mp_external_pos_id", "") or "").strip()
        return pos

    def _tpv_qr_listo(self):
        config._load_config()
        token = str(config.get("mp_access_token", "") or "").strip()
        user = str(config.get("mp_user_id", "") or "").strip()
        return bool(token and user and self._pos_qr())

    def _pintar_luz_tpv(self):
        config._load_config()
        token = str(config.get("mp_access_token", "") or "").strip()
        device = str(config.get("mp_device_id", "") or "").strip()
        user = str(config.get("mp_user_id", "") or "").strip()
        listo = bool(token and device) or bool(token and user and self._pos_qr())
        self._tpv_listo = listo
        if hasattr(self, "teclado_lateral"):
            self.teclado_lateral.mostrar_emergencia(listo)
        color = "#22C55E" if listo else "#EF4444"
        texto = "TPV listo" if listo else "TPV sin activar"
        estilo = (
            f"background: {color}; border-radius: 8px; border: none;"
        )
        for luz in (getattr(self, "luz_tpv", None), getattr(self, "luz_tpv_metodos", None)):
            if luz is None:
                continue
            luz.setStyleSheet(estilo)
            luz.setToolTip(texto)

    def _repartir_hueco(self, qr=0, tarjeta=0, monto=0, hueco=0):
        self.content_lay.setStretch(self._idx_qr, qr)
        self.content_lay.setStretch(self._idx_tarjeta, tarjeta)
        self.content_lay.setStretch(self._idx_monto, monto)
        self.content_lay.setStretch(self._idx_hueco, hueco)
        if hueco:
            self.hueco_pie.setMaximumHeight(16777215)
        else:
            self.hueco_pie.setMaximumHeight(0)

    def _ajustar_contenedor_monto(self):
        if not hasattr(self, "panel_monto"):
            return
        foto = self.current_metodo == "QR" and getattr(self.panel_qr, "_modo", "") == "foto"
        if self.current_metodo == "QR":
            self.panel_monto.ajustar(self.current_metodo, foto)
            self._repartir_hueco(qr=1, hueco=0)
            return
        if self.current_metodo == "Tarjeta":
            self.panel_monto.hide()
            self._repartir_hueco(tarjeta=1)
            return
        llena = self.panel_monto.ajustar(self.current_metodo, foto)
        if llena:
            self._repartir_hueco(monto=1)
        else:
            self._repartir_hueco(hueco=1)

    def _vista_monto_qr(self, modo=""):
        """En QR se van «paga con» y el neto. La foto vuelve a pedir el monto."""
        if self.current_metodo != "QR":
            return
        foto = (modo or getattr(self.panel_qr, "_modo", "")) == "foto"
        self.lbl_neto.hide()
        self.lbl_input1.setVisible(foto)
        self.txt_pago.setVisible(foto)
        if foto:
            self.lbl_input1.setText("PAGA CON ($):")
            self.txt_pago.setReadOnly(False)
            self.txt_pago.setFocus()
            self.txt_pago.selectAll()
        self._ajustar_contenedor_monto()

    def _refrescar_qr_si_vivo(self):
        if self.current_metodo != "QR":
            return
        if self.panel_qr._modo not in ("buscando", "esperando"):
            return
        self.panel_qr.mostrar(self.total_final, forzar=True)

    def _alternar_aviso_mp(self):
        from src.services.mp_escucha import EscuchaMP
        EscuchaMP.fijar_sonido(self.btn_aviso_mp.isChecked())
        self._pintar_aviso_mp()

    def _pintar_aviso_mp(self):
        from src.services.mp_escucha import EscuchaMP
        activo = EscuchaMP.con_sonido()
        self.btn_aviso_mp.setChecked(activo)
        self.btn_aviso_mp.setText("Con sonido" if activo else "Cajero silencioso")

    def _frase_espera(self):
        """Con el TPV activo, Enter no registra: hay que esperar el cobro."""
        if not getattr(self, "_tpv_listo", False):
            return ""
        if getattr(self, "_point_en_curso", False):
            return "Espere la tarjeta."
        if getattr(self, "_mixto_espera_transferencia", None) is not None:
            return "Espere la transferencia."
        if self.current_metodo == "Transferencia":
            return "Espere la transferencia."
        if getattr(self, "_mixto_esperando_qr", False) and self.panel_qr.bloquea_enter():
            return "Espere el QR."
        if self.current_metodo == "QR" and self.panel_qr.bloquea_enter():
            return "Espere el QR."
        if self.current_metodo == "Tarjeta" and self.panel_tarjeta.bloquea_enter():
            return "Espere la tarjeta."
        return ""

    def _enter_cobro(self):
        if hasattr(self, "aviso_toast") and self.aviso_toast.tiene_accion():
            self.aviso_toast.aceptar()
            return
        self._pintar_luz_tpv()
        if not getattr(self, "_tpv_listo", False) and self.current_metodo not in ("Fiado", "Clientes"):
            self._guardar_sin_tpv(False)
            return
        frase = self._frase_espera()
        if frase and hasattr(self, "aviso_toast"):
            self.aviso_toast.alarma(frase)
            return
        self.intentar_finalizar()

    def _emergencia(self):
        if not getattr(self, "_tpv_listo", False):
            return
        if getattr(self, "stack", None) and self.stack.currentIndex() == 0:
            return
        if getattr(self, "_point_en_curso", False):
            self._emergencia_pendiente = True
            self.espera_point.soltar()
            return
        self._cerrar_manual()

    def _cerrar_manual(self):
        self._guardar_sin_tpv(False)

    def _guardar_sin_tpv(self, imprimir):
        """Luz roja: Enter guarda la venta. No manda el Point ni espera transferencia ni QR."""
        self._emergencia_pendiente = False
        self._mixto_pasos = None
        self._mixto_espera_transferencia = None
        self._mixto_esperando_qr = False
        try:
            self.timer_mp.stop()
            self.timer_spinner.stop()
        except Exception:
            pass
        if hasattr(self, "aviso_toast"):
            self.aviso_toast.cerrar()
        if self.current_metodo == "Mixto" and hasattr(self, "panel_mixto"):
            self.valores_mixtos = self.panel_mixto.valores()
        elif self.current_metodo in ("Tarjeta", "Transferencia", "QR"):
            self.txt_pago.setText(self._monto(self.total_final))
        self.finalizar(bool(imprimir), emergencia=True)

    def _avisar(self, mensaje):
        if hasattr(self, "aviso_toast"):
            self.aviso_toast.mostrar(mensaje)

    def _esperado_transferencia(self):
        espera = getattr(self, "_mixto_espera_transferencia", None)
        if espera is not None:
            return float(espera)
        if self.current_metodo == "Mixto" and hasattr(self, "panel_mixto"):
            parte = float(self.panel_mixto.valores().get("mercadopago") or 0)
            if parte > 0.009:
                return parte
        return float(self.total_final or 0)

    def _ofrecer_vinculo(self, pago_id, monto, nombre=None):
        """El monto no coincide: el cartel deja atar esa transferencia a esta venta."""
        importe = float(monto or 0)
        quien = str(nombre or "").strip()
        if quien.lower() in ("", "none", "none none", "cliente", "desconocido", "transferencia recibida"):
            texto = f"Llegó ${importe:,.2f}. ¿Asociar al ticket o espere otro monto?"
        else:
            texto = f"Llegó ${importe:,.2f} de {quien}. ¿Asociar al ticket o espere otro monto?"
        if not hasattr(self, "aviso_toast"):
            return
        self.aviso_toast.mostrar(
            texto,
            accion=lambda: self._vincular_transferencia(str(pago_id), importe),
            rotulo="Asociar",
        )

    def _vincular_transferencia(self, pago_id, monto):
        """La diferencia queda en redondeo o recargo y esa transferencia no se vuelve a usar."""
        from src.cajero.paso6_cobro.vinculo_mp.libro import asociado

        if asociado(pago_id):
            self._avisar("No hay nueva transferencia.")
            return
        if getattr(self, "_vinculando", False):
            return
        self._vinculando = True
        try:
            diferencia = float(monto) - self._esperado_transferencia()
            if diferencia < -0.05:
                nuevo = float(getattr(self, "descuento_monto", 0) or 0) + abs(diferencia)
                self.txt_desc.setText(f"{nuevo:.2f}")
            elif diferencia > 0.05:
                nuevo = float(getattr(self, "recargo_monto", 0) or 0) + diferencia
                self.txt_rec.setText(f"{nuevo:.2f}")
            if self.current_metodo == "Mixto":
                valores = getattr(self, "valores_mixtos", None) or {}
                valores["mercadopago"] = float(monto)
                self.valores_mixtos = valores
            try:
                from src.base_de_datos.database import db_manager

                db_manager.execute_non_query(
                    "INSERT INTO mp_transferencias_usadas (payment_id) VALUES (?)",
                    (str(pago_id),),
                )
            except Exception:
                pass
            self._anotar_pago_mp(
                {"id": pago_id, "transaction_amount": float(monto)},
                float(monto),
            )
            from src.admin.mercadopago.mercadopago_main import Admin10MP

            Admin10MP.ultimo_pago_detectado = None
            if getattr(self, "_mixto_espera_transferencia", None) is not None:
                self._mixto_espera_transferencia = None
                self.lbl_mp_status.hide()
                self.timer_mp.stop()
                self.timer_spinner.stop()
                self._mixto_i += 1
                QTimer.singleShot(200, self._seguir_mixto)
                return
            self.txt_pago.setText(self._monto(float(monto)))
            self._cerrar_como_eligio()
        finally:
            self._vinculando = False

    def _aviso_tarjeta(self, modo):
        if modo == "fallo" and self.panel_tarjeta.isVisible():
            self._avisar(self.panel_tarjeta.estado.text())

    def _refrescar_tarjeta(self):
        if self.current_metodo != "Tarjeta" or getattr(self, "_point_en_curso", False):
            return
        self.txt_pago.setText(self._monto(self.total_final))
        self._cobrar_tarjeta_point()

    def _tarjeta_cancelada(self):
        motivo = getattr(getattr(self, "espera_point", None), "motivo", "")
        return motivo in ("usuario", "cancelo")

    def _volver_a_metodos(self):
        self._ticket_al_pagar = None
        self._mixto_pasos = None
        self._mixto_confirmado = False
        self._mixto_espera_transferencia = None
        self._mixto_esperando_qr = False
        try:
            self.timer_mp.stop()
            self.timer_spinner.stop()
        except Exception:
            pass
        if hasattr(self, "aviso_toast"):
            self.aviso_toast.cerrar()
        self.stack.setCurrentIndex(0)
        self.setFocus()

    def _cobrar_tarjeta_point(self):
        if self.current_metodo != "Tarjeta" or getattr(self, "_point_en_curso", False):
            return
        from src.cajero.paso6_cobro.mercadopago_core.point_service import PointService
        ok = PointService(self).procesar_pago_mercadopago_point(cerrar=False)
        if getattr(self, "_emergencia_pendiente", False):
            self._cerrar_manual()
            return
        if ok is True and self.current_metodo == "Tarjeta":
            self._anotar_point()
            self._cerrar_venta_por_tarjeta(self.total_final)
            return
        if self._tarjeta_cancelada():
            self._volver_a_metodos()

    def _cerrar_venta_por_tarjeta(self, monto):
        if getattr(self, "_tarjeta_ya_cerrado", False):
            return
        self._tarjeta_ya_cerrado = True
        self.txt_pago.setText(self._monto(monto))
        self._tarjeta_cerrando = True
        try:
            self._cerrar_como_eligio()
        finally:
            self._tarjeta_cerrando = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "aviso_toast"):
            self.aviso_toast.ubicar()
        if hasattr(self, "espera_point") and self.espera_point.isVisible():
            self.espera_point.ubicar()
        if hasattr(self, "hoja_cuenta") and self.hoja_cuenta.isVisible():
            self.hoja_cuenta.ubicar()

    def _reparto_mixto(self, valores):
        from src.utils.dinero import redondear_dinero

        datos = valores or {}
        return tuple(
            redondear_dinero(datos.get(clave) or 0)
            for clave in ("efectivo", "tarjeta", "mercadopago", "qr")
        )

    def _soltar_pasos_mixto(self):
        """Suelta la escucha, el QR o el Point que quedó de un reparto anterior."""
        self._mixto_pasos = None
        self._mixto_esperando_qr = False
        self._mixto_espera_transferencia = None
        self.timer_mp.stop()
        self.timer_spinner.stop()
        self.lbl_mp_status.hide()
        if hasattr(self, "panel_qr") and self.panel_qr.isVisible():
            self.panel_qr.ocultar()
        if hasattr(self, "panel_tarjeta") and self.panel_tarjeta.isVisible():
            self.panel_tarjeta.ocultar()
        if self.current_metodo == "Mixto" and hasattr(self, "panel_mixto"):
            self.panel_mixto.show()
            self.panel_mixto._recalcular()
            self._ajustar_contenedor_monto()

    def _entrar_mixto(self, imprimir):
        self._pintar_luz_tpv()
        if not getattr(self, "_tpv_listo", False):
            self._guardar_sin_tpv(imprimir)
            return
        if getattr(self, "_mixto_pasos", None) is not None:
            if getattr(self, "_mixto_esperando_qr", False) and not self.panel_qr.bloquea_enter():
                self._mixto_esperando_qr = False
                self._mixto_i += 1
                self._seguir_mixto()
            return
        if not self.panel_mixto.cubre():
            return
        from src.cajero.paso6_cobro.mixto_en_cobro.confirmar import pasos_vivos
        self.valores_mixtos = self.panel_mixto.valores()
        self._mixto_imprimir = imprimir
        self._mixto_confirmado = True
        self._mixto_pasos = pasos_vivos(self.valores_mixtos)
        self._mixto_i = 0
        self._mixto_esperando_qr = False
        self._mixto_espera_transferencia = None
        self._seguir_mixto()

    def _seguir_mixto(self):
        pasos = getattr(self, "_mixto_pasos", None) or []
        if self._mixto_i >= len(pasos):
            self._mixto_pasos = None
            self._mixto_cerrando = True
            try:
                if getattr(self, "_ticket_al_pagar", None):
                    self._cerrar_como_eligio()
                else:
                    self.finalizar(getattr(self, "_mixto_imprimir", False))
            finally:
                self._mixto_cerrando = False
            return
        tipo, monto = pasos[self._mixto_i]
        if tipo == "tarjeta":
            from src.cajero.paso6_cobro.mercadopago_core.point_service import PointService
            aviso = PointService(self).procesar_pago_mercadopago_point(cerrar=False)
            if getattr(self, "_emergencia_pendiente", False):
                self._mixto_pasos = None
                self._cerrar_manual()
                return
            if aviso is None:
                self._mixto_pasos = None
                if self._tarjeta_cancelada():
                    self._volver_a_metodos()
                    return
                if self.current_metodo == "Mixto" and self.isVisible():
                    self.panel_mixto.show()
                return
            self._anotar_point()
            self._mixto_i += 1
            self._seguir_mixto()
            return
        if tipo == "transferencia":
            self._mixto_espera_transferencia = float(monto)
            from src.services.mp_escucha import EscuchaMP
            EscuchaMP.asegurar()
            self.panel_mixto.estado.setText(f"Escuchando transferencia {self._monto(monto)}")
            self.panel_mixto.estado.setStyleSheet(
                "color: #0EA5E9; font-size: 20px; font-weight: 800; background: transparent; border: none;"
            )
            self.lbl_mp_status.show()
            self.timer_mp.start(1000)
            self.timer_spinner.start(60)
            return
        self.panel_mixto.ocultar()
        self._mixto_espera_transferencia = None
        self.timer_mp.stop()
        self.timer_spinner.stop()
        self.lbl_mp_status.hide()
        self._mixto_esperando_qr = True
        self._repartir_hueco(qr=1)
        self._pintar_luz_tpv()
        if not self._tpv_qr_listo():
            self.panel_qr.ofrecer_foto()
            self.panel_qr.estado.setText(
                f"Foto del QR por {self._monto(monto)}. Enter registra esta parte."
            )
        else:
            self.panel_qr.mostrar(monto, forzar=True)

    def _anotar_point(self):
        pago = getattr(getattr(self, "espera_point", None), "_pago", None)
        self._anotar_pago_mp(pago, self.total_final)

    def _anotar_pago_mp(self, pago, monto=None):
        """Deja el cobro en el monitor y, si hay id, listo para el ticket."""
        if not isinstance(pago, dict) or not pago.get("id"):
            return
        try:
            importe = float(pago.get("transaction_amount") or monto or 0)
        except (TypeError, ValueError):
            importe = float(monto or 0)
        ficha = {"id": str(pago.get("id")), "monto": importe}
        lista = [
            item for item in (getattr(self, "_mp_pagos", None) or [])
            if str(item.get("id")) != ficha["id"]
        ]
        lista.append(ficha)
        self._mp_pagos = lista
        self._mp_pago_usado = ficha
        try:
            from src.admin.mercadopago.historial.archivo import guardar

            guardar([pago])
        except Exception:
            pass
        try:
            from src.admin.mercadopago.mercadopago_main import Admin10MP

            vista = getattr(Admin10MP, "vista", None)
            if vista is not None:
                vista.cargar_datos_locales()
        except Exception:
            pass

    def _cerrar_venta_por_qr(self, monto):
        self._anotar_pago_mp(getattr(self.panel_qr, "_pago", None), monto)
        if getattr(self, "_mixto_esperando_qr", False):
            self._mixto_esperando_qr = False
            self.panel_qr.ocultar()
            self._mixto_i += 1
            self._seguir_mixto()
            return
        if getattr(self, "_qr_ya_cerrado", False):
            return
        self._qr_ya_cerrado = True
        self.txt_pago.setText(self._monto(monto))
        self._cerrar_como_eligio()

    def _tomar_mixto(self, valores):
        if getattr(self, "_point_en_curso", False):
            return
        if getattr(self, "_mixto_rearmando", False):
            self.valores_mixtos = valores
            return
        if getattr(self, "_mixto_pasos", None) is not None:
            if self._reparto_mixto(valores) == self._reparto_mixto(getattr(self, "valores_mixtos", None)):
                return
            self._mixto_rearmando = True
            try:
                self._soltar_pasos_mixto()
                self.valores_mixtos = valores
                if self.current_metodo == "Mixto" and self.panel_mixto.cubre():
                    self._entrar_mixto(getattr(self, "_mixto_imprimir", False))
            finally:
                self._mixto_rearmando = False
            return
        self.valores_mixtos = valores
        if (
            getattr(self, "_mixto_confirmado", False)
            and self.current_metodo == "Mixto"
            and getattr(self, "_mixto_pasos", None) is None
            and self.panel_mixto.cubre()
        ):
            self._entrar_mixto(getattr(self, "_mixto_imprimir", False))

    def _ajustar_botones_mp(self):
        """Cada columna conserva el hueco. Solo se ve el botón del medio elegido."""
        if not hasattr(self, "pila_point"):
            return
        metodo = self.current_metodo
        self.pila_point.setCurrentIndex(0 if metodo in ("Tarjeta", "Mixto") else 1)
        if hasattr(self, "pila_f2"):
            self.pila_f2.setCurrentIndex(1 if metodo == "Mixto" else 0)
        if metodo == "Mixto":
            self.pila_extra.setCurrentIndex(0)
        elif metodo == "Transferencia":
            self.pila_extra.setCurrentIndex(1)
        else:
            self.pila_extra.setCurrentIndex(2)
        self._pintar_boton_fiscal()

    def _pintar_boton_fiscal(self):
        if not hasattr(self, "teclado_lateral"):
            return
        config._load_config()
        self.teclado_lateral.mostrar_fiscal(bool(config.get("facturacion_afip_global", False)))

    def _tecla_f12(self):
        if self.current_metodo == "Transferencia":
            self.corroborar_ultimo_monto()
        elif self.current_metodo == "Mixto":
            if getattr(self, "_mixto_esperando_qr", False):
                self.verificar_transferencia_mp()
            else:
                self.corroborar_ultimo_monto()
        elif self.current_metodo == "Tarjeta" and self.btn_f12.isVisible():
            self.verificar_transferencia_mp()

    def corroborar_ultimo_monto(self):
        if getattr(self, "stack", None) and self.stack.currentIndex() == 0:
            return
        from src.cajero.paso6_cobro.mercadopago_core.polling_service import PollingService
        PollingService(self).ultimo_monto_recibido()

    def procesar_pago_mercadopago_point(self):
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0: return
        if self.current_metodo == "QR":
            return
        if self.current_metodo == "Mixto":
            self.valores_mixtos = self.panel_mixto.valores()
            if float(self.valores_mixtos.get("tarjeta") or 0) <= 0.009:
                self._avisar("No hay monto de tarjeta para el Point.")
                return
            from src.cajero.paso6_cobro.mercadopago_core.point_service import PointService
            PointService(self).procesar_pago_mercadopago_point(cerrar=False)
            return
        if self.current_metodo == "Tarjeta":
            if not getattr(self, "_point_en_curso", False):
                self._cobrar_tarjeta_point()
            return
        from src.cajero.paso6_cobro.mercadopago_core.point_service import PointService
        if PointService(self).procesar_pago_mercadopago_point() is False:
            self.finalizar(False)

    def _procesar_cobro_qr_pantalla(self, token, monto):
        from src.cajero.paso6_cobro.mercadopago_core.qr_service import QRService
        QRService(self).procesar_cobro_qr_pantalla(token, monto)

    def verificar_transferencia_mp(self):
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0: return
        from src.cajero.paso6_cobro.mercadopago_core.polling_service import PollingService
        PollingService(self).verificar_transferencia_mp()

    def keyPressEvent(self, event):
        if getattr(self, "stack", None) and self.stack.currentIndex() == 0:
            atender_pagina_metodos(self, event)
            return

        if event.isAutoRepeat():
            return

        k = event.key()

        # =========================================================
        # A partir de aquí, solo se ejecuta si estamos en la Página 1
        # =========================================================

        if k == Qt.Key.Key_F1: self._elegir_cierre("imprime")
        elif k == Qt.Key.Key_F2: self._elegir_cierre("cierra")
        elif k == Qt.Key.Key_F3: self.abrir_descuento()
        elif k == Qt.Key.Key_F4: self.abrir_recargo()
        elif k == Qt.Key.Key_F10: self._elegir_cierre("fiscal")
        elif k == Qt.Key.Key_F9: self._emergencia()
        elif k == Qt.Key.Key_F11:
            if self.btn_f11.isVisible():
                self.procesar_pago_mercadopago_point()
        elif k == Qt.Key.Key_F12:
            self._tecla_f12()
        elif k == Qt.Key.Key_Escape:
            if self.current_metodo in ("Fiado", "Clientes") and self.hoja_cuenta.isVisible():
                self.hoja_cuenta._cancelar()
                return
            self.reject()
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            foco = self.focusWidget()
            if self.current_metodo in ("Fiado", "Clientes"):
                if self.hoja_cuenta.isVisible():
                    self.hoja_cuenta.confirmar()
                    return
                if getattr(self, "_fiado_cliente_id", None):
                    self.finalizar(imprimir=False)
                else:
                    self._reabrir_cuenta()
                return
            if isinstance(foco, QPushButton) and foco in self.btns.values():
                # 1. ENTER ELIGE MÉTODO -> Salta al casillero de monto
                self.txt_pago.setFocus()
                self.txt_pago.selectAll()
            else:
                self._enter_cobro()
        else:
            super().keyPressEvent(event)



    def on_teclado_key_clicked(self, key):
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0:
            if key in ("ESC", "Salir"):
                self.reject()
            elif key == "ENTER":
                if self.current_metodo:
                    self.procesar_click_metodo(self.current_metodo)
            return

        focused = self.focusWidget()
        if key == "F10":
            self._elegir_cierre("fiscal")
            return
        if (
            self.current_metodo in ("Fiado", "Clientes")
            and hasattr(self, "hoja_cuenta")
            and self.hoja_cuenta.isVisible()
        ):
            if key == "ENTER":
                self.hoja_cuenta.confirmar()
                return
            if key == "⌫":
                self.hoja_cuenta.borrar()
                return
            if len(str(key)) == 1:
                self.hoja_cuenta.escribir(key)
                return
        if key == "ENTER" and self.current_metodo in ("Transferencia", "QR", "Tarjeta", "Mixto"):
            self._enter_cobro()
            return
        if self.current_metodo == "Mixto":
            focused = self.panel_mixto.campo_foco()
            if key == "ENTER":
                self.intentar_finalizar()
                return
        elif self.current_metodo == "Tarjeta" and key == "ENTER":
            self.intentar_finalizar()
            return
        elif not focused or not isinstance(focused, QLineEdit):
            focused = self.txt_pago

        if key == "⌫":
            event_press = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.NoModifier, "")
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.Type.KeyRelease, Qt.Key.Key_Backspace, Qt.NoModifier, "")
            QApplication.sendEvent(focused, event_release)
