from src.utils.qt_compat import qt_exec
import src.utils.qt_compat  # noqa: F401 — enums Qt6 antes de widgets
from PyQt6.QtWidgets import (

    QMainWindow, QWidget, QStackedWidget, QLabel, QFrame,
    QGraphicsDropShadowEffect, QApplication, QMessageBox, QPushButton,
    QHBoxLayout, QVBoxLayout
)
import sys
from PyQt6.QtGui import QKeySequence, QColor, QShortcut
from PyQt6.QtCore import Qt, QTimer
# NOTA: Paso5Terminal se importa dentro de _init_screens (lazy) para no
# bloquear la splash screen durante la carga del módulo main_window.
from src.utils.floating_widgets import BotonFlotanteRegreso
from src.logger import logger
from src.config import config
from src.base_de_datos.database import db_manager

# Cache de temas QSS — se leen UNA sola vez del disco y se reutilizan
_QSS_CACHE: dict = {}

# Terminal TPV (pantalla cajero): referencia y mínimo para monitores chicos
_TERMINAL_REF_W = 1366
_TERMINAL_REF_H = 768
_TERMINAL_MIN_W = 1280
_TERMINAL_MIN_H = 720


def _terminal_window_sizes():
    try:
        from src.utils.qt_dpi import scaled_size

        return (
            *scaled_size(_TERMINAL_REF_W, _TERMINAL_REF_H),
            *scaled_size(_TERMINAL_MIN_W, _TERMINAL_MIN_H),
        )
    except Exception:
        return _TERMINAL_REF_W, _TERMINAL_REF_H, _TERMINAL_MIN_W, _TERMINAL_MIN_H


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cobro Fácil")
        ref_w, ref_h, min_w, min_h = _terminal_window_sizes()
        self.resize(ref_w, ref_h)
        self.setMinimumSize(min_w, min_h)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget); self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self._supervisor_mode = False

        # ── Pirámide de acceso F11 ───────────────────────────────────────
        # _came_from_cajero: True si la escalada arrancó desde el terminal
        # El botón flotante desciende: Jefe → Admin → Cajero
        self._came_from_cajero: bool = False
        self._nav_stack: list = []   # alias por retrocompatibilidad
        self._kiosk_mode: bool = False

        # Inicializar cajón y cargar pantallas y atajos
        from src.hardware.cash_drawer import drawer_manager

        # Restablecer cajón y cargar pantallas y atajos
        drawer_manager.reset_all()
        self._init_screens()
        self._init_shortcuts()
        # NOTA: apply_roles() se llama DESPUÉS del login en main.py, no aquí.
        # Llamarlo en __init__ era un doble-procesamiento innecesario.
        self._init_global_alarm()
        self._init_security_monitor()
        self._init_update_banner()

        # ChatBot: Pre-cargado aquí para evitar parpadeos/reseteos del sistema en pantalla completa por Chromium.
        from src.cajero.paso5_terminal.componentes_visuales.componentes_barra_inferior.chatbot.chat_bot import ChatManualWidget as ChatBotWidget
        self.chatbot_overlay = ChatBotWidget(self)
        self.chatbot_overlay.hide()
        self.chatbot_overlay.chat_closed.connect(lambda: setattr(self, '_chatbot_active', False))
        
        self._chatbot_active = False
        self._active_theme_file = None
        self._cargar_datos_timer = QTimer(self)
        self._cargar_datos_timer.setSingleShot(True)
        self._preload_qss_cache()

        # Chequear actualizaciones 10 segundos después de que arranque la UI
        QTimer.singleShot(5000, self._chequear_actualizaciones_bg)

    def _init_security_monitor(self):
        """ Motor de Vigilancia Global: Monitorea el hardware 24/7 sin importar el módulo activo. """
        # Monitor Permanente de Seguridad: Delegado al Motor Global en MainWindow
        from src.hardware.cash_drawer import drawer_manager
        
        self.security_timer = QTimer(self)
        self.security_timer.timeout.connect(drawer_manager.check_status)
        self.security_timer.start(1500) # Chequeo universal cada 1.5s (seguro para hardware)
        
        # Conexiones Reactivas de Seguridad
        drawer_manager.intrusion_detected.connect(self._on_security_breach)
        drawer_manager.drawer_closed.connect(lambda: self.mostrar_alerta_perimetral(False))
        drawer_manager.drawer_opened.connect(self._on_operational_opening)

    def _on_security_breach(self):
        self.mostrar_alerta_perimetral(True, modo="security")
        # Sonido de alerta (opcional, beep del sistema)
        QApplication.beep()

    def _on_operational_opening(self):
        from src.hardware.cash_drawer import drawer_manager
        if drawer_manager.is_authorized:
            self.mostrar_alerta_perimetral(True, modo="info")

    def _init_global_alarm(self):
        """ Inicializa el sistema de alerta perimetral global. """
        self.marco_alerta = QFrame(self)
        self.marco_alerta.setWindowFlags(Qt.FramelessWindowHint)
        self.marco_alerta.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.marco_alerta.setStyleSheet("border: 30px solid #B91C1C; background: transparent;")
        self.marco_alerta.hide()
        
        # Innovación: Marca de Agua de Seguridad
        self.layout_alerta = QVBoxLayout(self.marco_alerta)
        self.layout_alerta.setAlignment(Qt.AlignCenter)
        
        self.lbl_watermark = QLabel("⚠️ CAJÓN ABIERTO ⚠️\nSIN AUTORIZACIÓN")
        self.lbl_watermark.setAlignment(Qt.AlignCenter)
        self.lbl_watermark.setStyleSheet("""
            font-size: 80px; 
            font-weight: 900; 
            color: rgba(255, 255, 255, 200);
            background: transparent;
            border: none;
            letter-spacing: 5px;
        """)
        # Sombra de impacto
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setColor(QColor(0,0,0,200)); shadow.setOffset(5,5)
        self.lbl_watermark.setGraphicsEffect(shadow)
        self.layout_alerta.addWidget(self.lbl_watermark)
        
        self.lbl_timestamp = QLabel("00/00/0000 00:00:00")
        self.lbl_timestamp.setAlignment(Qt.AlignCenter)
        self.lbl_timestamp.setStyleSheet("font-size: 30px; font-weight: bold; color: white; background: transparent; border: none; margin-top: 20px;")
        self.layout_alerta.addWidget(self.lbl_timestamp)
        
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._toggle_blink_alerta)
        self._blink_state = False

    def _init_update_banner(self):
        """Crea el banner de actualizacion estilo celular, oculto hasta que haya novedad."""
        self._update_banner = QFrame(self)
        self._update_banner.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #065f46,stop:1 #0f172a);"
            "border-top:3px solid #34d399; border-radius:0px;}"
        )
        self._update_banner.setFixedHeight(62)
        self._update_banner.hide()

        ban_lay = QHBoxLayout(self._update_banner)
        ban_lay.setContentsMargins(20, 0, 12, 0)
        ban_lay.setSpacing(14)

        ico = QLabel("\U0001f4e6")
        ico.setStyleSheet("font-size:22px; background:transparent; border:none;")
        ban_lay.addWidget(ico)

        self._lbl_update_msg = QLabel("Nueva actualizacion disponible")
        self._lbl_update_msg.setStyleSheet(
            "color:white; font-size:15px; font-weight:bold;"
            "background:transparent; border:none;")
        ban_lay.addWidget(self._lbl_update_msg, stretch=1)

        btn_instalar = QPushButton("\u2b07\ufe0f  INSTALAR AHORA")
        btn_instalar.setStyleSheet(
            "QPushButton{background:#34d399;color:#0f172a;font-weight:900;"
            "font-size:14px;padding:10px 24px;border-radius:8px;border:none;}"
            "QPushButton:hover{background:#6ee7b7;}"
            "QPushButton:pressed{background:#10b981;}")
        btn_instalar.clicked.connect(self._instalar_actualizacion_rapida)
        ban_lay.addWidget(btn_instalar)

        btn_luego = QPushButton("Mas tarde")
        btn_luego.setStyleSheet(
            "QPushButton{background:transparent;color:rgba(255,255,255,0.6);"
            "font-size:12px;padding:8px 14px;border:none;}"
            "QPushButton:hover{color:white;}")
        btn_luego.clicked.connect(self._update_banner.hide)
        ban_lay.addWidget(btn_luego)

        self._posicionar_banner()

    def _posicionar_banner(self):
        if hasattr(self, '_update_banner'):
            self._update_banner.setGeometry(
                0,
                self.height() - 62,
                self.width(),
                62
            )

    def _chequear_actualizaciones_bg(self):
        """Corre en hilo de fondo sin bloquear la UI."""
        import threading
        def _check():
            try:
                from src.updater.silent_auto_updater import (
                    get_status_message,
                    is_update_available,
                    is_update_staged,
                    download_and_stage_update,
                )
                if is_update_staged():
                    msg = get_status_message()
                    if msg:
                        QTimer.singleShot(0, lambda: self._mostrar_banner_update(msg))
                    return

                available, _, remote = is_update_available()
                if available:
                    msg = f"Nueva versión {remote} — descargando en segundo plano..."
                    QTimer.singleShot(0, lambda: self._mostrar_banner_update(msg))
                    threading.Thread(
                        target=download_and_stage_update,
                        kwargs={
                            "progress_callback": lambda m: QTimer.singleShot(
                                0,
                                lambda text=m: self._mostrar_banner_update(text),
                            )
                        },
                        daemon=True,
                    ).start()
                    return

                from src.updater.github_updater import verificar_actualizaciones_github
                res = verificar_actualizaciones_github(dry_run=True)
                if res and res.hay_cambios and not getattr(sys, "frozen", False):
                    n = len(res.actualizados)
                    canal = res.canal.upper()
                    ver = res.version_nueva
                    msg = (
                        f"Nueva versión {ver} ({canal}) desde la nube — "
                        f"{n} módulo{'s' if n != 1 else ''} listo{'s' if n != 1 else ''} para instalar"
                    )
                    self._origen_actualizacion = "github"
                    QTimer.singleShot(0, lambda: self._mostrar_banner_update(msg))
            except Exception as e:
                from src.logger import logger
                logger.error(f"Error buscando actualizaciones bg: {e}")
                
        threading.Thread(target=_check, daemon=True).start()

    def _mostrar_banner_update(self, mensaje: str):
        if hasattr(self, '_lbl_update_msg'):
            self._lbl_update_msg.setText(mensaje)
        if hasattr(self, '_update_banner'):
            self._posicionar_banner()
            self._update_banner.show()
            self._update_banner.raise_()

    def _instalar_actualizacion_rapida(self):
        """Descarga en segundo plano y aplica al reiniciar (estilo web app)."""
        from src.updater.silent_auto_updater import SilentUpdateWorker
        self._update_banner.hide()

        # Dialogo de progreso minimalista
        from PyQt6.QtWidgets import QProgressDialog
        dlg = QProgressDialog(
            "Descargando e instalando actualizacion...", None, 0, 0, self)
        dlg.setWindowTitle("Actualizando TPV Pro")
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(0)
        dlg.setValue(0)
        dlg.show()

        self._uw = SilentUpdateWorker(dry_run=False)

        def on_progreso(pct, msg):
            dlg.setLabelText(msg)
            QApplication.processEvents()

        def on_terminado(res):
            dlg.close()
            if res.hay_cambios:
                n = len(res.actualizados)
                ret = QMessageBox.information(
                    self, "\u2705 Actualizacion lista",
                    f"Se descargaron {n} paquete(s) correctamente.\n\n"
                    "Al reiniciar el programa se aplicará al instante, "
                    "como una web app.",
                    QMessageBox.Ok,
                )
                if res.necesita_reinicio:
                    ret2 = QMessageBox.question(
                        self, "Reiniciar ahora",
                        "\u00bfReiniciar ahora para aplicar la actualizacion?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if ret2 == QMessageBox.Yes:
                        QApplication.exit(99)
            else:
                QMessageBox.information(self, "Sin cambios",
                    "Ya estas en la ultima version.")

        self._uw.progreso.connect(on_progreso)
        self._uw.terminado.connect(on_terminado)
        self._uw.start()


    def _restore_user_role(self, screen_index: int):
        """Restaura el rol activo en config.current_user según la pantalla destino."""
        from src.config import config
        if screen_index == 0:
            # Volvemos al admin— buscamos el usuario admin en DB
            res = db_manager.execute_query(
                "SELECT id, username, rol FROM usuarios WHERE rol = 'admin' LIMIT 1")
            if res:
                config.current_user = {
                    "id":       res[0]['id'],
                    "username": res[0]['username'],
                    "role":     res[0]['rol'],
                }


    def _init_screens(self):
        """Inicializa el stack de pantallas con LAZY LOADING.

        Los widgets pesados (Admin, Jefe, Nexus, etc.) se instancian la primera
        vez que el usuario navega a ellos, en vez de todos al arrancar.
        Esto elimina el freeze del splash y reduce el RAM inicial.
        """
        # ── Placeholders para Lazy Loading ───────────────────────────────────
        # None = aún no instanciado; se crea en switch_tab() al primer acceso.
        # Los índices NUNCA cambian (contratos externos vigentes).
        class _Dead(QWidget):
            """Slot libre en el stacked widget — nunca se navega aquí."""
            pass

        # El stacked_widget necesita exactamente 20 slots fijos.
        # Usamos QWidget() vacíos como placeholder para los lazy.
        self.screens = [
            None,    # 0  — Admin0Dashboard          (lazy)
            None,    # 1  — Cajero                   (lazy)
            None,    # 2  — Admin1Inventario         (lazy)
            None,    # 3  — Admin2Ofertas            (lazy)
            None,    # 4  — Admin3Reportes           (lazy)
            None,    # 5  — Admin5Configuracion      (lazy)
            None,    # 6  — Admin6RedLan             (lazy)
            None,    # 7  — Admin7Cierre             (lazy)
            None,    # 8  — AdminEtiquetas           (lazy)
            None,    # 9  — JefeContabilidad         (lazy)
            None,    # 10 — Admin10MP                (lazy)
            None,    # 11 — Admin11Proveedores       (lazy)
            _Dead(), # 12 — [LIBRE]
            None,    # 13 — Admin13Hardware          (lazy)
            None,    # 14 — Admin14VentasDigitales   (lazy)
            _Dead(), # 15 — [LIBRE]
            _Dead(), # 16 — [LIBRE]
            None,    # 17 — AdminClientes            (lazy)
            None,    # 18 — NexusExtremeControl      (lazy)
            None,    # 19 — Jefe0Dashboard           (lazy)
            None,    # 20 — JefeReportes             (lazy)
            None,    # 21 — CarteleriaMain           (lazy)
            None,    # 22 — Admin15Carteleria        (lazy)
            None,    # 23 — JefeIAProactiva          (lazy)
        ]

        # Fábricas: callable que crea el widget cuando se necesita
        self._screen_factories = {
            0:  lambda: __import__('src.admin.admin0_dashboard',  fromlist=['Admin0Dashboard']).Admin0Dashboard(),
            1:  lambda: __import__('src.cajero.paso5_terminal', fromlist=['Paso5Terminal']).Paso5Terminal(),
            2:  lambda: __import__('src.admin.admin1_inventario', fromlist=['Admin1Inventario']).Admin1Inventario(),
            3:  lambda: __import__('src.admin.admin2_ofertas',    fromlist=['Admin2Ofertas']).Admin2Ofertas(),
            4:  lambda: __import__('src.admin.admin3_reportes',   fromlist=['Admin3Reportes']).Admin3Reportes(),
            5:  lambda: __import__('src.admin.admin5_configuracion', fromlist=['Admin5Configuracion']).Admin5Configuracion(),
            6:  lambda: __import__('src.admin.admin6_red_lan',    fromlist=['Admin6RedLan']).Admin6RedLan(),
            7:  lambda: __import__('src.admin.admin7_cierre',     fromlist=['Admin7Cierre']).Admin7Cierre(self),
            8:  lambda: __import__('src.admin.etiquetas.admin_etiquetas', fromlist=['AdminEtiquetas']).AdminEtiquetas(),
            9:  lambda: __import__('src.jefe.contabilidad.jefe_contabilidad',  fromlist=['JefeContabilidad']).JefeContabilidad(),
            10: lambda: __import__('src.admin.admin10_mp',        fromlist=['Admin10MP']).Admin10MP(),
            11: lambda: __import__('src.admin.admin11_proveedores', fromlist=['Admin11Proveedores']).Admin11Proveedores(),
            13: lambda: __import__('src.admin.admin13_hardware',  fromlist=['Admin13Hardware']).Admin13Hardware(),
            14: lambda: __import__('src.admin.admin14_ventas_digitales', fromlist=['Admin14VentasDigitales']).Admin14VentasDigitales(),
            17: lambda: __import__('src.admin.admin_clientes',    fromlist=['AdminClientes']).AdminClientes(),
            18: lambda: __import__('src.admin.admin7_nexus',      fromlist=['NexusExtremeControl']).NexusExtremeControl(),
            19: lambda: __import__('src.jefe.jefe0_dashboard',    fromlist=['Jefe0Dashboard']).Jefe0Dashboard(),
            20: lambda: __import__('src.jefe.reportes.reportes_main', fromlist=['ReportesMain']).ReportesMain(),
            21: lambda: __import__('src.carteleria.main_board', fromlist=['CarteleriaMain']).CarteleriaMain(),
            22: lambda: __import__('src.admin.admin15_carteleria', fromlist=['Admin15Carteleria']).Admin15Carteleria(),
            23: lambda: __import__('src.jefe.ia.jefe_ia_proactiva', fromlist=['JefeIAProactiva']).JefeIAProactiva(self),
        }

        # Añadir todos los slots al QStackedWidget
        # Los slots lazy arrancan como QWidget vacíos; se reemplazan en switch_tab
        for i, s in enumerate(self.screens):
            placeholder = s if s is not None else QWidget()
            self.stacked_widget.addWidget(placeholder)
            if s is None:
                # Guardar el placeholder para poder reemplazarlo luego
                self.stacked_widget.widget(i).setObjectName(f"_lazy_placeholder_{i}")

        # Paso5Terminal ahora se carga de manera lazy en _build_lazy_screen

    def _preload_qss_cache(self):
        """Lee ambos temas una sola vez al arrancar."""
        import os
        from src.utils.paths import get_resource_path
        for theme_file in ("styles.qss", "styles_light.qss"):
            if theme_file in _QSS_CACHE:
                continue
            # Check in src first, then src/ui_components
            qss_path = get_resource_path(os.path.join("src", theme_file))
            if not os.path.exists(qss_path):
                qss_path = get_resource_path(os.path.join("src", "ui_components", theme_file))
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    _QSS_CACHE[theme_file] = f.read()
            except Exception as e:
                print(f"Error precargando tema {theme_file}: {e}")
                _QSS_CACHE[theme_file] = ""

    def _pregwarm_screens_for_role(self, role: str):
        """Instancia módulos frecuentes en idle para que la 1ª navegación no congele."""
        if role == "admin":
            warm = (2, 3, 4, 5, 7, 10, 11)
        elif role == "jefe":
            warm = (9, 20, 18)
        else:
            return
        for idx in warm:
            if idx >= len(self.screens) or self.screens[idx] is not None:
                continue
            try:
                self._build_lazy_screen(idx)
                QApplication.processEvents()
            except Exception as e:
                logger.warning(f"Prewarm pantalla {idx} falló: {e}")

    @property
    def pantalla_ventas(self):
        """Lazy load de la terminal de ventas (Paso 5)"""
        if self.screens[1] is None:
            self._build_lazy_screen(1)
        return self.screens[1]

    def _apply_theme_for_index(self, index: int):
        """Solo reaplica QSS al cambiar oscuro↔claro; evita repintar todo en cada tab admin."""
        if index == 1:
            if hasattr(self, 'pantalla_ventas') and hasattr(self.pantalla_ventas, 'apply_theme'):
                self.setUpdatesEnabled(False)
                try:
                    self.pantalla_ventas.apply_theme()
                    if hasattr(self.pantalla_ventas, 'teclado_virtual') and hasattr(self.pantalla_ventas.teclado_virtual, 'apply_theme'):
                        self.pantalla_ventas.teclado_virtual.apply_theme()
                finally:
                    self.setUpdatesEnabled(True)
                    self.repaint()
            self._active_theme_file = "terminal_theme"
            return

        theme_file = "styles_light.qss"
        if theme_file == self._active_theme_file:
            return
        css = _QSS_CACHE.get(theme_file, "")
        if css:
            QApplication.instance().setStyleSheet(css)
        self._active_theme_file = theme_file

    def _schedule_cargar_datos(self, index: int):
        """Evita encolar cargar_datos() duplicados al hacer clic rápido entre módulos."""
        try:
            self._cargar_datos_timer.timeout.disconnect()
        except Exception:
            pass

        def _run():
            s = self.screens[index] if index < len(self.screens) else None
            if s is not None and hasattr(s, "cargar_datos"):
                s.cargar_datos()

        self._cargar_datos_timer.timeout.connect(_run)
        self._cargar_datos_timer.start(50)

    def _build_lazy_screen(self, index: int):
        """Instancia el widget real para `index` y lo registra en el stack.

        Reemplaza el placeholder vacío por el widget definitivo y aplica
        el tema + conecta señales. Llamado automáticamente desde switch_tab.
        """
        factory = self._screen_factories.get(index)
        if factory is None:
            return  # Slot libre (_Dead) o índice desconocido

        widget = factory()
        self.screens[index] = widget

        # Reemplazar placeholder en el QStackedWidget sin cambiar el índice
        old = self.stacked_widget.widget(index)
        self.stacked_widget.insertWidget(index, widget)
        self.stacked_widget.removeWidget(old)
        old.deleteLater()

        # Aplicar tema si corresponde
        if index not in (0, 1, 6, 12, 15, 16, 18, 19):
            try:
                from src.utils.theme_manager import theme_manager
                theme_manager.apply_to_admin(widget)
                theme_manager.theme_changed.connect(lambda t, w=widget: theme_manager.apply_to_admin(w))
            except Exception:
                pass

        self._connect_screen_signals(index, widget)

        # Conexiones especiales para Cajero (index 1)
        if index == 1:
            self.screens[1].request_admin_jump = self.jump_to_admin_secure
            self.screens[1].request_chatbot_toggle.connect(self._toggle_chatbot_overlay)

    def _connect_screen_signals(self, index: int, s):
        """Conecta las señales de navegación de un widget recién creado."""
        if hasattr(s, 'request_dashboard'):
            s.request_dashboard.connect(self._handle_global_dashboard_return)

        if hasattr(s, 'request_screen'):
            s.request_screen.connect(self.switch_tab)

        if hasattr(s, 'request_tab'):
            s.request_tab.connect(self._on_jefe_request_tab)

        # Conectar señales comunes si existen
        # Conectar señales comunes si existen
        if hasattr(s, 'request_logout'):
            try:
                s.request_logout.disconnect()
            except:
                pass
            s.request_logout.connect(self._logout_to_selector)
            try:
                s.request_logout.disconnect()
            except:
                pass
            s.request_logout.connect(self._logout_to_selector)

    def _handle_global_dashboard_return(self):
        from src.config import config
        if config.current_user and config.current_user.get('role') == 'jefe':
            self.switch_tab(19)
        else:
            self.switch_tab(0)

    def _init_shortcuts(self):
        # ── Pirámide de acceso F11 ───────────────────────────────────────
        from src.navegacion_f11.f11_escalation_manager import GestorEscaladaF11
        self.gestor_f11 = GestorEscaladaF11(self)
        self.btn_flotante = self.gestor_f11.btn_flotante

        self._sc_f3 = QShortcut(QKeySequence(Qt.Key_F3), self)
        self._sc_f3.setContext(Qt.ApplicationShortcut)
        self._sc_f3.activated.connect(self._handle_f3_logic)

        self._sc_f12 = QShortcut(QKeySequence(Qt.Key_F12), self)
        self._sc_f12.setContext(Qt.ApplicationShortcut)
        self._sc_f12.activated.connect(self._handle_f12_logic)

    def _handle_f3_logic(self):
        if self.stacked_widget.currentIndex() == 1: # Estamos en Ventas
            self.pantalla_ventas.abrir_historial_dia()
        elif config.current_user.get('role') == 'admin':
            self.switch_tab(4)

    def _handle_f12_logic(self):
        # Si estamos en el terminal de ventas, F12 abre la ventana de cobro/pagar
        if self.stacked_widget.currentIndex() == 1:
            self.pantalla_ventas.finalizar_venta()
        # Si estamos en el Dashboard de Admin, F12 va a Nexus Extreme (18)
        elif config.current_user.get('role') == 'admin':
            self.switch_tab(18)

    def jump_to_admin_secure(self):
        self.gestor_f11.jump_to_admin_secure()

    def handle_f11_global(self):
        self.gestor_f11.handle_f11_global()
        pass



    def _show_terminal_window(self):
        """Terminal TPV — kiosco: pantalla completa sin recrear la ventana (F11 intacto)."""
        self._kiosk_mode = True
        if not self.isFullScreen():
            self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def _restore_office_window(self):
        """Sale del kiosco cajero → ventana maximizada con barra (admin / jefe)."""
        self._kiosk_mode = False
        if self.isFullScreen():
            self.showNormal()
        self.showMaximized()
        self.raise_()
        self.activateWindow()

    def switch_tab(self, index):
        """Navega a la pantalla indicada por su índice en el QStackedWidget.

        Guards de seguridad:
          - El perfil JEFE nunca llega a screen 0 (Admin0Dashboard)
            EXCEPTO durante una escalada piramidal (_escalando=True).
          - Los slots libres (6, 12, 15, 16) redirigen al home del rol.
        """
        from src.config import config
        role = (config.current_user or {}).get('role', 'admin').lower()
        escalando = getattr(self, '_escalando', False)

        # Guard: jefe nunca va al dashboard del admin
        # (bypass durante escalada piramidal F11 Admin→Jefe y descenso)
        if role == 'jefe' and index == 0 and not escalando:
            index = 19

        # Guard: slots libres — redirigir al home del rol activo
        if index in (12, 15, 16):
            index = 19 if role == 'jefe' else 0

        hay_venta = self.pantalla_ventas.tabla.rowCount() > 0
        is_supervisor = getattr(self, '_supervisor_mode', False)
        
        if index == 1:
            self._supervisor_mode = False
            self.btn_flotante.hide()
            self._show_terminal_window()
            # Mostrar chatbot solo en Terminal de Ventas SI fue activado por el usuario
            if self.chatbot_overlay is not None and self._chatbot_active:
                self.chatbot_overlay.show()
                self.chatbot_overlay.raise_()
            # Refrescar datos y título del terminal al activarlo
            if hasattr(self.pantalla_ventas, 'refresh_terminal_data'):
                self.pantalla_ventas.refresh_terminal_data()
        elif index == 21:
            self._kiosk_mode = False
            self.btn_flotante.hide()
            
            # --- MODO BORDERLESS MAXIMIZED (PANTALLA SECUNDARIA) ---
            from src.utils.qt_compat import screen_count, screen_geometry_at

            # Cambiar flags oculta la ventana temporalmente
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
            self.setAttribute(Qt.WA_ShowWithoutActivating)

            if screen_count() > 1:
                screen_rect = screen_geometry_at(1)
            else:
                screen_rect = screen_geometry_at(0)
            if screen_rect is not None:
                self.setGeometry(screen_rect)
                
            self.showMaximized()
            self.show()
            
            if self.chatbot_overlay is not None:
                self.chatbot_overlay.hide()
                self.chatbot_overlay.cerrar_chat()
        elif index == 22:
            top_bar = getattr(self, 'top_bar', None)
            if top_bar is not None:
                top_bar.lbl_title.setText("🌟 CARTELERÍA / OFERTAS RELÁMPAGO")
                top_bar.show()
        elif index == 23:
            top_bar = getattr(self, 'top_bar', None)
            if top_bar is not None:
                top_bar.lbl_title.setText("🧠 IA PROACTIVA - CENTRO DE INTELIGENCIA")
                top_bar.show()
        else:
            # Mostrar si estamos fuera de ventas y HAY UNA VENTA PENDIENTE o es INTERVENCIÓN DE SUPERVISOR
            self.gestor_f11.update_floating_button_visibility(index, hay_venta, is_supervisor)
                
            # Ocultar chatbot en las demás pantallas
            if self.chatbot_overlay is not None:
                self.chatbot_overlay.hide()
                self.chatbot_overlay.cerrar_chat()  # Cerrar burbuja si quedó abierta

            self._restore_office_window()
        
        # ── Lazy Loading: instanciar el widget si es la primera visita ───────
        if self.screens[index] is None:
            self._build_lazy_screen(index)

        self.stacked_widget.setCurrentIndex(index)

        self._apply_theme_for_index(index)
        self._schedule_cargar_datos(index)

    def apply_roles(self):
        user = config.current_user
        if not user: return
        # Aceptar tanto 'rol' (DB) como 'role' (Config manual)
        role = (user.get("role") or user.get("rol") or "cajero").lower()
        # Cajero → terminal. Jefe → panel exclusivo (19). Admin → dashboard (0).
        if role == "cajero":
            self.switch_tab(1)
        elif role == "jefe":
            if self.screens[19] is None:
                self._build_lazy_screen(19)
            self.switch_tab(19)
            QTimer.singleShot(400, lambda: self._pregwarm_screens_for_role("jefe"))
        elif role == "carteleria":
            if hasattr(self, 'nav_bar_v3'): self.nav_bar_v3.hide()
            if hasattr(self, 'top_bar_v3'): self.top_bar_v3.hide()
            self.switch_tab(21)
        else:
            if self.screens[0] is None:
                self._build_lazy_screen(0)
            self.switch_tab(0)
            QTimer.singleShot(400, lambda: self._pregwarm_screens_for_role("admin"))

    def _on_jefe_request_tab(self, tab_index: int):
        """El jefe pide un tab específico del ERP contable (ej: 3 = Proveedores)."""
        # Asegurarse de que JefeContabilidad esté instanciado (lazy)
        if self.screens[9] is None:
            self._build_lazy_screen(9)
        cont_widget = self.screens[9]
        if cont_widget is None:
            return
        if hasattr(cont_widget, 'ir_a_tab'):
            if getattr(cont_widget, '_loaded', True):
                cont_widget.ir_a_tab(tab_index)
            else:
                QTimer.singleShot(600, lambda: cont_widget.ir_a_tab(tab_index))

    def _logout_to_selector(self):
        """Cierra la sesión activa y relanza el selector de perfiles.

        Comportamiento:
          - Admin  → logout() en Admin0Dashboard emite exit(888).
            Este método es llamado ADICIONALMENTE si Admin0Dashboard tiene
            request_logout (doble cobertura — no rompe nada).
          - Jefe   → Jefe0Dashboard.request_logout → este método → exit(99).

        El loop en main.py captura códigos 99 y 888 y relanza launch_app().
        """
        from src.config import config
        config.current_user = None
        QApplication.exit(99)



    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'marco_alerta'):
            self.marco_alerta.setGeometry(0, 0, self.width(), self.height())
        # Safely adjust overlay if it still exists
        try:
            if hasattr(self, 'overlay_transition') and self.overlay_transition and not self.overlay_transition.isHidden():
                self.overlay_transition.setGeometry(0, 0, self.width(), self.height())
        except RuntimeError:
            # The overlay widget was already deleted; ignore
            pass
        self.gestor_f11.update_floating_button_position(self.width(), self.height())
        self._posicionar_banner()

    def mostrar_alerta_perimetral(self, visible, modo="security"):
        if visible:
            import datetime
            ahora = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
            
            if modo == "security":
                self.lbl_watermark.setText("⚠️ CAJÓN ABIERTO ⚠️\nSIN AUTORIZACIÓN")
                self.lbl_watermark.setStyleSheet("font-size: 80px; font-weight: 900; color: rgba(255, 255, 255, 200); background: transparent; border: none; letter-spacing: 5px;")
                self.lbl_timestamp.setText(f"DETECCIÓN: {ahora}")
                self.marco_alerta.setStyleSheet("border: 30px solid #B91C1C; background: transparent;")
                self.blink_timer.start(400)
            else:
                # MODO INFO (MENOS INVASIVO)
                self.lbl_watermark.setText("📥 CAJÓN ABIERTO\nCIERRE PRONTO")
                self.lbl_watermark.setStyleSheet("font-size: 50px; font-weight: 900; color: rgba(30, 58, 138, 180); background: transparent; border: none;")
                self.lbl_timestamp.setText(f"Operación: {ahora}")
                self.marco_alerta.setStyleSheet("border: none; background: rgba(248, 250, 252, 100);")
                self.blink_timer.stop() # Sin parpadeo en modo info
            
            self.marco_alerta.show()
            self.marco_alerta.raise_()
        else:
            self.marco_alerta.hide()
            self.blink_timer.stop()
            # Restaurar visibilidad normal
            if hasattr(self.pantalla_ventas, 'lbl_terminal_title'):
                title = config.get('business_name', 'Punto de Venta [20.09.02]')
                self.pantalla_ventas.lbl_terminal_title.setText(title)

    def _toggle_chatbot_overlay(self):
        self._chatbot_active = not self._chatbot_active
        if self._chatbot_active:
            self.chatbot_overlay.actualizar_posicion()
            self.chatbot_overlay.abrir_y_desplegar()
        else:
            self.chatbot_overlay.cerrar_chat()
            QTimer.singleShot(300, self.chatbot_overlay.hide)

    def _toggle_blink_alerta(self):
        self._blink_state = not self._blink_state
        if self._blink_state:
            # ESTADO ROJO TOTAL
            self.marco_alerta.setStyleSheet("border: 60px solid #7F1D1D; background: rgba(185, 28, 28, 150);")
            if hasattr(self.pantalla_ventas, 'lbl_terminal_title'):
                self.pantalla_ventas.lbl_terminal_title.setText("🚨 ALERTA DE SEGURIDAD 🚨")
            try: import PyQt6.QtWidgets as qw; qw.QApplication.beep()
            except: pass
        else:
            self.marco_alerta.setStyleSheet("border: 40px solid #EF4444; background: transparent;")
            if hasattr(self.pantalla_ventas, 'lbl_terminal_title'):
                self.pantalla_ventas.lbl_terminal_title.setText("⚠️ SEGURIDAD ACTIVA ⚠️")
        
        self.marco_alerta.raise_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(qt_exec(app))