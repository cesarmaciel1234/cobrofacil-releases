from src.utils.qt_compat import qt_exec
import os, sys, threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import src.utils.qt_compat  # noqa: F401 — enums Qt6 (Qt + widgets)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QListWidget, QListWidgetItem, QDialog, QPushButton, QGridLayout,
    QComboBox, QDoubleSpinBox, QMessageBox, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QDate, QTime, QObject, pyqtSignal, QRect, QEvent
from PyQt6.QtGui import QColor, QFont, QPen, QPainter
from datetime import datetime
import time
import logging
logger = logging.getLogger(__name__)

from src.cajero.paso8_historial import DialogoHistorialDia, fmt_moneda
from src.config import config
from src.cajero.paso5_terminal.componentes_paso5_terminal.componente_tabla_de_productos.suprimir_articulo import suprimir_articulo
from src.cajero.paso5_terminal.dialogos.dialogo_editar_cantidad import DialogoEditarCantidad
from src.cajero.paso5_terminal.dialogos.pin.dialogo_pin import DialogoPIN
from src.cajero.sacar_efectivo import DialogoRetiroEfectivo
from src.cajero.ingresar_efectivo import DialogoIngresoEfectivo
from src.cajero.paso5_terminal.dialogos.candado.dialogo_candado import DialogoCandado
from src.cajero.paso5_terminal.logica.terminal_controller import TerminalController

from src.hardware.cash_drawer import drawer_manager
try:
    import winsound
    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False

try:
    from src.cajero.paso5_terminal.componentes_paso5_terminal.componentes_barra_inferior.teclado_virtual.virtual_keyboard_paso5 import VirtualKeyboardPaso5 as VirtualKeyboard
    HAS_KEYBOARD = True
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Modulo de teclado virtual no disponible: {e}")
    HAS_KEYBOARD = False

# --- Componentes Visuales Modularizados ---
from src.cajero.paso5_terminal.componentes_paso5_terminal.cabecera_superior import CabeceraSuperior
from src.cajero.paso5_terminal.componentes_paso5_terminal.centro_de_notificaciones import CentroDeNotificaciones
from src.cajero.paso5_terminal.componentes_paso5_terminal.componente_tabla_de_productos.tabla_de_productos import TablaDeProductos
from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales import PanelDeTotales
from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior import BarraDeHerramientasInferior
from src.cajero.paso5_terminal.componentes_paso5_terminal.componente_tabla_de_productos.nav_row_border_overlay import NavRowBorderOverlay

def fmt_moneda_sin_centavos(val):
    try:
        return f"${float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "$0,00"

def parse_float_safe(val_str):
    try:
        val_str = str(val_str).replace("$", "").strip()
        # Si tiene formato europeo/argentino con coma decimal: 1.234,56
        if "," in val_str:
            # Quitamos los puntos de miles y cambiamos la coma por punto
            val_str = val_str.replace(".", "").replace(",", ".")
        # Si no tiene coma, asumimos que el punto ya es el decimal (formato inglés: 1234.56)
        return float(val_str)
    except Exception:
        return 0.0
SCAN_ROW_BG = "#EFF6FF"
NAV_ROW_BORDER = "#F59E0B"



# ──────────────────────────────────────────────────────────────
# ESTADO GLOBAL DEL CAJERO ACTIVO (módulo compartido)
# ──────────────────────────────────────────────────────────────
from src.cajero.cajero_activo import CajeroActivo
















class Paso5Terminal(QWidget):
    request_admin_jump = pyqtSignal()
    request_chatbot_toggle = pyqtSignal()
    bascula_leida = pyqtSignal(object)
    """
    PASO 5: TERMINAL INDUSTRIAL EXACTA (100% Foto + Búsqueda Rápida)
    """
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.controller = TerminalController(self)
        self.txt_scan = None
        self.setup_ui()
        self.apply_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_reloj)
        self.timer.start(1000)

        # Timer para evitar que el buscador se trabe al leer códigos rápido
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_busqueda)

        # Timer de alta velocidad (150ms) para auto-foco instantáneo en el escáner (haga click donde haga, vuelve al instante)
        self.autofocus_timer = QTimer(self)
        self.autofocus_timer.timeout.connect(self.asegurar_foco_escaner)
        self.autofocus_timer.start(150)
        self._foco_lejos_ms = 0

        # Timer de stock crítico (cada 5 minutos)
        if config.get("stock_alerta_activa", True):
            self.stock_timer = QTimer(self)
            self.stock_timer.timeout.connect(self.verificar_stock_minimo)
            self.stock_timer.start(300000) # 300,000 ms = 5 mins
            QTimer.singleShot(2000, self.verificar_stock_minimo)

        # Timer de autocierre (cada 60 segundos)
        if config.get("cierre_auto_activo", False):
            self.autoclose_timer = QTimer(self)
            self.autoclose_timer.timeout.connect(self.verificar_autocierre)
            self.autoclose_timer.start(60000) # 60,000 ms = 1 min
        # Monitor de Seguridad: Delegado al Motor Global en MainWindow
        pass

        # El chatbot animado ahora se inicializa en segundo plano desde main.py
        # para que esté listo de forma instantánea al presionar el botón
        self.chatbot_process = None

        self.tickets_espera = []
        self.cliente_id = None
        self.cliente_nombre = "Consumidor Final"
        self.descuento_general = 0.0
        self.timer_alerta_espera = QTimer(self)
        self.timer_alerta_espera.timeout.connect(self._alerta_tickets_espera)
        self.timer_alerta_espera.start(120000)
        self.bascula_leida.connect(self._aplicar_lectura_bascula)
        if HAS_KEYBOARD:
            QTimer.singleShot(0, self._enganchar_foco_teclado)

    def _stock_disponible(self, p, p_id):
        if p_id == "000":
            return None
        try:
            if hasattr(p, "keys") and "stock" in p.keys():
                return float(p["stock"] or 0)
            if isinstance(p, dict) and "stock" in p:
                return float(p["stock"] or 0)
        except (TypeError, ValueError):
            pass
        return self.controller.stock_ofertas.obtener_stock_db(p_id)

    def _fmt_stock_mostrar(self, p, stk):
        from src.motor_inventario.unidad_medida import formatear_stock

        return formatear_stock(p, stk)

    def _validar_stock(self, p, p_id, cantidad_necesaria):
        from PyQt6.QtWidgets import QMessageBox
        from src.motor_inventario.unidad_medida import (
            alcanza_stock,
            permitir_cobro_sin_stock,
        )

        permitir = permitir_cobro_sin_stock()
        disp = self._stock_disponible(p, p_id)
        if alcanza_stock(disp, cantidad_necesaria, permitir):
            return True
        nombre = ""
        try:
            nombre = str(p["nombre"] or "").strip()
        except Exception:
            nombre = str(p_id)
        QMessageBox.warning(
            self,
            "Sin stock",
            f"No hay stock suficiente de {nombre or p_id}. Disponible: {disp:g}.",
        )
        return False



    def _refresh_urgencia_stock_banner(self):
        self._refrescar_notificaciones()

    def _refrescar_notificaciones(self):
        try:
            if hasattr(self, "notificador"):
                self.notificador.refrescar()
        except Exception:
            pass

    def refresh_terminal_title(self):
        title = config.get('business_name', 'Punto de Venta [20.09.02]')
        self.lbl_terminal_title.setText(title)
        self._orig_title = title

    def refresh_status_bar(self):
        import socket, uuid
        from src.utils.paths import get_base_path
        base_path = get_base_path().lower()
        db_path = self.controller.get_db_path()

        # Determinar si la base de datos es local (Maestra) o remota (Cliente)
        is_local = base_path in db_path or not db_path or db_path == "punpro.db"
        self.lbl_estado.setText("Maestra" if is_local else "Cliente")

        # Generar código de instalación único a partir de la dirección MAC
        mac_str = f"{uuid.getnode():012X}"
        formatted_mac = f"№ {mac_str[:4]}-{mac_str[4:8]}-{mac_str[8:]}"
        self.lbl_instalacion.setText(formatted_mac)

        # Iniciar latido de red y conteo dinámico si no existe el timer
        if not hasattr(self, 'red_timer'):
            self.red_timer = QTimer(self)
            self.red_timer.timeout.connect(self.actualizar_red_heartbeat)
            self.red_timer.start(15000) # Latido cada 15 segundos
            # Ejecutar una vez al inicio
            QTimer.singleShot(500, self.actualizar_red_heartbeat)

        from src.cajero.cajero_activo import CajeroActivo
        self._pintar_perfil_cajero()

    def actualizar_red_heartbeat(self):
        try:
            import socket
            caja_id = config.get("caja_id", 1)
            hostname = socket.gethostname().upper()

            # Registrar presencia de este terminal
            self.controller.registrar_heartbeat(caja_id, hostname)
            self.lbl_caja_num.setText(f"{caja_id:02d}   ·   {hostname}")

            # Efecto Destello (Flash LED Blanco a Verde estilo router)
            self.led_status.setProperty("estado", "parpadeo"); self.led_status.style().unpolish(self.led_status); self.led_status.style().polish(self.led_status)
            QTimer.singleShot(400, lambda: (self.led_status.setProperty("estado", "normal"), self.led_status.style().unpolish(self.led_status), self.led_status.style().polish(self.led_status)))
        except Exception:
            # Si falla la conexión a la base de datos o red, poner LED en rojo
            self.led_status.setProperty("estado", "alerta"); self.led_status.style().unpolish(self.led_status); self.led_status.style().polish(self.led_status)
            try:
                caja_id = config.get("caja_id", 1)
                hostname = socket.gethostname().upper()
                self.lbl_caja_num.setText(f"{caja_id:02d}   ·   {hostname}")
            except Exception:
                self.lbl_caja_num.setText("Caja")

    def verificar_stock_minimo(self):
        self._refrescar_notificaciones()

    def verificar_autocierre(self):
        try:
            hora_target = config.get("cierre_auto_hora", "00:00")
            hora_actual = datetime.now().strftime("%H:%M")

            # Solo intentamos ejecutar si coincide el minuto exacto
            if hora_actual == hora_target:
                from src.services.caja_service import verificar_y_realizar_autocierre
                hizo_cierre, monto = verificar_y_realizar_autocierre()
                if hizo_cierre:
                    logger.info(f"Cierre automático ejecutado exitosamente a las {hora_actual}.")
                    self._agregar_al_ticket("> [SISTEMA] CIERRE AUTOMÁTICO EFECTUADO.", 0, 0, color="#10B981")
        except Exception as e:
            logger.error(f"Autoclose error: {e}")

    def refresh_terminal_data(self):
        """
        REFRESCO TOTAL (F11 Back): Actualiza precios de la tabla, ofertas y config.
        Evita que el cajero use precios viejos tras una intervención de supervisor.
        """
        logger.info("Refrescando datos del terminal post-intervención...")
        # 1. Recargar Configuración (Por si cambiaron balanza, impresora, etc.)
        from src.config import config as _c
        _c._load_config()

        # Recargar título y barra de estado dinámicamente
        self.refresh_terminal_title()
        self.refresh_status_bar()
        self._refresh_urgencia_stock_banner()

        # 2. Actualizar ítems en la tabla
        for i in range(self.tabla.rowCount()):
            p_id = self.tabla.item(i, 0).text()
            p = self.controller.stock_ofertas.obtener_producto_para_refresh(p_id)
            if p:
                p_base = float(p['precio'])
                cant = float(self.tabla.item(i, 3).text())
                c_of = float(p['cant_oferta'] or 0)
                p_of = float(p['precio_oferta'] or 0)
                c_may = float(p['cant_mayoreo'] or 0)
                p_may = float(p['precio_mayoreo'] or 0)

                if c_may > 0 and p_may > 0 and cant >= c_may:
                    p_final = p_may
                    desc = (p_base - p_may) * cant
                    nombre = f"📦 [MAYOREO] {p['nombre']}"
                elif c_of > 0 and p_of > 0 and cant >= c_of:
                    p_final = p_of
                    desc = (p_base - p_of) * cant
                    nombre = f"🔥 [OFERTA] {p['nombre']}"
                else:
                    p_final = p_base
                    desc = 0.0
                    nombre = p['nombre']

                self.tabla.item(i, 1).setText(nombre)
                self.tabla.item(i, 2).setText(fmt_moneda_sin_centavos(p_final))
                self.tabla.item(i, 4).setText(fmt_moneda_sin_centavos(desc))
                self.tabla.item(i, 5).setText(fmt_moneda_sin_centavos(cant * p_final))
                self._reaplicar_estilo_fila(i)

        self.actualizar_totales()
        if hasattr(self, 'txt_scan') and self.txt_scan:
            self.txt_scan.setFocus()

    def monitor_permanente_seguridad(self):
        """ Deprecado en favor de drawer_manager.check_status """
        pass

    def monitor_cajon_bloqueante(self, manual=False):
        """ Deprecado en favor de drawer_manager reactivo """
        pass

    def mostrar_alerta_perimetral(self, visible, modo="security"):
        """El cajón no pinta la barra. El punto rojo lo pone el notificador."""
        parent = self.window()
        if parent is not self and hasattr(parent, "mostrar_alerta_perimetral"):
            parent.mostrar_alerta_perimetral(visible, modo=modo)

    def setup_ui(self):
        self.setObjectName("TerminalMain")
        # Layout principal con márgenes suaves
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        # 1. Cabecera Superior
        title = config.get('business_name', 'Punto de Venta [20.09.02]')
        self.cabecera = CabeceraSuperior(titulo_inicial=title)
        self.main_layout.addWidget(self.cabecera)

        # Mapeo de variables anteriores a la cabecera (compatibilidad con lógica actual)
        self.header_frame = self.cabecera
        self.lbl_estado = self.cabecera.etiqueta_estado
        self.lbl_instalacion = self.cabecera.etiqueta_instalacion
        self.led_status = self.cabecera.luz_indicadora
        self.lbl_caja_num = self.cabecera.etiqueta_caja
        self.lbl_fecha = self.cabecera.etiqueta_fecha
        self.lbl_terminal_title = self.cabecera.etiqueta_titulo
        self._orig_title = title

        # 2. Centro de Notificaciones (Reemplaza banner y alertas de stock)
        self.notificador = CentroDeNotificaciones(zona_iconos=self.cabecera.zona_alertas)
        self.main_layout.addWidget(self.notificador)
        self._refrescar_notificaciones()

        # Inicializar datos en la barra y cabecera
        self.refresh_status_bar()

        # 3. Tabla de Productos (Centro)
        self.componente_tabla = TablaDeProductos()
        self.tabla = self.componente_tabla.get_tabla()

        self.central_frame = QFrame()
        self.central_frame.setObjectName("TerminalCentralFrame")
        central_layout = QVBoxLayout(self.central_frame)
        central_layout.setContentsMargins(0,0,0,0)
        central_layout.addWidget(self.componente_tabla)
        self.main_layout.addWidget(self.central_frame, 2)

        # Binding industrial para la tabla
        self.tabla.installEventFilter(self)
        self._nav_border_overlay = NavRowBorderOverlay(self.tabla)
        self.tabla.viewport().installEventFilter(self)
        self.tabla.verticalScrollBar().valueChanged.connect(lambda *_: self._sync_nav_border_overlay())
        self.tabla.horizontalScrollBar().valueChanged.connect(lambda *_: self._sync_nav_border_overlay())
        self.tabla.currentCellChanged.connect(self._on_tabla_nav_changed)
        self.tabla.itemSelectionChanged.connect(self._on_tabla_nav_row_only)
        self._nav_prev_row = -1

        # 4. Panel de Totales (Bottom Dashboard)
        self.panel_totales = PanelDeTotales()
        self.main_layout.addWidget(self.panel_totales)

        # Mapeo del panel de totales
        self.dashboard_frame = self.panel_totales # Para alertas perimetrales
        self.txt_scan = self.panel_totales.entrada_codigo
        self.txt_scan.textChanged.connect(self.actualizar_busqueda)
        self.txt_scan.returnPressed.connect(self.procesar_scan)

        # --- Overlay de Resultados de Búsqueda (Flotante, plano) ---
        self.panel_busqueda = QFrame(self)
        self.panel_busqueda.setObjectName("TerminalBusquedaPanel")
        self.panel_busqueda.hide()
        self.panel_busqueda.setGraphicsEffect(None)
        self.panel_busqueda.setStyleSheet(
            "QFrame#TerminalBusquedaPanel { background: #FFFFFF; border: 1px solid #2563EB; }"
        )
        bus_lay = QVBoxLayout(self.panel_busqueda)
        bus_lay.setContentsMargins(0, 0, 0, 0)
        bus_lay.setSpacing(0)

        cab = QWidget()
        cab.setFixedHeight(48)
        cab.setStyleSheet("background: #F1F5F9; border: none; border-bottom: 1px solid #E2E8F0;")
        cab_l = QHBoxLayout(cab)
        cab_l.setContentsMargins(28, 0, 28, 0)
        cab_l.setSpacing(28)
        _hstyle = "font-size: 14px; font-weight: 800; color: #64748B; background: transparent; letter-spacing: 0.8px;"
        h_nom = QLabel("PRODUCTO")
        h_nom.setStyleSheet(_hstyle)
        h_pre = QLabel("PRECIO")
        h_pre.setFixedWidth(180)
        h_pre.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        h_pre.setStyleSheet(_hstyle)
        h_stk = QLabel("STOCK")
        h_stk.setFixedWidth(170)
        h_stk.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        h_stk.setStyleSheet(_hstyle)
        cab_l.addWidget(h_nom, 1)
        cab_l.addWidget(h_pre)
        cab_l.addWidget(h_stk)
        bus_lay.addWidget(cab)

        self.list_results = QListWidget()
        self.list_results.setObjectName("TerminalListResults")
        self.list_results.itemClicked.connect(self.seleccionar_item_busqueda)
        self.list_results.installEventFilter(self)
        self.list_results.setGraphicsEffect(None)
        self.list_results.setUniformItemSizes(True)
        self.list_results.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        self.list_results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._search_sel_row = -1
        self.list_results.setAlternatingRowColors(False)
        self.list_results.itemSelectionChanged.connect(self._update_search_colors)
        self.list_results.setSpacing(0)
        self.list_results.setStyleSheet("""
            QListWidget#TerminalListResults {
                border: none;
                background-color: #FFFFFF;
                color: #0F172A;
                outline: none;
            }
            QListWidget#TerminalListResults::item {
                padding: 0px;
                border: none;
                border-bottom: 1px solid #F1F5F9;
                min-height: 72px;
            }
            QListWidget#TerminalListResults::item:selected {
                background-color: #2563EB;
                color: #FFFFFF;
            }
        """)
        bus_lay.addWidget(self.list_results, 1)

        self.lbl_busqueda_pie = QLabel("Enter agregar   ·   Esc cerrar")
        self.lbl_busqueda_pie.setFixedHeight(36)
        self.lbl_busqueda_pie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_busqueda_pie.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #64748B; background: #F8FAFC; "
            "border: none; border-top: 1px solid #E2E8F0;"
        )
        bus_lay.addWidget(self.lbl_busqueda_pie)

        # Mapeo de etiquetas numéricas
        self.lbl_cant_val = self.panel_totales.valor_cant
        self.lbl_total_val = self.panel_totales.etiqueta_total_grande
        self.lbl_ahorro_val = self.panel_totales.etiqueta_ahorro
        self.lbl_side_cant_t = self.panel_totales.titulo_cant
        self.lbl_side_cant = self.panel_totales.valor_cant
        self.lbl_side_total_t = self.panel_totales.titulo_total
        self.lbl_side_total = self.panel_totales.valor_total
        self.lbl_side_ahorro_t = self.panel_totales.titulo_ahorro
        self.lbl_side_ahorro = self.panel_totales.valor_ahorro
        self.lbl_side_pagos_t = self.panel_totales.titulo_pagos
        self.lbl_side_pagos = self.panel_totales.valor_pagos
        self.lbl_side_cambio_t = self.panel_totales.titulo_cambio
        self.lbl_side_cambio = self.panel_totales.valor_cambio

        self.en_venta = False

        # 5. Barra de Herramientas Inferior
        from src.updater.github_updater import get_local_version
        v_local = get_local_version()
        self.barra_herramientas = BarraDeHerramientasInferior(mostrar_teclado=HAS_KEYBOARD, version_sistema=f"COBRO FACIL {v_local}")
        self.main_layout.addWidget(self.barra_herramientas)

        # Conectar señales a funciones existentes
        self.barra_herramientas.teclado_presionado.connect(self.toggle_keyboard)
        self.barra_herramientas.tema_presionado.connect(self.toggle_theme)
        self.barra_herramientas.espera_presionado.connect(self._swap_ticket_espera)
        self.barra_herramientas.bloquear_presionado.connect(self.bloquear_terminal)
        self.barra_herramientas.chatbot_presionado.connect(self.toggle_chatbot)

        # Enrutador de teclas F
        def enrutar_f(tecla_str):
            if tecla_str == "F1": self._do_busqueda()
            elif tecla_str == "F3": self.abrir_historial_dia()
            elif tecla_str == "F12": self.finalizar_venta()
            elif tecla_str == "F5": self.abrir_retiro_efectivo()
            elif tecla_str == "F6": self.abrir_ingreso_efectivo()
            elif tecla_str == "F7": self._leer_bascula()
            elif tecla_str == "F8": self._swap_ticket_espera()
            elif tecla_str == "F4": self.abrir_cierre_caja()
            elif tecla_str == "F11": self.llamar_supervisor()

        self.barra_herramientas.tecla_f_presionada.connect(enrutar_f)

        # Mapeo de botones de la barra inferior
        self.status_bar = self.barra_herramientas
        self.btn_teclado = getattr(self.barra_herramientas, 'boton_teclado', None)
        self.btn_theme = self.barra_herramientas.boton_tema
        self.lbl_version = self.barra_herramientas.etiqueta_version
        self.btn_espera = self.barra_herramientas.boton_espera
        self._shortcuts_scroll = self.barra_herramientas.scroll_atajos
        self.shortcut_buttons = (
            self._shortcuts_scroll.botones_f if self._shortcuts_scroll is not None else {}
        )
        self.btn_candado = self.barra_herramientas.boton_bloquear
        self.btn_chatbot = self.barra_herramientas.boton_chatbot

        QTimer.singleShot(0, self._apply_screen_layout)
        self.txt_scan.setFocus()
        QTimer.singleShot(500, self.txt_scan.setFocus) # Asegurar foco inicial
        QTimer.singleShot(1200, self._precalentar_cobro)
        self.txt_scan.installEventFilter(self) # Para monitoreo PRO

    def _precalentar_cobro(self):
        """Carga el cobro en segundo plano. En un ejecutable el primer import es el que espera."""
        try:
            from src.cajero.paso6_cobro import Paso6Cobro  # noqa: F401
        except Exception:
            pass

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key.Key_F1: self._do_busqueda()
        elif k == Qt.Key.Key_F3: self.abrir_historial_dia()
        elif k == Qt.Key.Key_F12: self.finalizar_venta()
        elif k == Qt.Key.Key_F5: self.abrir_retiro_efectivo()
        elif k == Qt.Key.Key_F6: self.abrir_ingreso_efectivo()
        elif k == Qt.Key.Key_F7: self._leer_bascula()
        elif k == Qt.Key.Key_F8: self._swap_ticket_espera()
        elif k == Qt.Key.Key_F4: self.abrir_cierre_caja()
        elif k == Qt.Key.Key_F11: self.llamar_supervisor()
        elif k == Qt.Key.Key_Escape:
            if getattr(self, 'list_results', None) is not None and not self.list_results.isHidden():
                self._ocultar_busqueda()
            self.txt_scan.setFocus()

    def toggle_chatbot(self):
        self.request_chatbot_toggle.emit()
        self.txt_scan.setFocus()

    def llamar_supervisor(self):
        main_win = self.window()
        if main_win and hasattr(main_win, 'handle_f11_global'):
            main_win.handle_f11_global()

    def paintEvent(self, event):
        from PyQt6.QtWidgets import QStyle, QStyleOption
        from PyQt6.QtGui import QPainter
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

    def hideEvent(self, event):
        super().hideEvent(event)
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(b"HIDE", ("127.0.0.1", 45680))
            sock.close()
        except Exception:
            pass

    def _enganchar_foco_teclado(self):
        if getattr(self, "_foco_teclado_enganchado", False) or not HAS_KEYBOARD:
            return
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            return
        app.focusChanged.connect(self.on_focus_changed)
        self._enganchar_motivo_foco(app)
        self._foco_teclado_enganchado = True

    def _enganchar_motivo_foco(self, app):
        if getattr(self, "_filtro_motivo_foco", None) is not None:
            return
        from PyQt6.QtCore import QObject, QEvent

        terminal = self

        class _MotivoFoco(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.FocusIn:
                    terminal._motivo_foco = event.reason()
                return False

        self._filtro_motivo_foco = _MotivoFoco(self)
        app.installEventFilter(self._filtro_motivo_foco)

    def _pantalla_tactil(self):
        if getattr(self, "_es_tactil", None) is not None:
            return self._es_tactil
        tactil = False
        try:
            import sys
            if sys.platform == "win32":
                import ctypes
                user32 = ctypes.windll.user32
                digito = int(user32.GetSystemMetrics(94))
                toques = int(user32.GetSystemMetrics(95))
                tactil = bool(digito & 0x03) or toques > 0
        except Exception:
            tactil = False
        self._es_tactil = tactil
        return tactil

    def _conviene_abrir_teclado(self):
        """El teclado en pantalla se abre al tocar un cuadro. El teclado físico no."""
        from PyQt6.QtCore import Qt
        from src.config import config
        if config.get("teclado_virtual_modo", "tactil") == "nunca":
            return False
        if getattr(self, "_motivo_foco", None) != Qt.FocusReason.MouseFocusReason:
            return False
        return self._pantalla_tactil()

    def _leer_bascula(self):
        """Lee el puerto fuera de la pantalla. El escáner sigue recibiendo teclas."""
        if getattr(self, "_bascula_leyendo", False):
            return
        self._bascula_leyendo = True
        puerto = config.get("puerto_bascula", "COM1")

        def _trabajo():
            import re
            aviso = "falla"
            peso = ""
            detalle = ""
            try:
                import serial
                ser = serial.Serial(puerto, 9600, timeout=0.45)
                try:
                    ser.write(b"P\r\n")
                    respuesta = ser.readline().decode("ascii", errors="ignore").strip()
                finally:
                    ser.close()
                if respuesta:
                    peso_match = re.search(r"([0-9]+\.[0-9]+)", respuesta)
                    if peso_match:
                        aviso = "leido"
                        peso = peso_match.group(1)
                    else:
                        aviso = "raro"
                        detalle = respuesta
                else:
                    aviso = "vacio"
            except ImportError:
                aviso = "sin_pyserial"
            except Exception as e:
                aviso = "falla"
                detalle = str(e)
            self.bascula_leida.emit(
                {"aviso": aviso, "peso": peso, "detalle": detalle, "puerto": puerto}
            )

        threading.Thread(target=_trabajo, daemon=True).start()

    def _aplicar_lectura_bascula(self, dato):
        from PyQt6.QtWidgets import QMessageBox
        self._bascula_leyendo = False
        aviso = (dato or {}).get("aviso")
        puerto = (dato or {}).get("puerto") or "COM1"
        if aviso == "leido":
            peso = dato.get("peso") or ""
            self.txt_scan.setText(f"{peso}*")
            QMessageBox.information(self, "Báscula", f"Peso leído: {peso} kg")
        elif aviso == "raro":
            QMessageBox.warning(self, "Báscula", f"Lectura no reconocida: {dato.get('detalle')}")
        elif aviso == "sin_pyserial":
            QMessageBox.critical(self, "Error", "Falta instalar pyserial (pip install pyserial).")
        elif aviso == "vacio":
            peso_simulado = "1.250"
            self.txt_scan.setText(f"{peso_simulado}*")
            QMessageBox.information(
                self,
                "Báscula (Simulador)",
                f"Báscula no encontrada en {puerto}.\nSe simuló un peso de {peso_simulado} kg para pruebas.",
            )
        else:
            peso_simulado = "0.750"
            self.txt_scan.setText(f"{peso_simulado}*")
            QMessageBox.information(
                self,
                "Báscula (Simulador)",
                "No se detectó báscula física en el puerto configurado.\n"
                f"Se simuló un peso de {peso_simulado} kg para pruebas.\n\n"
                f"Detalle técnico: {dato.get('detalle')}",
            )
        self.txt_scan.setFocus()

    def mousePressEvent(self, event):
        # Al hacer click en cualquier parte, el cursor vuelve al buscador y se oculta la lista
        if getattr(self, 'list_results', None) is not None and not self.list_results.isHidden():
            self._ocultar_busqueda()
        if getattr(self, 'txt_scan', None) is not None:
            self.txt_scan.setFocus()
        super().mousePressEvent(event)

    def toggle_theme(self):
        current = config.get("theme", "light")
        new_theme = "dark" if current == "light" else "light"
        config.set("theme", new_theme)

        # OPTIMIZACION: Pausar el renderizado mientras se inyectan multiples hojas de estilo
        self.setUpdatesEnabled(False)
        try:
            self.apply_theme()
            if HAS_KEYBOARD and hasattr(self, 'teclado_virtual'):
                if hasattr(self.teclado_virtual, 'apply_theme'):
                    self.teclado_virtual.apply_theme()
        finally:
            self.setUpdatesEnabled(True)
            self.repaint()

    def apply_theme(self):
        theme = config.get("theme", "light")
        if hasattr(self, 'barra_herramientas') and hasattr(self.barra_herramientas, 'boton_tema'):
            self.barra_herramientas.boton_tema.setText("TEMAS")

        self.setProperty("theme", theme)

        # Aplicar el tema globalmente
        from src.ui_components.tema_estilos import aplicar_tema
        from PyQt6.QtWidgets import QApplication
        qss_filename = "estilo_dia.qss" if theme == "light" else "estilo_noche.qss"
        aplicar_tema(QApplication.instance(), qss_filename)

        # Asignar objectNames a los componentes principales para el QSS
        if hasattr(self, 'central_frame'): self.central_frame.setObjectName("TerminalCentralFrame")
        if hasattr(self, 'dashboard_frame'): self.dashboard_frame.setObjectName("TerminalDashboard")
        if hasattr(self, 'txt_scan') and self.txt_scan: self.txt_scan.setObjectName("TerminalScan")
        if hasattr(self, 'list_results') and self.list_results: self.list_results.setObjectName("TerminalListResults")
        if hasattr(self, 'lbl_ahorro_val'): self.lbl_ahorro_val.setObjectName("TerminalAhorroVal")
        if hasattr(self, 'lbl_total_val'): self.lbl_total_val.setObjectName("TotalGrande")
        if hasattr(self, 'side_box'): self.side_box.setObjectName("TerminalSideBox")
        if hasattr(self, 'status_bar'): self.status_bar.setObjectName("TerminalStatusBar")
        if getattr(self, "btn_teclado", None): self.btn_teclado.setObjectName("BtnTeclado")
        if getattr(self, "btn_theme", None): self.btn_theme.setObjectName("BtnTheme")
        if hasattr(self, 'icon_lbl'): self.icon_lbl.setObjectName("TerminalIconLbl")
        if hasattr(self, 'tabla'): self.tabla.setObjectName("TerminalTabla")

        if hasattr(self, 'shortcut_buttons'):
            for btn in self.shortcut_buttons:
                btn.setProperty("is_shortcut", True)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        # Refrescar los estilos
        self.style().unpolish(self)
        self.style().polish(self)

        if hasattr(self, 'lbl_side_cant'):
            self.panel_totales.actualizar_estilo_cambio(False)

    def toggle_keyboard(self):
        if not HAS_KEYBOARD:
            return
        active_win = self.window() or self
        if not hasattr(self, 'teclado_virtual'):
            self.teclado_virtual = VirtualKeyboard(active_win)
        elif self.teclado_virtual.parent() != active_win:
            self.teclado_virtual.setParent(active_win)
            self.teclado_virtual.setWindowFlags(
                Qt.Tool |
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.WindowDoesNotAcceptFocus
            )

        if self.teclado_virtual.isVisible():
            self.teclado_virtual.hide()
            self._teclado_abierto_a_mano = False
        else:
            self.teclado_virtual.reposition_keyboard()
            self.teclado_virtual.show()
            self._teclado_abierto_a_mano = True

    def hideEvent(self, event):
        if HAS_KEYBOARD and hasattr(self, 'teclado_virtual'):
            self.teclado_virtual.hide()
        super().hideEvent(event)

    def on_focus_changed(self, old_widget, new_widget):
        if not HAS_KEYBOARD:
            return

        # Sanitizar referencia de teclado virtual si el objeto C++ subyacente fue eliminado
        if hasattr(self, 'teclado_virtual') and self.teclado_virtual is not None:
            try:
                self.teclado_virtual.parent()
            except RuntimeError:
                self.teclado_virtual = None

        # Si la terminal de venta principal no está visible, permitir que el teclado flote
        # globalmente si un QLineEdit tiene foco (para el panel admin).
        pass

        from PyQt6.QtWidgets import QLineEdit, QApplication
        from PyQt6.QtCore import Qt

        # Si el foco entra a una caja de texto (QLineEdit)
        if new_widget and isinstance(new_widget, QLineEdit):
            # 1. Ya no se bloquea en Panel Admin para soportar pantallas táctiles completas
            # 1.b Protección Paso 6 Cobro: el diálogo de cobro tiene el teclado incrustado directamente.
            is_paso6 = False
            parent = new_widget.parent()
            while parent:
                if parent.__class__.__name__ == 'Paso6Cobro':
                    is_paso6 = True
                    break
                parent = parent.parent()
            if is_paso6:
                if getattr(self, 'teclado_virtual', None) is not None:
                    self.teclado_virtual.hide()
                return

            if not self._conviene_abrir_teclado():
                if not getattr(self, "_teclado_abierto_a_mano", False):
                    if getattr(self, 'teclado_virtual', None) is not None and self.teclado_virtual.isVisible():
                        self.teclado_virtual.hide()
                return

            active_win = new_widget.window()
            if not active_win:
                active_win = self.window()

            # 2. Protección Cambio de Ventana: ocultar antes si la ventana de destino cambió
            # Esto previene congelamientos y asegura que la nueva ventana inicie con un teclado limpio
            if getattr(self, 'teclado_virtual', None) is not None and self.teclado_virtual.isVisible():
                if self.teclado_virtual.parent() != active_win:
                    self.teclado_virtual.hide()

            if getattr(self, 'teclado_virtual', None) is None:
                self.teclado_virtual = VirtualKeyboard(active_win)
            elif self.teclado_virtual.parent() != active_win:
                self.teclado_virtual.setParent(active_win)
                self.teclado_virtual.setWindowFlags(
                    Qt.Tool |
                    Qt.FramelessWindowHint |
                    Qt.WindowStaysOnTopHint |
                    Qt.WindowDoesNotAcceptFocus
                )

            # En el buscador principal usamos layout alfabético por defecto (abc)
            self._teclado_abierto_a_mano = False
            self.teclado_virtual.set_layout_mode("abc")
            self.teclado_virtual.reposition_keyboard()
            self.teclado_virtual.show()
        else:
            if new_widget is getattr(self, "btn_teclado", None):
                return
            if getattr(self, 'teclado_virtual', None) is not None and self.teclado_virtual.isVisible():
                self._teclado_abierto_a_mano = False
                self.teclado_virtual.hide()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent

        if getattr(self, 'list_results', None) is not None and obj == self.list_results:
            if event.type() == QEvent.Type.KeyPress:
                self._foco_lejos_ms = 0
                if event.key() == Qt.Key.Key_Up and self.list_results.currentRow() == 0:
                    self.txt_scan.setFocus()
                    return True
                elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self.seleccionar_item_busqueda()
                    return True

        if getattr(self, 'txt_scan', None) is not None and obj == self.txt_scan:
            # INTERCEPTAR TECLAS DE FUNCIÓN: el QLineEdit consume los KeyPress
            # antes de que lleguen al keyPressEvent del widget padre.
            # Los capturamos aquí para garantizar que siempre funcionen.
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                if key == Qt.Key.Key_F4:
                    self.abrir_cierre_caja()
                    return True  # Consumir el evento, no propagarlo
                elif key == Qt.Key.Key_F3:
                    self.abrir_historial_dia()
                    return True
                elif key == Qt.Key.Key_F12:
                    self.finalizar_venta()
                    return True
                elif key == Qt.Key.Key_F1:
                    self.txt_scan.selectAll()
                    return True
                elif key == Qt.Key.Key_F8:
                    self._swap_ticket_espera()
                    return True
                elif key == Qt.Key.Key_F5:
                    self.abrir_retiro_efectivo()
                    return True
                elif key == Qt.Key.Key_F6:
                    self.abrir_ingreso_efectivo()
                    return True
                elif key == Qt.Key.Key_F11:
                    self.llamar_supervisor()
                    return True
                elif key == Qt.Key.Key_Down:
                    if self.list_results.isVisible() and self.list_results.count() > 0:
                        self.list_results.setFocus()
                        self.list_results.setCurrentRow(0)
                        return True
                elif key == Qt.Key.Key_Up:
                    if self.list_results.isVisible() and self.list_results.count() > 0:
                        self.list_results.setFocus()
                        self.list_results.setCurrentRow(self.list_results.count() - 1)
                        return True
                elif key == Qt.Key.Key_Escape:
                    self.txt_scan.clear()
                    self._ocultar_busqueda()
                    return True
                elif key == Qt.Key.Key_Down:
                    if not self.list_results.isHidden() and self.list_results.count() > 0:
                        self.list_results.setFocus()
                        self.list_results.setCurrentRow(0)
                        return True
                    elif self.tabla.rowCount() > 0:
                        self.tabla.setFocus()
                        self.tabla.selectRow(self.tabla.rowCount() - 1)
                        self.tabla.setCurrentCell(self.tabla.rowCount() - 1, 3)
                        QTimer.singleShot(0, self._on_tabla_nav_row_only)
                        return True
                elif key == Qt.Key.Key_Up:
                    if self.tabla.rowCount() > 0:
                        self.tabla.setFocus()
                        self.tabla.selectRow(self.tabla.rowCount() - 1)
                        self.tabla.setCurrentCell(self.tabla.rowCount() - 1, 3)
                        QTimer.singleShot(0, self._on_tabla_nav_row_only)
                        return True
                elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    # Si la lista de resultados está desplegada, procesamos el ítem seleccionado directamente
                    if not self.list_results.isHidden() and self.list_results.currentRow() >= 0:
                        self.seleccionar_item_busqueda()
                        return True
                    # Si el buscador está totalmente vacío, iniciar cobro como alternativa a F4
                    if not self.txt_scan.text().strip():
                        self.finalizar_venta()
                        return True
                    # De lo contrario, no lo consumimos para que siga el flujo natural a procesar_scan o al keyPressEvent del QLineEdit

            # GUARDIA DE FOCO: Si algo intenta quitarle el foco al buscador, lo devolvemos
            elif event.type() == QEvent.Type.FocusOut:
                # CRÍTICO: Si el terminal no está visible (ej: estamos en IA Boss), no forzamos el foco
                if not self.isVisible():
                    return super().eventFilter(obj, event)
                # Solo permitimos perder foco hacia la lista de resultados, la tabla, o campos de texto externos (ej: chatbot)
                if not (self.list_results.hasFocus() or self.tabla.hasFocus()):
                    def restore_focus():
                        from PyQt6.QtWidgets import QApplication, QLineEdit, QTextEdit
                        fw = QApplication.focusWidget()
                        if getattr(self, 'txt_scan', None) is not None:
                            # Si el foco pasó a otro campo de texto (como el chatbot), NO lo robamos
                            if isinstance(fw, (QLineEdit, QTextEdit)) and fw != self.txt_scan:
                                return
                            self.txt_scan.setFocus()
                    QTimer.singleShot(50, restore_focus)

        elif obj == self.tabla:
            if event.type() == QEvent.Type.FocusOut:
                QTimer.singleShot(0, self._sync_nav_border_overlay)
            elif event.type() == QEvent.Type.FocusIn:
                QTimer.singleShot(0, self._sync_nav_border_overlay)
            elif event.type() == QEvent.Type.KeyPress:
                self._foco_lejos_ms = 0
                if event.key() == Qt.Key.Key_F12:
                    self.finalizar_venta()
                    return True
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    row = self.tabla.currentRow()
                    if row != -1:
                        nombre = self.tabla.item(row, 1).text()
                        cant_actual = float(self.tabla.item(row, 3).text())

                        dlg = DialogoEditarCantidad(cant_actual, nombre, self)
                        if qt_exec(dlg):
                            new_cant = dlg.get_value()
                            self.tabla.item(row, 3).setText(
                                f"{new_cant:.2f}" if new_cant % 1 != 0 else f"{int(new_cant)}"
                            )

                            # Verificación dinámica de ofertas al ingresar con el Enter
                            p_id = self.tabla.item(row, 0).text()
                            res_of = [self.controller.stock_ofertas.obtener_ofertas_producto(p_id)] if self.controller.stock_ofertas.obtener_ofertas_producto(p_id) else []
                            if res_of and p_id != "000":
                                p_base = float(res_of[0]['precio'])
                                c_of = float(res_of[0]['cant_oferta'] or 0.0)
                                p_of = float(res_of[0]['precio_oferta'] or 0.0)

                                if c_of > 0 and p_of > 0 and new_cant >= c_of:
                                    p_ap = p_of
                                    desc_t = (p_base - p_of) * new_cant
                                    nombre_txt = self.tabla.item(row, 1).text()
                                    if "🔥 [OFERTA]" not in nombre_txt:
                                        self.tabla.item(row, 1).setText(f"🔥 [OFERTA] {nombre_txt}")
                                else:
                                    p_ap = p_base
                                    desc_t = 0.0
                                    nombre_txt = self.tabla.item(row, 1).text()
                                    if "🔥 [OFERTA]" in nombre_txt:
                                        clean_name = nombre_txt.replace("🔥 [OFERTA] ", "")
                                        self.tabla.item(row, 1).setText(clean_name)

                                self.tabla.item(row, 2).setText(fmt_moneda_sin_centavos(p_ap))
                                self.tabla.item(row, 4).setText(fmt_moneda_sin_centavos(desc_t))
                                p_unit = p_ap
                            else:
                                p_unit = parse_float_safe(self.tabla.item(row, 2).text())

                            # Actualizar Subtotal
                            self.tabla.item(row, 5).setText(fmt_moneda_sin_centavos(new_cant * p_unit))
                            self._reaplicar_estilo_fila(row)
                            self.actualizar_totales()

                        QTimer.singleShot(50, self.txt_scan.setFocus)
                    return True # Consumido incondicionalmente
                elif event.key() == Qt.Key.Key_Delete:
                    row = self.tabla.currentRow()
                    suprimir_articulo(self, row)
                    return True

        elif obj is self.tabla.viewport():
            if event.type() == QEvent.Resize:
                QTimer.singleShot(0, self._sync_nav_border_overlay)

        return super().eventFilter(obj, event)

    def flash_feedback(self, success=True):
        """Marco verde o rojo. El texto del cobro lo muestra el notificador."""
        from src.cajero.paso5_terminal.componentes_paso5_terminal.apariencia.aviso.flash import (
            flash,
        )

        flash(self, success)
    def bloquear_terminal(self):
        """Bloquea la terminal. Al desbloquear, el cajero seleccionado queda activo."""
        dlg = DialogoCandado(parent=self)
        qt_exec(dlg)   # Si no se desbloquea, la terminal queda bloqueada

        # Actualizar barra de estado según el cajero activo
        self._actualizar_barra_cajero()
        QTimer.singleShot(50, self.txt_scan.setFocus)

    def _actualizar_barra_cajero(self):
        """Refresca el label de la barra de estado con el cajero activo."""
        nombre_str = CajeroActivo.nombre.upper()
        from src.updater.github_updater import get_local_version
        if self.lbl_version is not None:
            if CajeroActivo.numero == 2:
                self.lbl_version.setText(f"🟢 {nombre_str}  |  CF {get_local_version()}")
                self.lbl_version.setObjectName("VersionLabel")
                self.lbl_version.setProperty("estado", "normal")
            else:
                self.lbl_version.setText(f"🔵 {nombre_str}  |  CF {get_local_version()}")
                self.lbl_version.setProperty("estado", "offline")
            self.lbl_version.style().unpolish(self.lbl_version)
            self.lbl_version.style().polish(self.lbl_version)
        if self.btn_candado is not None:
            self.btn_candado.setObjectName("BtnCandado")
            self.btn_candado.setProperty("estado", "normal")
            self.btn_candado.style().unpolish(self.btn_candado)
            self.btn_candado.style().polish(self.btn_candado)
        self._pintar_perfil_cajero()

    def _pintar_perfil_cajero(self):
        """Azul Francia o rosa. La hoja está en apariencia/perfil."""
        from src.cajero.paso5_terminal.componentes_paso5_terminal.apariencia.perfil.pintar import (
            pintar,
        )

        pintar(self)




    def _apply_screen_layout(self):
        """Ajusta tamaños al monitor real (14\" laptop vs 24\" POS)."""
        from src.utils.qt_dpi import terminal_layout_metrics

        m = terminal_layout_metrics()
        ls = m["layout_scale"]

        self.main_layout.setContentsMargins(m["main_margin"], m["main_margin"], m["main_margin"], m["main_margin"])

        self.header_frame.setFixedHeight(m["header_height"])
        self.dashboard_frame.setFixedHeight(m["dashboard_height"])
        self.status_bar.setFixedHeight(m["status_height"])
        self._shortcuts_scroll.setFixedHeight(m["shortcuts_height"])
        self._apply_status_bar_controls(m)

        self.txt_scan.setFixedSize(420, 64)
        scan_px = m["scan_font"]
        total_px = m["total_font"]
        side_px = m["side_font"]
        title_px = m["title_font"]
        row_h = m["table_row"]

        self.lbl_terminal_title.setObjectName("TerminalCabeceraTitulo")
        self.lbl_terminal_title.setStyleSheet(
            "font-size: 28px; font-weight: 800; color: white; letter-spacing: 0px; background: transparent;"
        )
        self.lbl_total_val.setObjectName("TotalGrande")
        self.txt_scan.setObjectName("TerminalScan")
        self.panel_totales.actualizar_estilo_cambio(False)
        self.tabla.verticalHeader().setDefaultSectionSize(row_h)
        self._apply_status_bar_shortcuts_layout(ls)
        self._layout_list_results_popup(m)





    def _apply_status_bar_controls(self, metrics):
        """Escala altura de botones del pie para que coincidan con status_bar."""
        from src.utils.qt_dpi import scale_px

        ls = metrics["layout_scale"]
        ctrl_h = metrics["status_control_height"]
        icon_sz = metrics["status_icon_size"]

        sl = self.status_bar.layout()
        if sl is not None:
            sl.setContentsMargins(scale_px(15, ls), scale_px(5, ls), scale_px(5, ls), scale_px(5, ls))

        for attr in ("btn_teclado", "btn_theme", "btn_espera"):
            btn = getattr(self, attr, None)
            if btn is not None:
                btn.setFixedHeight(ctrl_h)

        for attr in ("btn_candado", "btn_chatbot"):
            btn = getattr(self, attr, None)
            if btn is not None:
                btn.setFixedSize(icon_sz, icon_sz)

    def _apply_status_bar_shortcuts_layout(self, ls=None):
        """F-keys blancas: (Manejado internamente por BarraDeHerramientasInferior)."""
        pass

    def _apply_tabla_column_layout(self):
        # Delegamos la responsabilidad nativamente a Qt usando QHeaderView
        pass

    def _ocultar_busqueda(self):
        if getattr(self, "list_results", None) is not None:
            self.list_results.hide()
        if getattr(self, "panel_busqueda", None) is not None:
            self.panel_busqueda.hide()

    def _mostrar_busqueda(self):
        self._layout_list_results_popup()
        if getattr(self, "panel_busqueda", None) is not None:
            self.panel_busqueda.show()
            self.panel_busqueda.raise_()
        if getattr(self, "list_results", None) is not None:
            self.list_results.show()

    def _color_stock_busqueda(self, selected, stock_val):
        if selected:
            return "#DBEAFE"
        if stock_val <= 0:
            return "#B91C1C"
        if stock_val <= 5:
            return "#C2410C"
        return "#64748B"

    def _pintar_fila_busqueda(self, row, selected):
        item = self.list_results.item(row)
        if not item:
            return
        w = self.list_results.itemWidget(item)
        if not w:
            return
        lbl_n = w.findChild(QLabel, "lbl_n")
        lbl_p = w.findChild(QLabel, "lbl_p")
        lbl_s = w.findChild(QLabel, "lbl_s")
        if not (lbl_n and lbl_p and lbl_s):
            return
        prod = item.data(Qt.UserRole) or {}
        try:
            stk = float(prod.get("stock") or 0)
        except Exception:
            stk = 0.0
        col_s = self._color_stock_busqueda(selected, stk)
        if selected:
            lbl_n.setStyleSheet("font-size: 22px; font-weight: 700; background: transparent; color: #FFFFFF;")
            lbl_p.setStyleSheet("font-size: 21px; font-weight: 700; background: transparent; color: #FFFFFF;")
        else:
            lbl_n.setStyleSheet("font-size: 22px; font-weight: 700; background: transparent; color: #0F172A;")
            lbl_p.setStyleSheet("font-size: 21px; font-weight: 700; background: transparent; color: #047857;")
        lbl_s.setStyleSheet(f"font-size: 18px; font-weight: 600; background: transparent; color: {col_s};")

    def _update_search_colors(self):
        if not hasattr(self, "list_results"):
            return
        row = self.list_results.currentRow()
        prev = getattr(self, "_search_sel_row", -1)
        if prev >= 0 and prev != row:
            self._pintar_fila_busqueda(prev, False)
        if row >= 0:
            self._pintar_fila_busqueda(row, True)
        self._search_sel_row = row

    def _layout_list_results_popup(self, metrics=None):
        if not hasattr(self, "panel_busqueda") or not hasattr(self, "txt_scan"):
            return
        w = max(int(self.width() * 0.72), 980)
        w = min(w, max(720, self.width() - 48))
        n = max(1, self.list_results.count())
        vis = min(n, 10)
        row_h = 72
        h = 48 + vis * row_h + 36
        max_h = max(360, int(self.height() * 0.68))
        h = min(h, max_h)
        from PyQt6.QtCore import QPoint
        pos = self.txt_scan.mapTo(self, QPoint(0, 0))
        x = pos.x()
        if x + w > self.width() - 16:
            x = max(16, self.width() - w - 16)
        y = pos.y() - h - 10
        if y < 8:
            y = 8
            h = max(280, pos.y() - 18)
        self.panel_busqueda.setGeometry(x, y, w, h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_screen_layout()
        if hasattr(self, "list_results"):
            from src.utils.qt_dpi import terminal_layout_metrics
            self._layout_list_results_popup(terminal_layout_metrics())

    def actualizar_reloj(self):
        ahora = datetime.now()
        self.cabecera.actualizar_reloj(ahora)

        # Cada 5 segundos verificamos los niveles de efectivo en caja para activar alertas SOS
        if ahora.second % 5 == 0:
            self.check_alertas_efectivo()

        # Cada 3 segundos verificamos si el Administrador ha solicitado un arqueo remoto (Señal de Cierre)
        if ahora.second % 3 == 0:
            self.check_solicitud_cierre_remoto()

        # Si es el inicio de un nuevo día (Medianoche exacta), forzamos el cierre automático
        if ahora.hour == 0 and ahora.minute == 0 and ahora.second == 1:
            self.check_midnight_closure()

    def _cerrar_abierto_paso5(self):
        """Cierra lo que tapa la venta. El cobro no entra: es otro paso."""
        from PyQt6.QtWidgets import QApplication
        if QApplication.activeModalWidget() is not None:
            return
        self._ocultar_busqueda()
        ventana = self.window()
        asistente = getattr(ventana, "chatbot_overlay", None)
        if asistente is not None and asistente.isVisible():
            asistente.cerrar_chat()

    def asegurar_foco_escaner(self):
        if not self.isVisible() or not getattr(self, "txt_scan", None):
            return
        from PyQt6.QtWidgets import QApplication, QLineEdit, QTextEdit
        if QApplication.activeModalWidget() is not None:
            self._foco_lejos_ms = 0
            return
        if self.txt_scan.hasFocus():
            self._foco_lejos_ms = 0
            self._firma_foco_ajeno = None
            return
        foco = QApplication.focusWidget()
        if isinstance(foco, (QLineEdit, QTextEdit)) and foco is not self.txt_scan:
            firma = foco.text() if isinstance(foco, QLineEdit) else foco.toPlainText()
            if firma != getattr(self, "_firma_foco_ajeno", None):
                self._firma_foco_ajeno = firma
                self._foco_lejos_ms = 0
                return
        else:
            self._firma_foco_ajeno = None
        self._foco_lejos_ms = getattr(self, "_foco_lejos_ms", 0) + 150
        if self._foco_lejos_ms < 2000:
            return
        self._foco_lejos_ms = 0
        self._ocultar_busqueda()
        self.txt_scan.setFocus()

    def check_alertas_efectivo(self):
        """Monitorea el efectivo en caja y parpadea los bordes si excede los límites."""
        self._refrescar_notificaciones()
        # El borde verde/rojo del cobro manda. El exceso queda solo en el notificador.
        if getattr(self, "_flash_borde", False):
            return
        if hasattr(self, '_parpadeo_activo') and self._parpadeo_activo:
            return
        from src.config import config
        c_id = config.get("caja_id", 1)
        efectivo = self.controller.movimientos_caja.obtener_efectivo_caja(c_id)

        # Obtener los umbrales configurados por el administrador (o usar defaults industriales)
        from src.config import config as _c
        umbral_naranja = float(_c.get("limite_efectivo_naranja", 50000.0))
        umbral_rojo    = float(_c.get("limite_efectivo_rojo",    70000.0))

        color_borde = None
        if efectivo >= umbral_rojo:
            color_borde = "#F97316"  # NARANJA (Crítico - Retiro Urgente)
        elif efectivo >= umbral_naranja:
            color_borde = "#EAB308"  # AMARILLO (Advertencia - Retiro Próximo)

        if color_borde:
            self._parpadeo_activo = True
            estilo_orig = self.dashboard_frame.styleSheet()

            # Parpadeo: encender borde grueso
            self.dashboard_frame.setProperty("modo_cobro", "true"); self.dashboard_frame.style().unpolish(self.dashboard_frame); self.dashboard_frame.style().polish(self.dashboard_frame)

            def apagar():
                self.dashboard_frame.setProperty("modo_cobro", "false"); self.dashboard_frame.style().unpolish(self.dashboard_frame); self.dashboard_frame.style().polish(self.dashboard_frame)
                self._parpadeo_activo = False

            # Apagar el borde en 800ms para crear el efecto intermitente
            QTimer.singleShot(800, apagar)

    def check_midnight_closure(self):
        """ Verifica si hay ventas del día anterior y reinicia la app si es necesario """
        from src.services.caja_service import verificar_y_realizar_autocierre
        from PyQt6.QtWidgets import QMessageBox, QApplication

        hizo, monto = verificar_y_realizar_autocierre()
        if hizo:
             QMessageBox.warning(self, "🌙 CIERRE AUTOMÁTICO DIARIO",
                f"El sistema ha realizado el cierre automático del día anterior por valor de ${monto:.2f}.\n\n"
                "Para continuar, la aplicación se reiniciará para que inicies el nuevo turno del día.")
             QApplication.exit(888) # Código de reinicio en main.py

    def check_solicitud_cierre_remoto(self):
        if not self.isVisible():
            return

        if getattr(self, '_cierre_en_progreso', False):
            return

        try:
            from src.config import config
            c_id = config.get("caja_id", 1)
            if self.controller.cierre_remoto.verificar_solicitud_cierre_remoto(c_id):
                self._cierre_en_progreso = True

                # Mostrar cuadro de dialogo informativo industrial alertando del Cierre Remoto
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, "⚠️ ARQUEO DE CAJA REQUERIDO",
                    "La administración central ha solicitado el arqueo y cierre de esta terminal.\n\n"
                    "Por favor, proceda a ingresar el efectivo contado físico para finalizar la sesión.",
                    QMessageBox.Ok
                )

                # Gatillar la ventana de cierre (Paso 7)
                self.abrir_cierre_caja()
                self._cierre_en_progreso = False
        except Exception as e:
            self._cierre_en_progreso = False
            print(f"Error verificando cierre remoto: {e}")

    def _texto_es_codigo(self, txt):
        """Un código de barras o una cantidad*código se resuelve al Enter, sin LIKE."""
        if not txt or txt.startswith("+"):
            return False
        if "*" in txt:
            _, der = txt.split("*", 1)
            der = der.strip()
            return (not der) or der.isdigit()
        return txt.isdigit()

    def actualizar_busqueda(self):
        # El nombre espera 160 ms. El código no consulta hasta Enter.
        txt = self.txt_scan.text().strip()
        if self._texto_es_codigo(txt):
            self.search_timer.stop()
            if getattr(self, "list_results", None) is not None and not self.list_results.isHidden():
                self._ocultar_busqueda()
            return
        self.search_timer.start(160)

    def _do_busqueda(self):
        txt = self.txt_scan.text().strip()
        if not txt or txt.startswith('+'):
            self._ocultar_busqueda()
            return

        if '*' in txt:
            partes = txt.split('*', 1)
            txt = partes[1].strip()
            if not txt:
                self._ocultar_busqueda()
                return

        res = self.controller.carrito.buscar_productos(txt)
        self.list_results.clear()

        if res:
            for r in res:
                stk = float(r['stock'] or 0.0)
                stk_str = self._fmt_stock_mostrar(r, stk)

                item = QListWidgetItem()
                item.setData(Qt.UserRole, r)
                self.list_results.addItem(item)

                w = QWidget()
                w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                lay = QHBoxLayout(w)
                lay.setContentsMargins(28, 14, 28, 14)
                lay.setSpacing(28)
                w.setFixedHeight(72)

                lbl_n = QLabel(str(r['nombre']))
                lbl_n.setObjectName("lbl_n")
                lbl_n.setStyleSheet("font-size: 22px; font-weight: 700; background: transparent; color: #0F172A;")
                lbl_n.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

                lbl_p = QLabel(f"${r['precio']:.2f}")
                lbl_p.setObjectName("lbl_p")
                lbl_p.setFixedWidth(180)
                lbl_p.setStyleSheet("font-size: 21px; font-weight: 700; background: transparent; color: #047857;")
                lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                lbl_s = QLabel(stk_str)
                lbl_s.setObjectName("lbl_s")
                lbl_s.setFixedWidth(170)
                col_s = self._color_stock_busqueda(False, stk)
                lbl_s.setStyleSheet(f"font-size: 15px; font-weight: 600; background: transparent; color: {col_s};")
                lbl_s.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                lay.addWidget(lbl_n, 1)
                lay.addWidget(lbl_p)
                lay.addWidget(lbl_s)

                item.setSizeHint(w.sizeHint())
                self.list_results.setItemWidget(item, w)
            self._search_sel_row = -1
            self.list_results.setCurrentRow(0)
            self._update_search_colors()
            nres = self.list_results.count()
            if hasattr(self, "lbl_busqueda_pie"):
                self.lbl_busqueda_pie.setText(f"{nres} resultado{'s' if nres != 1 else ''}   ·   Enter agregar   ·   Esc cerrar")
            self._mostrar_busqueda()
        else:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, None)
            vacio = QLabel(f"Sin resultados para «{txt}»")
            vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vacio.setStyleSheet("font-size: 16px; font-weight: 700; color: #B91C1C; background: transparent;")
            vacio.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            item.setSizeHint(vacio.sizeHint())
            self.list_results.addItem(item)
            self.list_results.setItemWidget(item, vacio)
            self.list_results.clearSelection()
            if hasattr(self, "lbl_busqueda_pie"):
                self.lbl_busqueda_pie.setText("Esc cerrar")
            self._mostrar_busqueda()

    def seleccionar_item_busqueda(self):
        current = self.list_results.currentItem()
        if current:
            p = current.data(Qt.UserRole)
            if p:
                # Si el usuario había ingresado un multiplicador en el texto, lo rescatamos
                txt_raw = self.txt_scan.text().strip()
                cant_multi = 1.0
                if '*' in txt_raw:
                    try: cant_multi = float(txt_raw.split('*')[0].replace(',', '.'))
                    except: pass
                self.agregar_a_tabla(p, cant_multi)
                self.txt_scan.clear()
                self._ocultar_busqueda()
                self.txt_scan.setFocus()

    def procesar_scan(self):
        from src.utils.barcode_parser import BarcodeParser
        self.search_timer.stop()
        self._cerrar_abierto_paso5()
        txt_raw = self.txt_scan.text()

        if not self.list_results.isHidden():
            current = self.list_results.currentItem()
            if current:
                p = current.data(Qt.UserRole)
                if p:
                    _, cantidad = BarcodeParser.parse_scan_text(txt_raw)
                    self.agregar_a_tabla(p, cantidad)
                    self.txt_scan.clear()
                    self._ocultar_busqueda()
                    self.txt_scan.setFocus()
                    return

        success, p, cantidad, error_msg = self.controller.carrito.procesar_codigo_escaneado(txt_raw)

        if error_msg == 'FINALIZAR_VENTA':
            self.finalizar_venta()
            return

        if success and p:
            self.agregar_a_tabla(p, cantidad)
            self.txt_scan.clear()
            self._ocultar_busqueda()
            self.txt_scan.setFocus()
            return

        if error_msg:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, 'Atención', error_msg)
            self.txt_scan.selectAll()
            self.txt_scan.setFocus()
            return

    def agregar_a_tabla(self, p, cantidad=1.0):
        self._cerrar_abierto_paso5()
        # Congela el dibujo hasta el final. El finally lo suelta aunque falle el cálculo.
        self.setUpdatesEnabled(False)
        try:
            self._agregar_a_tabla_calculado(p, cantidad)
        finally:
            self.setUpdatesEnabled(True)

    def _agregar_a_tabla_calculado(self, p, cantidad=1.0):
        self.en_venta = True
        p_id = str(p['id'])
        precio_base = float(p['precio'])

        cant_of = 0.0
        precio_of = 0.0
        cant_may = 0.0
        precio_may = 0.0
        if hasattr(p, 'keys'):
            if 'cant_oferta' in p.keys(): cant_of = float(p['cant_oferta'] or 0.0)
            if 'precio_oferta' in p.keys(): precio_of = float(p['precio_oferta'] or 0.0)
            if 'cant_mayoreo' in p.keys(): cant_may = float(p['cant_mayoreo'] or 0.0)
            if 'precio_mayoreo' in p.keys(): precio_may = float(p['precio_mayoreo'] or 0.0)

        # 1. Agrupar si el producto ya existe en la tabla (Auto-Suma), excepto Artículos Comunes
        if p_id != "000":
            for i in range(self.tabla.rowCount()):
                if self.tabla.item(i, 0).text() == p_id:
                    old_cant = float(self.tabla.item(i, 3).text())
                    new_cant = old_cant + cantidad
                    if not self._validar_stock(p, p_id, new_cant):
                        self.setUpdatesEnabled(True)
                        return

                    # Verificamos si alcanza o supera la cantidad de mayoreo u oferta
                    if cant_may > 0 and precio_may > 0 and new_cant >= cant_may:
                        p_aplicar = precio_may
                        desc_total = (precio_base - precio_may) * new_cant
                        display_name = f"📦 [MAYOREO] {p['nombre']}"
                    elif cant_of > 0 and precio_of > 0 and new_cant >= cant_of:
                        p_aplicar = precio_of
                        desc_total = (precio_base - precio_of) * new_cant
                        display_name = f"🔥 [OFERTA] {p['nombre']}"
                    else:
                        p_aplicar = precio_base
                        desc_total = 0.0
                        display_name = str(p['nombre'])

                    # Actualizar Nombre con el distintivo
                    self.tabla.item(i, 1).setText(display_name)
                    # Actualizar Precio Unitario Aplicado
                    self.tabla.item(i, 2).setText(fmt_moneda_sin_centavos(p_aplicar))
                    # Actualizar cantidad
                    self.tabla.item(i, 3).setText(f"{new_cant:.2f}" if new_cant % 1 != 0 else f"{int(new_cant)}")
                    # Actualizar Descuento Total
                    self.tabla.item(i, 4).setText(fmt_moneda_sin_centavos(desc_total))
                    # Actualizar Subtotal
                    self.tabla.item(i, 5).setText(fmt_moneda_sin_centavos(new_cant * p_aplicar))
                    self.last_active_row = i
                    self._reaplicar_estilo_fila(i)

                    # Foco visual sutil centrado en el duplicado
                    self.tabla.selectRow(i)
                    self.actualizar_totales()
                    self.setUpdatesEnabled(True)
                    self.repaint()
                    return

        if not self._validar_stock(p, p_id, cantidad):
            self.setUpdatesEnabled(True)
            return

        # 2. Si no existe, calculamos para la inserción de la fila nueva
        if cant_may > 0 and precio_may > 0 and cantidad >= cant_may:
            p_aplicar = precio_may
            desc_total = (precio_base - precio_may) * cantidad
            display_name = f"📦 [MAYOREO] {p['nombre']}"
        elif cant_of > 0 and precio_of > 0 and cantidad >= cant_of:
            p_aplicar = precio_of
            desc_total = (precio_base - precio_of) * cantidad
            display_name = f"🔥 [OFERTA] {p['nombre']}"
        else:
            p_aplicar = precio_base
            desc_total = 0.0
            display_name = str(p['nombre'])

        row = self.tabla.rowCount()
        self.tabla.insertRow(row)

        items = [p_id, display_name, fmt_moneda_sin_centavos(p_aplicar), f"{cantidad:.2f}" if cantidad % 1 != 0 else f"{int(cantidad)}", fmt_moneda_sin_centavos(desc_total), fmt_moneda_sin_centavos(p_aplicar * cantidad)]
        for idx, v in enumerate(items):
            it = QTableWidgetItem(v)
            it.setTextAlignment(Qt.AlignCenter)

            font = it.font()
            font.setBold(True) # Inquebrantable para toda la fila
            it.setFont(font)

            if idx == 1:
                it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            elif idx in (2, 3, 4, 5):
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            if idx == 5:
                it.setForeground(QColor("#059669")) # Esmeralda fuerte
                it.setFlags(it.flags() & ~Qt.ItemIsSelectable) # Deshabilitar selección para blindar su fondo verde agua

            self.tabla.setItem(row, idx, it)

        self.last_active_row = row
        self._reaplicar_estilo_fila(row)
        self.tabla.selectRow(row)
        self.actualizar_totales()

        # Sonido BEEP de Escáner ultra rápido
        if AUDIO_ENABLED:
            def fast_beep():
                try: import winsound; winsound.Beep(2500, 50)
                except: pass
            threading.Thread(target=fast_beep, daemon=True).start()

        # OPTIMIZACION: Liberar la pantalla para que dibuje el resultado final en 1 solo cuadro
        self.setUpdatesEnabled(True)
        self.repaint()

    def _evaluar_combos(self):
        if getattr(self, '_evaluando_combos', False): return
        self._evaluando_combos = True
        try:
            combos_activos = self.controller.stock_ofertas.combos_para_ticket()
            if not combos_activos:
                if getattr(self, "_ticket_tiene_combo", False):
                    i = 0
                    while i < self.tabla.rowCount():
                        celda = self.tabla.item(i, 0)
                        if celda and celda.text().startswith("COMBO-"):
                            self.tabla.removeRow(i)
                        else:
                            i += 1
                    self._ticket_tiene_combo = False
                return

            # 1. Eliminar filas previas de combo
            i = 0
            while i < self.tabla.rowCount():
                if self.tabla.item(i, 0).text().startswith("COMBO-"):
                    self.tabla.removeRow(i)
                else:
                    i += 1

            # 2. Recolectar stock virtual en la canasta actual
            canasta = {}
            for row in range(self.tabla.rowCount()):
                id_p = self.tabla.item(row, 0).text()
                cant = float(self.tabla.item(row, 3).text())
                precio = parse_float_safe(self.tabla.item(row, 2).text())
                if id_p not in canasta:
                    canasta[id_p] = {"cant": 0, "precio": precio}
                canasta[id_p]["cant"] += cant

            # 3. Aplicar combos ya recordados
            import json
            import socket
            # 4. Aplicar Combos
            combos_aplicados_ahora = []
            for combo in combos_activos:
                # Cuántas veces podemos aplicar este combo con la canasta actual?
                veces_aplicable = 999999
                costo_original_por_combo = 0
                for req in combo["reqs"]:
                    req_id = str(req["id_producto"])
                    req_cant = float(req["cantidad"])
                    disp = canasta.get(req_id, {"cant": 0, "precio": 0})
                    if req_cant > 0:
                        veces = int(disp["cant"] // req_cant)
                        if veces < veces_aplicable: veces_aplicable = veces
                    costo_original_por_combo += (disp["precio"] * req_cant)

                if veces_aplicable > 0 and veces_aplicable < 999999:
                    for req in combo["reqs"]:
                        req_id = str(req["id_producto"])
                        req_cant = float(req["cantidad"])
                        canasta[req_id]["cant"] -= (req_cant * veces_aplicable)

                    precio_final_combo = combo["precio_combo"]
                    ahorro_unitario = costo_original_por_combo - precio_final_combo
                    if ahorro_unitario > 0:
                        ahorro_total_desc = ahorro_unitario * veces_aplicable

                        r = self.tabla.rowCount()
                        self.tabla.insertRow(r)

                        from src.cajero.paso5_terminal.paso5_terminal import fmt_moneda_sin_centavos
                        items = [f"COMBO-{combo['id']}", f"🎁 [COMBO] {combo['nombre']}", fmt_moneda_sin_centavos(-ahorro_unitario), str(veces_aplicable), "0", fmt_moneda_sin_centavos(-ahorro_total_desc)]
                        for idx, v in enumerate(items):
                            it = QTableWidgetItem(v)
                            it.setTextAlignment(Qt.AlignCenter if idx != 1 else Qt.AlignLeft | Qt.AlignVCenter)
                            if idx in (2, 3, 4, 5): it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                            font = it.font(); font.setBold(True); it.setFont(font)
                            if idx == 5:
                                from PyQt6.QtGui import QColor
                                it.setForeground(QColor("#059669"))
                                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                            self.tabla.setItem(r, idx, it)

                        combos_aplicados_ahora.append(combo["nombre"])

                        # Emitir señal UDP
                        try:
                            udp_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            try:
                                from src.config import config
                                msg = json.dumps({
                                    "type": "COMBO_TRIGGERED",
                                    "combo": combo["nombre"],
                                    "precio_original": costo_original_por_combo * veces_aplicable,
                                    "precio_final": precio_final_combo * veces_aplicable,
                                    "ahorro": ahorro_total_desc,
                                    "caja_id": config.get("caja_id", 1)
                                })
                                udp_s.sendto(msg.encode('utf-8'), ("<broadcast>", 37021))
                            finally:
                                udp_s.close()
                        except Exception:
                            pass

            self._ticket_tiene_combo = bool(combos_aplicados_ahora)
        finally:
            self._evaluando_combos = False

    def actualizar_totales(self):
        filas_antes = self.tabla.rowCount()
        tenia_combo = getattr(self, "_ticket_tiene_combo", False)
        self._evaluar_combos()

        filas = self.tabla.rowCount()
        hay_combo = getattr(self, "_ticket_tiene_combo", False)
        pintadas = getattr(self, "_filas_pintadas", -1)
        linea_nueva = (
            not tenia_combo and not hay_combo and pintadas >= 0
            and filas == filas_antes + 1 and filas == pintadas + 1
        )
        if hay_combo or (filas != filas_antes and not linea_nueva) or (filas != pintadas and not linea_nueva):
            for i in range(filas):
                self._reaplicar_estilo_fila(i)
        else:
            previa = getattr(self, "_fila_pintada", -1)
            actual = getattr(self, "last_active_row", -1)
            if previa != actual and 0 <= previa < filas:
                self._reaplicar_estilo_fila(previa)
            if 0 <= actual < filas:
                self._reaplicar_estilo_fila(actual)
        self._filas_pintadas = filas
        self._fila_pintada = getattr(self, "last_active_row", -1)

        from src.utils.dinero import redondear_dinero
        total = redondear_dinero(
            sum(parse_float_safe(self.tabla.item(i, 5).text()) for i in range(self.tabla.rowCount()))
        )
        cant = sum(float(self.tabla.item(i, 3).text()) for i in range(self.tabla.rowCount()))
        total_desc = redondear_dinero(
            sum(abs(parse_float_safe(self.tabla.item(i, 4).text())) for i in range(self.tabla.rowCount()))
        )

        # El total grande vuelve a usar el formato sin centavos con comas de miles
        total_str = fmt_moneda_sin_centavos(total)
        self.lbl_total_val.setText(total_str)
        self.panel_totales.ajustar_cuerpo()
        self.lbl_cant_val.setText(f"{int(cant)}")

        # Si estamos agregando items, limpiamos los "Pagos" y "Cambio" de la venta anterior
        if self.en_venta:
            cant_txt = f"{cant:.2f}" if cant % 1 != 0 else f"{int(cant):,}"
            self.lbl_side_cant.setText(cant_txt)
            total_sin = fmt_moneda_sin_centavos(total)
            desc_sin = fmt_moneda_sin_centavos(total_desc)
            self.lbl_side_total.setText(total_sin)
            if total_desc > 0:
                self.lbl_side_ahorro.setText(desc_sin)
                self.lbl_side_ahorro_t.show()
                self.lbl_side_ahorro.show()
            else:
                self.lbl_side_ahorro_t.hide()
                self.lbl_side_ahorro.hide()
            self.lbl_side_pagos.setText("0")
            self.lbl_side_cambio.setText("0")
            self.panel_totales.actualizar_estilo_cambio(False)

        # Gatillar la animación interactiva de ahorro total
        self.animar_ahorro(total_desc)

    def animar_ahorro(self, nuevo_ahorro):
        """
        Animación interactiva premium tipo 'saldo ascendente'.
        Incrementa el valor del ahorro de forma asíncrona y fluida sin parpadeos de tamaño.
        """
        if not hasattr(self, 'current_ahorro'):
            self.current_ahorro = 0.0

        if nuevo_ahorro > 0 and abs(self.current_ahorro - float(nuevo_ahorro)) < 0.005:
            return

        if hasattr(self, '_respiracion_anim') and self._respiracion_anim:
            self._respiracion_anim.stop()
            self._respiracion_anim = None

        if hasattr(self, '_ahorro_anim') and self._ahorro_anim:
            self._ahorro_anim.stop()
            self._ahorro_anim = None

        if hasattr(self, '_zoom_ahorro_anim') and self._zoom_ahorro_anim:
            self._zoom_ahorro_anim.stop()
            self._zoom_ahorro_anim = None
        self.panel_totales._ahorro_en_zoom = False

        if nuevo_ahorro <= 0:
            self.current_ahorro = 0.0
            self.lbl_ahorro_val.hide()
            self.panel_totales.repartir_centro(False)
            return

        self.panel_totales.repartir_centro(True)
        self.lbl_ahorro_val.set_escala(0.28)
        self.lbl_ahorro_val.show()
        self.lbl_ahorro_val.setObjectName("AhorroVal")
        self._zoom_ahorro()

        from src.utils.qt_compat import VariantFloatAnimation
        self._ahorro_anim = VariantFloatAnimation(self)
        # El usuario pidió explícitamente que SIEMPRE arranque desde cero
        self._ahorro_anim.setStartValue(0.0)
        self._ahorro_anim.setEndValue(nuevo_ahorro)
        self._ahorro_anim.setDuration(1200) # 1.2 segundos (rápido pero fluido)

        def on_value_changed(value):
            self.lbl_ahorro_val.setText(f"+${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            self.panel_totales.ajustar_cuerpo()

        def on_finished():
            self.current_ahorro = nuevo_ahorro
            plata = f"${nuevo_ahorro:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.lbl_ahorro_val.setText(f"AHORRÁS {plata}")
            self.panel_totales.ajustar_cuerpo()

        self._ahorro_anim.valueChanged.connect(on_value_changed)
        self._ahorro_anim.finished.connect(on_finished)
        self._ahorro_anim.start()

    def _zoom_ahorro(self):
        """Escala el cartel: entra chico y crece hasta su tamaño. La letra no se toca."""
        etiqueta = self.lbl_ahorro_val
        etiqueta.set_escala(0.28)

        from PyQt6.QtCore import QEasingCurve
        from src.utils.qt_compat import VariantFloatAnimation

        if hasattr(self, '_zoom_ahorro_anim') and self._zoom_ahorro_anim:
            self._zoom_ahorro_anim.stop()

        anim = VariantFloatAnimation(self)
        anim.setStartValue(0.28)
        anim.setEndValue(1.0)
        anim.setDuration(620)
        anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutCubic))

        def on_step(escala):
            etiqueta.set_escala(float(escala))

        def on_done():
            etiqueta.set_escala(1.0)

        anim.valueChanged.connect(on_step)
        anim.finished.connect(on_done)
        self._zoom_ahorro_anim = anim
        anim.start()

    def iniciar_respiracion_ahorro(self):
        """
        Efecto continuo de brillo (glow) para llamar la atención sobre el ahorro,
        pero manteniendo el tamaño de la fuente estrictamente estático en 38px.
        """
        from src.utils.qt_compat import VariantFloatAnimation, easing_sine_curve

        if hasattr(self, '_respiracion_anim') and self._respiracion_anim:
            return

        self._respiracion_anim = VariantFloatAnimation(self)
        self._respiracion_anim.setStartValue(0.0)
        self._respiracion_anim.setEndValue(1.0)
        self._respiracion_anim.setDuration(1500)
        self._respiracion_anim.setEasingCurve(easing_sine_curve())
        self._respiracion_anim.setLoopCount(-1) # Bucle infinito

        def on_step(t):
            val_norm = (t + 1.0) / 2.0

            # Solo efecto brillo, SIN modificar tamaño
            glow_radius = int(10 + (15 * val_norm))
            alpha = int(100 + (120 * val_norm))

            from PyQt6.QtGui import QColor
            if hasattr(self, 'ahorro_glow') and self.ahorro_glow:
                self.ahorro_glow.setBlurRadius(glow_radius)
                self.ahorro_glow.setColor(QColor(255, 69, 0, alpha))

        self._respiracion_anim.valueChanged.connect(on_step)
        self._respiracion_anim.start()

    def abrir_retiro_efectivo(self):
        """Abre el panel rápido de retiro de efectivo de caja (F5)."""
        from src.config import config
        c_id = config.get("caja_id", 1)
        efectivo = self.controller.movimientos_caja.obtener_efectivo_caja(c_id)

        dlg = DialogoRetiroEfectivo(efectivo, parent=self)
        if qt_exec(dlg) and dlg.monto_retirado > 0:
            # Solicitar PIN de confirmación del operador activo
            pin_dlg = DialogoPIN(CajeroActivo.nombre, parent=self)
            if qt_exec(pin_dlg) and pin_dlg.ok:
                monto = dlg.monto_retirado
                motivo = getattr(dlg, "motivo", "Retiro rápido de efectivo en terminal")
                usuario = CajeroActivo.nombre
                from src.config import config
                c_id = config.get("caja_id", 1)
                if self.controller.movimientos_caja.registrar_retiro_efectivo(monto, usuario, motivo, c_id):
                    self.flash_feedback(success=True)
                    # Marcar apertura como autorizada para el monitor de seguridad
                    self._apertura_autorizada = True
                    self.monitor_cajon_bloqueante(manual=True)
                    self.check_alertas_efectivo()
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", "No se pudo registrar el retiro en la base de datos.")

        QTimer.singleShot(50, self.txt_scan.setFocus)

    def abrir_ingreso_efectivo(self):
        """Abre el panel de ingreso manual de dinero a la caja (F6)."""
        dlg = DialogoIngresoEfectivo(parent=self)
        if qt_exec(dlg) and dlg.monto_ingresado > 0:
            # Solicitar PIN de confirmación del operador activo
            pin_dlg = DialogoPIN(CajeroActivo.nombre, parent=self)
            if qt_exec(pin_dlg) and pin_dlg.ok:
                monto = dlg.monto_ingresado
                motivo = getattr(dlg, "motivo", "Ingreso manual de efectivo en terminal")
                usuario = CajeroActivo.nombre
                from src.config import config
                c_id = config.get("caja_id", 1)

                # Novedad: Si es un abono a Fiado, procesar la deuda en DB
                if getattr(dlg, "tipo_ingreso", "") == "FIADO" and getattr(dlg, "cliente_id", None):
                    from src.repositories.cliente_repository import ClienteRepository
                    exito, nuevo_saldo, nombre_cli = ClienteRepository.registrar_abono(dlg.cliente_id, monto)
                    if exito:
                        motivo = f"Abono Fiado: {nombre_cli} - Saldo restante: ${nuevo_saldo:,.2f}"

                if self.controller.movimientos_caja.registrar_ingreso_efectivo(monto, usuario, motivo, c_id):
                    self.flash_feedback(success=True)
                    self.monitor_cajon_bloqueante(manual=True)
                    self.check_alertas_efectivo()
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso en la base de datos.")

        QTimer.singleShot(50, self.txt_scan.setFocus)

    def showEvent(self, event):
        super().showEvent(event)
        from src.config import config as _c
        _c._load_config()
        self._refresh_urgencia_stock_banner()

    def keyPressEvent(self, event):
        k = event.key()

        # F1: Foco al buscador
        if k == Qt.Key.Key_F1:
            self.txt_scan.setFocus(); self.txt_scan.selectAll()
            return

        # F3: Historial
        if k == Qt.Key.Key_F3:
            self.abrir_historial_dia()
            return

        # F12: Cobrar
        if k == Qt.Key.Key_F12:
            self.finalizar_venta()
            return

        # F5: Retiro
        if k == Qt.Key.Key_F5:
            self.abrir_retiro_efectivo()
            return

        # F6: Ingreso
        if k == Qt.Key.Key_F6:
            self.abrir_ingreso_efectivo()
            return

        # F4: Cierre de Caja
        if k == Qt.Key.Key_F4:
            self.abrir_cierre_caja()
            return

        # Flecha Abajo desde el buscador
        if self.txt_scan.hasFocus() and k == Qt.Key.Key_Down:
            if not self.list_results.isHidden():
                self.list_results.setFocus()
            elif self.tabla.rowCount() > 0:
                self.tabla.setFocus()
                self.tabla.selectRow(self.tabla.rowCount() - 1)
                self.tabla.setCurrentCell(self.tabla.rowCount() - 1, 3)
                QTimer.singleShot(0, self._on_tabla_nav_row_only)
            return

        # Navegar en lista de resultados
        if self.list_results.hasFocus():
            if k == Qt.Key.Key_Up and self.list_results.currentRow() == 0:
                self.txt_scan.setFocus()
                return
            if k in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                self.seleccionar_item_busqueda()
                return

        # Edición en la tabla
        if self.tabla.hasFocus():
            row = self.tabla.currentRow()
            if row != -1:
                if k in [Qt.Key.Key_Left, Qt.Key.Key_Right]:
                    old_v = float(self.tabla.item(row, 3).text())
                    inc = 1 if k == Qt.Key.Key_Right else -1
                    new_v = max(0, old_v + inc)

                    if new_v <= 0:
                        self.tabla.removeRow(row)
                        self.actualizar_totales()
                        self.txt_scan.setFocus()
                        return

                    # 1. "Se infla para que el cliente lo vea"
                    self.tabla.setRowHeight(row, 70)

                    it_edit = self.tabla.item(row, 3)
                    it_edit.setText(f"{new_v:.2f}" if new_v % 1 != 0 else f"{int(new_v)}")
                    font_inflada = it_edit.font()
                    font_inflada.setPointSize(32)
                    font_inflada.setBold(True)
                    it_edit.setFont(font_inflada)
                    it_edit.setForeground(QColor("#FF0000")) # Rojo advertencia

                    # Verificación dinámica de ofertas al ajustar cantidad
                    p_id = self.tabla.item(row, 0).text()
                    oferta = self.controller.stock_ofertas.obtener_ofertas_producto(p_id)
                    res_of = [oferta] if oferta else []
                    if res_of and p_id != "000":
                        p_base = float(res_of[0]['precio'])
                        c_of = float(res_of[0]['cant_oferta'] or 0.0)
                        p_of = float(res_of[0]['precio_oferta'] or 0.0)

                        if c_of > 0 and p_of > 0 and new_v >= c_of:
                            p_ap = p_of
                            desc_t = (p_base - p_of) * new_v
                            nombre_txt = self.tabla.item(row, 1).text()
                            if "🔥 [OFERTA]" not in nombre_txt:
                                self.tabla.item(row, 1).setText(f"🔥 [OFERTA] {nombre_txt}")
                        else:
                            p_ap = p_base
                            desc_t = 0.0
                            nombre_txt = self.tabla.item(row, 1).text()
                            if "🔥 [OFERTA]" in nombre_txt:
                                clean_name = nombre_txt.replace("🔥 [OFERTA] ", "")
                                self.tabla.item(row, 1).setText(clean_name)

                        self.tabla.item(row, 2).setText(fmt_moneda_sin_centavos(p_ap))
                        self.tabla.item(row, 4).setText(fmt_moneda_sin_centavos(desc_t))
                        p_unit = p_ap
                    else:
                        p_unit = parse_float_safe(self.tabla.item(row, 2).text())

                    # Actualizar subtotal
                    it_sub = self.tabla.item(row, 5)
                    it_sub.setText(fmt_moneda_sin_centavos(new_v * p_unit))

                    font_normal = it_sub.font()
                    font_normal.setPointSize(18)
                    it_sub.setFont(font_normal)
                    it_sub.setForeground(QColor("#FF0000"))

                    self._reaplicar_estilo_fila(row)
                    self.actualizar_totales()
                    return # intercepted

                elif event.key() == Qt.Key.Key_Delete:
                    suprimir_articulo(self, row)
                    return True

                elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    nombre = self.tabla.item(row, 1).text()
                    cant_actual = float(self.tabla.item(row, 3).text())

                    dlg = DialogoEditarCantidad(cant_actual, nombre, self)
                    if qt_exec(dlg):
                        new_cant = dlg.get_value()
                        self.tabla.item(row, 3).setText(f"{new_cant:.2f}" if new_cant % 1 != 0 else f"{int(new_cant)}")

                        # Verificación dinámica de ofertas al ingresar con el Enter
                        p_id = self.tabla.item(row, 0).text()
                        oferta = self.controller.stock_ofertas.obtener_ofertas_producto(p_id)
                        res_of = [oferta] if oferta else []
                        if res_of and p_id != "000":
                            p_base = float(res_of[0]['precio'])
                            c_of = float(res_of[0]['cant_oferta'] or 0.0)
                            p_of = float(res_of[0]['precio_oferta'] or 0.0)
                            c_may = float(res_of[0]['cant_mayoreo'] or 0.0)
                            p_may = float(res_of[0]['precio_mayoreo'] or 0.0)

                            nombre_txt = self.tabla.item(row, 1).text()
                            clean_name = nombre_txt.replace("🔥 [OFERTA] ", "").replace("📦 [MAYOREO] ", "")

                            if c_may > 0 and p_may > 0 and new_cant >= c_may:
                                p_ap = p_may
                                desc_t = (p_base - p_may) * new_cant
                                self.tabla.item(row, 1).setText(f"📦 [MAYOREO] {clean_name}")
                            elif c_of > 0 and p_of > 0 and new_cant >= c_of:
                                p_ap = p_of
                                desc_t = (p_base - p_of) * new_cant
                                self.tabla.item(row, 1).setText(f"🔥 [OFERTA] {clean_name}")
                            else:
                                p_ap = p_base
                                desc_t = 0.0
                                self.tabla.item(row, 1).setText(clean_name)

                            self.tabla.item(row, 2).setText(fmt_moneda_sin_centavos(p_ap))
                            self.tabla.item(row, 4).setText(fmt_moneda_sin_centavos(desc_t))
                            p_unit = p_ap
                        else:
                            p_unit = parse_float_safe(self.tabla.item(row, 2).text())

                        # Actualizar Subtotal
                        self.tabla.item(row, 5).setText(fmt_moneda_sin_centavos(new_cant * p_unit))
                        self._reaplicar_estilo_fila(row)
                        self.actualizar_totales()

                    self.tabla.setRowHeight(row, 40) # Volver al tamaño normal suave
                    QTimer.singleShot(50, self.txt_scan.setFocus)
                    return

            # Permitir que las flechas naveguen por las casillas de la tabla de forma fluida
            if k in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                super().keyPressEvent(event)
                QTimer.singleShot(0, self._on_tabla_nav_row_only)
                return
            super().keyPressEvent(event)
            return

        super().keyPressEvent(event)

    def finalizar_venta(self):
        # Evitar doble apertura accidental
        if hasattr(self, '_cobro_abierto') and self._cobro_abierto: return
        self._cerrar_abierto_paso5()

        try:
            # Como ahora el total visual no tiene decimales ni comas de miles (son puntos),
            # lo calculamos directamente de la tabla para no perder precisión
            from src.utils.dinero import redondear_dinero, redondear_items_carrito
            total = redondear_dinero(
                sum(parse_float_safe(self.tabla.item(i, 5).text()) for i in range(self.tabla.rowCount()))
            )
        except: return
        if total <= 0: return

        self._cobro_abierto = True
        items = []
        for i in range(self.tabla.rowCount()):
            items.append({
                "id": self.tabla.item(i, 0).text(),
                "nombre": self.tabla.item(i, 1).text(),
                "precio": parse_float_safe(self.tabla.item(i, 2).text()),
                "cant": float(self.tabla.item(i, 3).text().replace(",", ".")),
                "subtotal": parse_float_safe(self.tabla.item(i, 5).text())
            })
        items = redondear_items_carrito(items)

        from src.cajero.paso6_cobro import Paso6Cobro
        dlg = Paso6Cobro(total, items, self)
        dlg.descuentaso_oferta = sum(
            abs(parse_float_safe(self.tabla.item(i, 4).text())) for i in range(self.tabla.rowCount())
        )
        dlg.recargar_total_final()

        # Ejecutamos el cobro
        ok = qt_exec(dlg)
        self._cobro_abierto = False
        self._refrescar_notificaciones()

        if ok:
            # Capturar info de la venta exitosa antes de limpiar
            res = getattr(dlg, 'resultado_venta', None)

            self.tabla.setRowCount(0)
            self.en_venta = False
            self.actualizar_totales()
            self.flash_feedback(success=True)

            if res:
                self.lbl_side_total.setText(fmt_moneda_sin_centavos(res['total']))
                self.lbl_side_pagos.setText(fmt_moneda_sin_centavos(res['pago_con']))
                self.lbl_side_cambio.setText(fmt_moneda_sin_centavos(res['cambio']))
                self.panel_totales.actualizar_estilo_cambio(True)

            # Al cobrar exitosamente, si hay un ticket en espera, lo cargamos automáticamente
            if getattr(self, 'tickets_espera', None):
                self._swap_ticket_espera()
        else:
            self.flash_feedback(success=False)

        QTimer.singleShot(100, self.txt_scan.setFocus)

    def _get_ticket_actual_dict(self):
        import datetime
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        filas = []
        for i in range(self.tabla.rowCount()):
            pid = self.tabla.item(i, 0).text()
            nom = self.tabla.item(i, 1).text()
            pre = self.tabla.item(i, 2).text()
            can = self.tabla.item(i, 3).text()
            des = self.tabla.item(i, 4).text()
            tot = self.tabla.item(i, 5).text()
            filas.append((pid, nom, pre, can, des, tot))

        return {
            "hora": hora,
            "cliente_id": getattr(self, "cliente_id", None),
            "cliente_nombre": getattr(self, "cliente_nombre", "Consumidor Final"),
            "desc_general": getattr(self, "descuento_general", 0.0),
            "total": self.lbl_total_val.text() if hasattr(self, "lbl_total_val") else "0",
            "filas": filas,
        }

    def _restaurar_ticket_dict(self, t):
        self.cliente_id = t.get("cliente_id")
        self.cliente_nombre = t.get("cliente_nombre", "Consumidor Final")
        self.descuento_general = float(t.get("desc_general", 0.0))

        for f in t.get("filas", []):
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            for col, val in enumerate(f):
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignCenter)
                font = it.font()
                font.setBold(True)
                it.setFont(font)
                if col == 1:
                    it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                elif col in (2, 3, 4, 5):
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col == 5:
                    it.setForeground(QColor("#059669"))
                    it.setFlags(it.flags() & ~Qt.ItemIsSelectable)
                self.tabla.setItem(row, col, it)
            self.last_active_row = row
            self._reaplicar_estilo_fila(row)

        if self.tabla.rowCount() > 0:
            self.en_venta = True
        self.actualizar_totales()

    def _limpiar_para_nuevo_ticket(self):
        self.tabla.setRowCount(0)
        self.en_venta = False
        self._volcar_carrito_a_carteleria(limpiar=True)
        self.cliente_id = None
        self.cliente_nombre = "Consumidor Final"
        self.descuento_general = 0.0
        self.actualizar_totales()

    def _volcar_carrito_a_carteleria(self, limpiar=False):
        from src.services.carteleria_service import CarteleriaService

        if limpiar:
            CarteleriaService.limpiar_carteleria()
            return

        carrito = []
        total_ahorro = 0.0
        ultimo_producto = ""

        for i in range(self.tabla.rowCount()):
            try:
                nombre = self.tabla.item(i, 1).text().replace("🔥 [OFERTA] ", "").replace("🌟 ", "")
                precio_str = self.tabla.item(i, 2).text().replace("$", "")
                precio_str = precio_str.replace(".", "").replace(",", ".")
                precio = float(precio_str)
                carrito.append({"producto": nombre, "precio": precio})
                ultimo_producto = nombre
                try:
                    desc_str = self.tabla.item(i, 4).text().replace("$", "")
                    desc_str = desc_str.replace(".", "").replace(",", ".")
                    total_ahorro += float(desc_str) if desc_str else 0.0
                except Exception:
                    pass
            except Exception:
                pass

        CarteleriaService.notificar_escaneo(carrito, total_ahorro, ultimo_producto)

    def _actualizar_boton_espera(self):
        if self.btn_espera is None:
            return
        c = len(self.tickets_espera)
        if c > 0:
            self.btn_espera.setText(f"{c} en espera")
            self.btn_espera.setProperty("estado", "con_espera")
        else:
            self.btn_espera.setText("Espera")
            self.btn_espera.setProperty("estado", "sin_espera")
        self.btn_espera.style().unpolish(self.btn_espera)
        self.btn_espera.style().polish(self.btn_espera)

    def _swap_ticket_espera(self, *args, **kwargs):
        actual_lleno = self.tabla.rowCount() > 0
        hay_espera = len(self.tickets_espera) > 0

        if not actual_lleno and not hay_espera:
            return

        if actual_lleno and not hay_espera:
            self.tickets_espera.append(self._get_ticket_actual_dict())
            self._limpiar_para_nuevo_ticket()
            self._actualizar_boton_espera()
            self._volcar_carrito_a_carteleria(limpiar=True)
        elif not actual_lleno and hay_espera:
            t = self.tickets_espera.pop(0)
            self._restaurar_ticket_dict(t)
            self._actualizar_boton_espera()
            self._volcar_carrito_a_carteleria()
        elif actual_lleno and hay_espera:
            ticket_a_guardar = self._get_ticket_actual_dict()
            ticket_a_restaurar = self.tickets_espera.pop(0)
            self._limpiar_para_nuevo_ticket()
            self._restaurar_ticket_dict(ticket_a_restaurar)
            self.tickets_espera.append(ticket_a_guardar)
            self._actualizar_boton_espera()
            self._volcar_carrito_a_carteleria()

    def _alerta_tickets_espera(self):
        if self.tickets_espera:
            if AUDIO_ENABLED:
                winsound.Beep(1000, 300)
                winsound.Beep(1000, 300)

    def _hay_ticket_activo(self):
        """True si hay venta pendiente: carrito, cobro abierto o tickets en espera."""
        if getattr(self, "_cobro_abierto", False):
            return True
        if getattr(self, "tabla", None) is not None and self.tabla.rowCount() > 0:
            return True
        if getattr(self, "tickets_espera", None) and len(self.tickets_espera) > 0:
            return True
        return False

    def abrir_cierre_caja(self):
        if self._hay_ticket_activo():
            QMessageBox.warning(
                self,
                "Ticket activo",
                "No podés cerrar turno con productos en el ticket.\n\n"
                "Cobrá la venta (F12) o vaciá el carrito antes de usar F4.",
            )
            QTimer.singleShot(50, self.txt_scan.setFocus)
            return

        from PyQt6.QtWidgets import QDialog, QVBoxLayout
        from src.ui_global.cierre_diario_ui.cierre_main_ui import CierreGlobalUI

        dlg = QDialog(self)
        dlg.setWindowTitle("Cierre de Caja Global")
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dlg.setFixedSize(1200, 900)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(0, 0, 0, 0)

        cierre = CierreGlobalUI(self, is_terminal=True)
        cierre.btn_back.setText("❌ Cerrar")
        cierre.request_dashboard.connect(dlg.reject)
        cierre.turno_cerrado.connect(dlg.accept)

        lay.addWidget(cierre)

        ok = qt_exec(dlg)

        if ok:
            from PyQt6.QtWidgets import QApplication
            from src.config import config
            config.current_user = None
            QApplication.processEvents()

            # Flash de cierre: el rolling del día ya corrió en background; solo sella
            try:
                from src.ui_components.backup_flash import mostrar_flash_backup_dia

                engine, host = self.controller.get_db_engine_info()
                host = "127.0.0.1"
                try:
                    pass
                except Exception:
                    pass
                mostrar_flash_backup_dia(self, engine, host)
            except Exception:
                try:
                    from src.base_de_datos.autoblindaje_db import AutoBlindajeDB
                    AutoBlindajeDB.finalizar_backup_del_dia("mariadb", "127.0.0.1")
                except Exception:
                    pass

            # Update pendiente: relaunch duro (889). Nunca apply con el .exe aún en uso.
            try:
                from src.updater.silent_auto_updater import is_update_staged
                if is_update_staged():
                    QApplication.exit(889)
                    return
            except Exception:
                pass

            QApplication.exit(888)
        else:
            QTimer.singleShot(50, self.txt_scan.setFocus)

    def abrir_historial_dia(self):
        dlg = DialogoHistorialDia(self)
        qt_exec(dlg)

        QTimer.singleShot(50, self.txt_scan.setFocus)

    def _is_fila_navegacion(self, row):
        return row >= 0 and self.tabla.hasFocus() and row == self.tabla.currentRow()

    def _sync_nav_border_overlay(self):
        if hasattr(self, "_nav_border_overlay"):
            self._nav_border_overlay.sync_and_repaint()

    def _repintar_filas_nav(self, *rows):
        model = self.tabla.model()
        if model is None:
            return
        for r in rows:
            if r is None or r < 0:
                continue
            for c in range(self.tabla.columnCount()):
                self.tabla.update(model.index(r, c))

    def _on_tabla_nav_row_only(self):
        curr = self.tabla.currentRow()
        prev = getattr(self, "_nav_prev_row", -1)
        if prev != curr:
            self._on_tabla_nav_changed(curr, self.tabla.currentColumn(), prev, -1)

    def _on_tabla_nav_changed(self, current_row=-1, current_col=-1, prev_row=-1, prev_col=-1):
        if current_row < 0:
            current_row = self.tabla.currentRow()
        if prev_row < 0 and hasattr(self, "_nav_prev_row"):
            prev_row = self._nav_prev_row
        self._nav_prev_row = current_row

        for i in range(self.tabla.rowCount()):
            self._reaplicar_estilo_fila(i)

        self._repintar_filas_nav(prev_row, current_row)
        self._sync_nav_border_overlay()

    def _reaplicar_estilo_fila(self, row):
        try:
            desc_val = parse_float_safe(self.tabla.item(row, 4).text())
        except Exception:
            desc_val = 0.0

        is_oferta = desc_val > 0
        is_ultimo = (row == getattr(self, "last_active_row", -1))
        is_nav = self._is_fila_navegacion(row)
        activa = is_ultimo or is_nav

        if activa:
            bg_color = QColor(SCAN_ROW_BG)
        elif is_oferta:
            bg_color = QColor("#FFEDD5")
        else:
            bg_color = QColor("#FFFFFF") if row % 2 == 0 else QColor("#F8FAFC")

        for col in range(self.tabla.columnCount()):
            it = self.tabla.item(row, col)
            if not it: continue

            if col == 5:
                it.setBackground(QColor("#D1FAE5") if activa else QColor("#F0FAF4"))
            else:
                it.setBackground(bg_color)

            f = it.font()
            f.setBold(True)
            f.setPointSize(20 if activa else 16)
            it.setFont(f)

            if col == 1:
                it.setForeground(QColor("#1E3A8A") if activa else (QColor("#C2410C") if is_oferta else QColor("#1E3A8A")))
            elif col == 4:
                it.setForeground(QColor("#1E3A8A") if activa else (QColor("#EA580C") if is_oferta else QColor("#EF4444")))
            elif col == 5:
                it.setForeground(QColor("#047857"))
            else:
                it.setForeground(QColor("#1E3A8A") if activa else (QColor("#C2410C") if is_oferta else QColor("#1E293B")))



if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # Mocking config for direct run
    try:
        from src.config import config
        config.current_user = {"username": "TEST_USER", "role": "admin"}
    except: pass
    win = Paso5Terminal()
    win.showMaximized()
    sys.exit(qt_exec(app))
