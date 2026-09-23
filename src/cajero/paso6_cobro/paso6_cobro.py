from src.utils.qt_compat import qt_exec
import hashlib
import os
from PIL import Image, ImageChops
from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QGridLayout,
    QWidget, QApplication, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QKeyEvent
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
        return min(1200, max(720, ancho - 80)), min(780, max(560, alto - 80))

    def _cubrir_paso5(self):
        parent = self.parent()
        if parent is None:
            return
        origen = parent.mapToGlobal(parent.rect().topLeft())
        self.setGeometry(origen.x(), origen.y(), parent.width(), parent.height())

    def showEvent(self, event):
        self._cubrir_paso5()
        super().showEvent(event)

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
        content_lay.setContentsMargins(40, 30, 40, 20)
        content_lay.setSpacing(30)

        self.lbl_total = QLabel(self._monto(self.total_original))
        self.lbl_total.setObjectName("CobroTotal")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_lay.addWidget(self.lbl_total)

        self.aviso_monto = QLabel("INGRESÁ EL MONTO RECIBIDO")
        self.aviso_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aviso_monto.setFixedHeight(84)
        self.aviso_monto.setStyleSheet(
            "background: #FEF3C7; color: #92400E; font-size: 32px; font-weight: 900; "
            "letter-spacing: 1px; border: 3px solid #F59E0B; border-radius: 14px; padding: 12px;"
        )
        self.aviso_monto.hide()
        content_lay.addWidget(self.aviso_monto)

        # Cargar lista de clientes para fiado
        self.lista_clientes = db_manager.execute_query("SELECT id, nombre, limite_credito, deuda_actual FROM clientes ORDER BY nombre ASC")


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
        for c in self.lista_clientes:
            disp = float(c['limite_credito']) - float(c['deuda_actual'])
            self.cmb_cliente.addItem(f"{c['nombre']} (Disp: ${disp:,.2f})", c['id'])

        self.lbl_cliente.hide()
        self.cmb_cliente.hide()

        grid_inputs.addWidget(self.lbl_cliente, 2, 0)
        grid_inputs.addWidget(self.cmb_cliente, 2, 1)
        content_lay.addLayout(grid_inputs)

        # NUEVA LÍNEA HORIZONTAL DE MODIFICADORES COMPACTA
        grid_desc_rec = QGridLayout()

        self.lbl_desc = QLabel("Redondeo ($):")
        self.lbl_desc.setObjectName("InputLabel")
        grid_desc_rec.addWidget(self.lbl_desc, 0, 0)

        self.txt_desc = QLineEdit("")
        self.txt_desc.setObjectName("InputDesc")
        self.txt_desc.setFixedHeight(48)
        self.txt_desc.setStyleSheet("font-size: 20px; font-weight: bold; border-radius: 8px; border: 1px solid #CBD5E1;")
        self.txt_desc.setPlaceholderText("0.00")
        self.txt_desc.textChanged.connect(self.on_descuento_changed)
        self.txt_desc.installEventFilter(self)
        grid_desc_rec.addWidget(self.txt_desc, 0, 1)

        self.lbl_rec = QLabel("Recargo ($):")
        self.lbl_rec.setObjectName("InputLabel")
        grid_desc_rec.addWidget(self.lbl_rec, 0, 2)

        self.txt_rec = QLineEdit("")
        self.txt_rec.setObjectName("InputRec")
        self.txt_rec.setFixedHeight(48)
        self.txt_rec.setStyleSheet("font-size: 20px; font-weight: bold; border-radius: 8px; border: 1px solid #CBD5E1;")
        self.txt_rec.setPlaceholderText("0.00")
        self.txt_rec.textChanged.connect(self.on_recargo_changed)
        self.txt_rec.installEventFilter(self)
        grid_desc_rec.addWidget(self.txt_rec, 0, 3)

        content_lay.addSpacing(10)
        content_lay.addLayout(grid_desc_rec)

        # NUEVO: Neto a cobrar destacado abajo
        self.lbl_neto = QLabel(f"NETO: $ {self.total_final:,.2f}")
        self.lbl_neto.setObjectName("NetoLabel")
        self.lbl_neto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_neto.setStyleSheet(
            "color: #1E3A8A; font-size: 28px; font-weight: 800; background: transparent; border: none;"
        )
        content_lay.addWidget(self.lbl_neto)

        # Vuelto (Extraído modularmente)
        self.resumen_vuelto = ResumenVuelto(self)
        content_lay.addWidget(self.resumen_vuelto)

        # Barra de Estado Mercado Pago con animación
        self.lbl_mp_status = QLabel("")
        self.lbl_mp_status.setObjectName("LblMpStatus")
        self.lbl_mp_status.setProperty("estado", "info")
        self.lbl_mp_status.setStyleSheet("font-size: 20px; font-weight: 900;") # Más grande y fuerte
        self.lbl_mp_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_mp_status.style().unpolish(self.lbl_mp_status)
        self.lbl_mp_status.style().polish(self.lbl_mp_status)
        self.lbl_mp_status.hide()
        content_lay.addWidget(self.lbl_mp_status)

        self.timer_mp = QTimer(self)
        self.timer_mp.timeout.connect(self.verificar_pago_mp_automatico)

        # Timer para el spinner y zoom
        self.mp_spinner_idx = 0
        self.mp_font_size = 20
        self.mp_font_dir = 1
        self.mp_spinner_chars = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]
        self.timer_spinner = QTimer(self)
        self.timer_spinner.timeout.connect(self._actualizar_spinner_mp)

        # Empujar el pie de página hasta abajo
        content_lay.addStretch()

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

        actions_grid = QGridLayout()
        actions_grid.setSpacing(5)
        actions_grid.setContentsMargins(0, 0, 0, 0)
        actions_grid.setColumnStretch(0, 1)
        actions_grid.setColumnStretch(1, 1)
        actions_grid.setColumnStretch(2, 1)

        actions_grid.addWidget(create_action_btn("F1", "imprime", lambda: self.finalizar(True), style="primary"), 0, 0)
        self.btn_f2 = create_action_btn("F2", "s/imprime", lambda: self.finalizar(False), style="featured")
        actions_grid.addWidget(self.btn_f2, 0, 1)
        self.btn_descuento = create_action_btn("F3", "redondeo", self.abrir_descuento, style="green")
        actions_grid.addWidget(self.btn_descuento, 0, 2)

        self.btn_recargo = create_action_btn("F4", "recargo", self.abrir_recargo, style="orange")
        actions_grid.addWidget(self.btn_recargo, 1, 0)
        self.btn_f11 = create_action_btn("F11", "Point MP", lambda: self.procesar_pago_mercadopago_point(), style="mp")
        actions_grid.addWidget(self.btn_f11, 1, 1)
        self.btn_f12 = create_action_btn("F12", "Verif QR", lambda: self.verificar_transferencia_mp(), style="qr")
        actions_grid.addWidget(self.btn_f12, 1, 2)

        right_lay.addLayout(actions_grid, 2)

        btn_f10 = create_action_btn("F10", "AFIP", lambda: self.finalizar_fiscal_efectivo())
        btn_f10.hide()
        right_lay.addWidget(btn_f10)

        # Teclado numérico extraído modularmente
        self.teclado_lateral = TecladoNumericoLateral(self)
        self.teclado_lateral.key_clicked.connect(self.on_teclado_key_clicked)
        right_lay.addWidget(self.teclado_lateral, 5)

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
        if key not in ("Mixto", "Fiado", "Clientes"):
            # Solo los métodos simples (Efectivo, Tarjeta, QR) pasan a la Pantalla 1
            self.stack.setCurrentIndex(1)
            self.txt_pago.setFocus()

        if key == "Clientes":
            self._activar_cliente_express()
            return
        elif key == "Fiado":
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
        metodo_previo = self.current_metodo
        marcar_tarjeta(self, key)

        if key == "Mixto":
            from src.cajero.paso6_cobro.widgets.pagos_mixtos import DialogoPagosMixtos
            dlg = DialogoPagosMixtos(self.total_final, self)
            if qt_exec(dlg):
                self.valores_mixtos = dlg.get_valores()
                self.current_metodo = "Mixto"
                self.lbl_input1.setText("MÚLTIPLES PAGOS ($):")
                self.lbl_input2.hide(); self.txt_otro.hide()
                self.lbl_cliente.hide(); self.cmb_cliente.hide()
                self.txt_pago.setText(self._monto(self.total_final))
                self.txt_pago.setReadOnly(True)
                self.lbl_mp_status.hide()
                self.timer_mp.stop()

                # Si hay monto de tarjeta, mandarlo al Point antes de finalizar
                monto_tarjeta = self.valores_mixtos.get("tarjeta", 0.0)
                if monto_tarjeta > 0 and self._tpv_point_listo():
                    QTimer.singleShot(200, lambda: self.procesar_pago_mercadopago_point())
                else:
                    # Sin tarjeta, finalizar directo
                    QTimer.singleShot(200, lambda: self.finalizar(True))
            else:
                self.set_metodo("Efectivo")
            return
        elif key in ["Tarjeta", "Transferencia", "QR"]:
            self.lbl_input1.setText("PAGA CON ($):")
            self.lbl_input2.hide(); self.txt_otro.hide()
            self.lbl_cliente.hide(); self.cmb_cliente.hide()
            # Autocompletar monto para medios electrónicos (evita errores y agiliza)
            self.txt_pago.setText(self._monto(self.total_final))

            if key == "Transferencia":
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
                self.timer_mp.start(1000)
                self.timer_spinner.start(60) # Gira y palpita rápido
            else:
                self.lbl_mp_status.hide()
                self.timer_mp.stop()
                self.timer_spinner.stop()
        elif key == "Clientes":
            if metodo_previo != "Clientes":
                self._revertir_tras_fiado = metodo_previo or "Efectivo"
            self.lbl_input1.setText("MONTO A FIAR ($):")
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
            self.lbl_input1.setText("MONTO A FIAR ($):")
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
        self.calcular_vuelto()
        if getattr(self, "stack", None) and self.stack.currentIndex() == 0:
            self.setFocus()
            return
        self.txt_pago.setFocus()
        self.txt_pago.selectAll()

    def _activar_cliente_express(self):
        """Clic en tarjeta Clientes → resalta y abre Cliente Express."""
        rev = self.current_metodo if self.current_metodo != "Clientes" else "Efectivo"
        self.set_metodo("Clientes")
        self._abrir_cliente_express(rev)

    def _abrir_cliente_express(self, revertir_a="Efectivo"):
        """Cliente Express en 2 ventanas."""
        from PyQt6.QtWidgets import QDialog
        from src.cajero.paso6_cobro.widgets.cliente_express import (
            DialogoClienteExpressPaso1,
            DialogoClienteExpressPaso2,
        )

        rev = revertir_a if revertir_a != "Clientes" else getattr(self, "_revertir_tras_fiado", "Efectivo")
        terminal = self.parent()
        self._fiado_flujo_activo = True

        cliente_ok = None
        dni_ref = ""

        while True:
            dlg1 = DialogoClienteExpressPaso1(self.total_final, self)
            if qt_exec(dlg1) != QDialog.DialogCode.Accepted:
                self._fiado_flujo_activo = False
                self._fiado_cliente_id = None
                self.set_metodo(rev)
                return

            cliente_ok = dlg1.cliente
            nombre_ref = getattr(dlg1, "nombre_ref", "")

            dlg2 = DialogoClienteExpressPaso2(
                self.total_final, cliente_ok, nombre_ref, terminal
            )
            res2 = qt_exec(dlg2)

            if res2 == QDialog.DialogCode.Accepted:
                self.current_metodo = "Clientes"
                self._fiado_cliente_id = dlg2.cliente_id
                idx = self.cmb_cliente.findData(dlg2.cliente_id)
                if idx >= 0:
                    self.cmb_cliente.setCurrentIndex(idx)
                self.txt_pago.setText(self._monto(self.total_final))
                self._fiado_flujo_activo = False
                QTimer.singleShot(80, lambda: self.finalizar(imprimir=False))
                return

            if getattr(dlg2, "reintentar_dni", False):
                continue

            self._fiado_flujo_activo = False
            self._fiado_cliente_id = None
            self.set_metodo(rev)
            return

    def _activar_fiado_express(self):
        """Clic en tarjeta Fiado → resalta y abre Fiado Express."""
        rev = self.current_metodo if self.current_metodo != "Fiado" else "Efectivo"
        self.set_metodo("Fiado")
        self._abrir_fiado_express_original(rev)

    def _abrir_fiado_express(self, revertir_a="Efectivo"):
        """Abre el flujo de Fiado Express."""
        return self._abrir_fiado_express_original(revertir_a)

    def _abrir_fiado_express_original(self, revertir_a="Efectivo"):
        """Fiado Express original."""
        from PyQt6.QtWidgets import QDialog
        from src.cajero.paso6_cobro.widgets.fiado_express import (
            DialogoFiadoExpressPaso1,
            DialogoFiadoExpressConfirmacion,
        )

        rev = revertir_a if revertir_a != "Fiado" else getattr(self, "_revertir_tras_fiado", "Efectivo")
        terminal = self.parent()
        self._fiado_flujo_activo = True

        cliente_ok = None
        dni_ref = ""

        while True:
            dlg1 = DialogoFiadoExpressPaso1(self.total_final, self)
            if qt_exec(dlg1) != QDialog.DialogCode.Accepted:
                self._fiado_flujo_activo = False
                self._fiado_cliente_id = None
                self.set_metodo(rev)
                return

            cliente_ok = dlg1.cliente
            dni_ref = dlg1.dni_ref

            dlg2 = DialogoFiadoExpressConfirmacion(
                self.total_final, cliente_ok, dni_ref, terminal
            )
            res2 = qt_exec(dlg2)

            if res2 == QDialog.DialogCode.Accepted:
                self.current_metodo = "Fiado"
                self._fiado_cliente_id = dlg2.cliente_id
                idx = self.cmb_cliente.findData(dlg2.cliente_id)
                if idx >= 0:
                    self.cmb_cliente.setCurrentIndex(idx)
                self.txt_pago.setText(self._monto(self.total_final))
                self._fiado_flujo_activo = False
                QTimer.singleShot(80, lambda: self.finalizar(imprimir=False))
                return

            if getattr(dlg2, "reintentar_dni", False):
                continue

            self._fiado_flujo_activo = False
            self._fiado_cliente_id = None
            self.set_metodo(rev)
            return

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

            # Zoom logic
            self.mp_font_size += self.mp_font_dir
            if self.mp_font_size >= 24:
                self.mp_font_dir = -1
            elif self.mp_font_size <= 20:
                self.mp_font_dir = 1

            self.lbl_mp_status.setStyleSheet(f"font-size: {self.mp_font_size}px; font-weight: 900;")
            self.lbl_mp_status.setText(f" {char} ESCUCHANDO MERCADO PAGO EN TIEMPO REAL... (${self.total_final:.2f})")
        except Exception as e:
            pass

    def verificar_pago_mp_automatico(self):
        try:
            import time
            from src.admin.admin10_mp import Admin10MP
            if hasattr(Admin10MP, 'ultimo_pago_detectado') and Admin10MP.ultimo_pago_detectado is not None:
                pago = Admin10MP.ultimo_pago_detectado
                ahora = time.time()

                # Validar que el pago haya ocurrido hace menos de 90 segundos
                if ahora - pago['timestamp'] <= 90:
                    # Validar que el monto coincida exactamente con self.total_final (permitiendo un margen de 0.05)
                    monto_pago = pago['monto']
                    if abs(monto_pago - self.total_final) <= 0.05:
                        # Consumir el pago para evitar duplicados
                        Admin10MP.ultimo_pago_detectado = None

                        self.timer_mp.stop()
                        self.timer_spinner.stop()

                        self.lbl_mp_status.setStyleSheet("font-size: 20px; font-weight: 900;")

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

                        # Esperar 1.5 segundos para la animación y finalizar con ticket
                        QTimer.singleShot(1500, lambda: self.finalizar(imprimir=True))
        except Exception as e:
            print(f"Error verificando auto-pago MP: {e}")

    def _validar_pago(self):
        """ Centraliza la validación para evitar redundancias y errores de arqueo. """
        p1_t = self.txt_pago.text().replace('$', '').replace(',', '').strip()
        p2_t = self.txt_otro.text().replace('$', '').replace(',', '').strip()

        if not p1_t:
            if self.current_metodo in ("Tarjeta", "Transferencia", "QR"):
                self.txt_pago.setText(self._monto(self.total_final))
                p1_t = f"{self.total_final:.2f}"
            else:
                self.aviso_monto.show()
                self.txt_pago.setStyleSheet(
                    "font-size: 40px; font-weight: 900; border-radius: 12px; "
                    "border: 3px solid #F59E0B; color: #0F172A; background: #FFFBEB;"
                )
                self.txt_pago.setFocus()
                return None
        else:
            self.aviso_monto.hide()

        if self.current_metodo in ("Fiado", "Clientes"):
            from src.repositories.cliente_repository import ClienteRepository

            cliente_id = getattr(self, "_fiado_cliente_id", None) or self.cmb_cliente.currentData()
            if not cliente_id:
                if not getattr(self, "_fiado_flujo_activo", False):
                    self._abrir_fiado_express(getattr(self, "_revertir_tras_fiado", "Efectivo"))
                else:
                    QMessageBox.warning(self, "Clientes", "No se seleccionó cliente.")
                return None
            c = ClienteRepository.obtener_por_id(cliente_id)
            if not c:
                QMessageBox.warning(self, "Clientes", "Cliente no encontrado.")
                return None
            disp = ClienteRepository.credito_disponible(c)
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
                QMessageBox.critical(self, "ERROR", "Monto inválido ingresado.")
            else:
                # Si falta dinero y no es mixto, ofrecer pasarse a Mixto
                if self.current_metodo != "Mixto":
                    try:
                        p1_val = float(p1_t) if p1_t else 0.0
                    except ValueError:
                        p1_val = 0.0
                    self.set_metodo("Mixto")
                    faltante = self.total_final - p1_val
                    self.txt_otro.setText(f"{faltante:.2f}")
                    self.txt_otro.setFocus()
                    self.txt_otro.selectAll()
                else:
                    QMessageBox.critical(self, "MONTO INSUFICIENTE", "Falta dinero para cubrir el total.")
            return None

        return (p1, p2)

    def intentar_finalizar(self):
        if self.current_metodo in ("Fiado", "Clientes"):
            if getattr(self, "_fiado_flujo_activo", False):
                return
            if getattr(self, "_fiado_cliente_id", None):
                self.finalizar(imprimir=False)
            else:
                self._abrir_fiado_express(getattr(self, "_revertir_tras_fiado", "Efectivo"))
            return
        if self.current_metodo == "QR" and self._tpv_qr_listo():
            self._procesar_cobro_qr_pantalla(
                config.get("mp_access_token", ""), self.total_final
            )
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

        # El total de arriba sigue mostrando el original fijo
        self.lbl_total.setText(self._monto(self.total_original))

        # El neto destacado de abajo se actualiza en caliente
        self.lbl_neto.setText(f"NETO A PAGAR: ${self.total_final:,.2f}")

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
        if self.current_metodo in ["Tarjeta", "Transferencia"]:
            self.txt_pago.setText(self._monto(self.total_final))

        self.calcular_vuelto()

    def on_descuento_changed(self, text):
        try:
            txt = text.strip()
            if not txt:
                self.descuento_monto = 0.0
            elif txt.endswith('%'):
                val = float(txt[:-1])
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
            elif txt.endswith('%'):
                val = float(txt[:-1])
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

    def finalizar_fiscal_efectivo(self):
        self.set_metodo("Efectivo")
        self.finalizar(True, force_fiscal=True)

    def finalizar(self, imprimir=True, force_fiscal=False):
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
                "request_id": getattr(self, "request_id", None)
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

        if watched in [self.txt_pago, self.txt_otro, self.txt_desc, self.txt_rec] and event.type() == QEvent.Type.KeyPress:
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
                self.procesar_pago_mercadopago_point()
                return True
            elif k == Qt.Key.Key_F12:
                self.verificar_transferencia_mp()
                return True
            elif k == Qt.Key.Key_F1:
                self.finalizar(True)
                return True

        return super().eventFilter(watched, event)



    def _tpv_point_listo(self):
        config._load_config()
        token = str(config.get("mp_access_token", "") or "").strip()
        device = str(config.get("mp_device_id", "") or "").strip()
        return bool(token and device)

    def _tpv_qr_listo(self):
        config._load_config()
        token = str(config.get("mp_access_token", "") or "").strip()
        user = str(config.get("mp_user_id", "") or "").strip()
        pos = str(config.get("mp_external_pos_id", "") or "").strip()
        return bool(token and user and pos)

    def _pintar_luz_tpv(self):
        listo = self._tpv_point_listo() or self._tpv_qr_listo()
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

    def procesar_pago_mercadopago_point(self):
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0: return
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

        if k == Qt.Key.Key_F1: self.finalizar(True)
        elif k == Qt.Key.Key_F2: self.finalizar(False)
        elif k == Qt.Key.Key_F3: self.abrir_descuento()
        elif k == Qt.Key.Key_F4: self.abrir_recargo()
        elif k == Qt.Key.Key_F10: self.finalizar_fiscal_efectivo()
        elif k == Qt.Key.Key_F11: self.procesar_pago_mercadopago_point()
        elif k == Qt.Key.Key_F12: self.verificar_transferencia_mp()
        elif k == Qt.Key.Key_Escape: self.reject()
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            foco = self.focusWidget()
            if self.current_metodo in ("Fiado", "Clientes"):
                if getattr(self, "_fiado_flujo_activo", False):
                    return
                if getattr(self, "_fiado_cliente_id", None):
                    self.finalizar(imprimir=False)
                else:
                    self._abrir_fiado_express(getattr(self, "_revertir_tras_fiado", "Efectivo"))
                return
            if isinstance(foco, QPushButton) and foco in self.btns.values():
                # 1. ENTER ELIGE MÉTODO -> Salta al casillero de monto
                self.txt_pago.setFocus()
                self.txt_pago.selectAll()
            else:
                # 2 y 3. ENTER CONFIRMA Y CIERRA (Sin Ticket)
                self.intentar_finalizar()
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
        if not focused or not isinstance(focused, QLineEdit):
            focused = self.txt_pago

        if key == "⌫":
            event_press = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.NoModifier, "")
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.Type.KeyRelease, Qt.Key.Key_Backspace, Qt.NoModifier, "")
            QApplication.sendEvent(focused, event_release)
        elif key == "ENTER":
            event_press = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.NoModifier, "\n")
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.Type.KeyRelease, Qt.Key.Key_Return, Qt.NoModifier, "\n")
            QApplication.sendEvent(focused, event_release)
        elif key in ("ESC", "Salir"):
            self.reject()
        else:
            teclado_key_map = {
                '0': Qt.Key.Key_0, '1': Qt.Key.Key_1, '2': Qt.Key.Key_2, '3': Qt.Key.Key_3, '4': Qt.Key.Key_4,
                '5': Qt.Key.Key_5, '6': Qt.Key.Key_6, '7': Qt.Key.Key_7, '8': Qt.Key.Key_8, '9': Qt.Key.Key_9,
                ',': Qt.Key.Key_Comma
            }
            key_code = teclado_key_map.get(key, Qt.Key.Key_unknown)
            event_press = QKeyEvent(QEvent.Type.KeyPress, key_code, Qt.NoModifier, key)
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.Type.KeyRelease, key_code, Qt.NoModifier, key)
            QApplication.sendEvent(focused, event_release)
