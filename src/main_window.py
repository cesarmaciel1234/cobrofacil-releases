import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame, QShortcut,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QApplication
)
from PyQt5.QtGui import QKeySequence, QFont, QColor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from src.admin.admin0_dashboard import Admin0Dashboard
from src.cajero.paso5_terminal import Paso5Terminal
from src.admin.admin1_inventario import Admin1Inventario
from src.admin.admin2_ofertas import Admin2Ofertas
from src.admin.admin3_reportes import Admin3Reportes
from src.admin.admin4_gastos import Admin4Gastos
from src.admin.admin5_configuracion import Admin5Configuracion
from src.admin.admin9_contabilidad import Admin9Contabilidad
from src.admin.admin10_mp import Admin10MP
from src.admin.etiquetas.admin_etiquetas import AdminEtiquetas
from src.admin.admin12_ai_boss import Admin12AIBoss
from src.admin.admin13_hardware import Admin13Hardware
from src.admin.admin11_proveedores import Admin11Proveedores
from src.admin.admin14_ventas_digitales import Admin14VentasDigitales
from src.admin.admin15_actualizaciones import Admin15Actualizaciones
from src.cajero.paso7_cierre import Paso7CierreCaja
from src.utils.floating_widgets import BotonFlotanteRegreso
from src.logger import logger
from src.config import config
from src.database import db_manager
from src.admin.admin7_cierre import Admin7Cierre

class ScifiReconstructionOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(0, 0, parent.width(), parent.height())
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # Fondo oscuro semi-transparente estilo vidrio soplado
        self.bg_overlay = QFrame(self)
        self.bg_overlay.setGeometry(0, 0, parent.width(), parent.height())
        self.bg_overlay.setStyleSheet("background-color: rgba(10, 15, 30, 0.95);")
        
        # 4 Paneles esquineros (símbolos de esquinas de ciencia ficción)
        self.panel_tl = QLabel("┌", self)
        self.panel_tr = QLabel("┐", self)
        self.panel_bl = QLabel("└", self)
        self.panel_br = QLabel("┘", self)
        
        # Estilo premium sci-fi para las esquinas (neon verde matrix)
        corner_style = "color: #10B981; font-size: 90px; font-weight: bold; background: transparent; border: none;"
        for p in [self.panel_tl, self.panel_tr, self.panel_bl, self.panel_br]:
            p.setStyleSheet(corner_style)
            p.setFixedSize(120, 120)
            p.setAlignment(Qt.AlignCenter)
            
        # Mensaje de carga holográfico central
        self.lbl_msg = QLabel("RECONSTRUYENDO TERMINAL INDUSTRIAL...\n[ SISTEMA DE SEGURIDAD ACTIVO ]", self)
        self.lbl_msg.setAlignment(Qt.AlignCenter)
        self.lbl_msg.setStyleSheet("""
            color: #34D399; 
            font-size: 15px; 
            font-weight: bold; 
            letter-spacing: 3px;
            font-family: 'Consolas', 'Lucida Console', monospace;
            background: transparent;
            border: none;
        """)
        
        # Sombra de brillo holográfico
        glow = QGraphicsDropShadowEffect(self.lbl_msg)
        glow.setBlurRadius(15); glow.setColor(QColor(16, 185, 129, 200)); glow.setOffset(0, 0)
        self.lbl_msg.setGraphicsEffect(glow)
        
        # Línea de barrido (scanline)
        self.scanline = QFrame(self)
        self.scanline.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(16,185,129,0), stop:0.5 rgba(16,185,129,0.8), stop:1 rgba(16,185,129,0)); border: none;")
        
        self.w = parent.width()
        self.h = parent.height()
        
        # Posicionar inicialmente en las esquinas exteriores
        self.panel_tl.move(0, 0)
        self.panel_tr.move(self.w - 120, 0)
        self.panel_bl.move(0, self.h - 120)
        self.panel_br.move(self.w - 120, self.h - 120)
        
        self.lbl_msg.setGeometry(0, self.h // 2 - 60, self.w, 120)
        self.scanline.setGeometry(0, 0, self.w, 8)
        
    def start_animation(self):
        from PyQt5.QtCore import QPropertyAnimation, QPoint, QParallelAnimationGroup, QEasingCurve, QRect
        
        # Centro exacto de convergencia
        cx = self.w // 2 - 60
        cy = self.h // 2 - 60
        
        self.anim_group = QParallelAnimationGroup(self)
        
        # 1. Esquinas al centro
        self.anim_tl = QPropertyAnimation(self.panel_tl, b"pos")
        self.anim_tl.setDuration(1000)
        self.anim_tl.setStartValue(QPoint(0, 0))
        self.anim_tl.setEndValue(QPoint(cx, cy))
        self.anim_tl.setEasingCurve(QEasingCurve.InOutQuint)
        
        self.anim_tr = QPropertyAnimation(self.panel_tr, b"pos")
        self.anim_tr.setDuration(1000)
        self.anim_tr.setStartValue(QPoint(self.w - 120, 0))
        self.anim_tr.setEndValue(QPoint(cx, cy))
        self.anim_tr.setEasingCurve(QEasingCurve.InOutQuint)
        
        self.anim_bl = QPropertyAnimation(self.panel_bl, b"pos")
        self.anim_bl.setDuration(1000)
        self.anim_bl.setStartValue(QPoint(0, self.h - 120))
        self.anim_bl.setEndValue(QPoint(cx, cy))
        self.anim_bl.setEasingCurve(QEasingCurve.InOutQuint)
        
        self.anim_br = QPropertyAnimation(self.panel_br, b"pos")
        self.anim_br.setDuration(1000)
        self.anim_br.setStartValue(QPoint(self.w - 120, self.h - 120))
        self.anim_br.setEndValue(QPoint(cx, cy))
        self.anim_br.setEasingCurve(QEasingCurve.InOutQuint)
        
        # 2. Barrido vertical
        self.anim_scan = QPropertyAnimation(self.scanline, b"geometry")
        self.anim_scan.setDuration(1000)
        self.anim_scan.setStartValue(QRect(0, 0, self.w, 8))
        self.anim_scan.setEndValue(QRect(0, self.h, self.w, 8))
        self.anim_scan.setEasingCurve(QEasingCurve.InOutSine)
        
        # 3. Desvanecimiento
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim_fade = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_fade.setDuration(350)
        self.anim_fade.setStartValue(1.0)
        self.anim_fade.setEndValue(0.0)
        
        self.anim_group.addAnimation(self.anim_tl)
        self.anim_group.addAnimation(self.anim_tr)
        self.anim_group.addAnimation(self.anim_bl)
        self.anim_group.addAnimation(self.anim_br)
        self.anim_group.addAnimation(self.anim_scan)
        
        def on_convergencia():
            self.lbl_msg.setText("✅ INTEGRIDAD DE INTERFAZ RECONSTRUIDA\n[ SISTEMA ONLINE ]")
            self.lbl_msg.setStyleSheet("""
                color: #FFFFFF; 
                font-size: 16px; 
                font-weight: bold; 
                letter-spacing: 3px;
                font-family: 'Consolas', 'Lucida Console', monospace;
                background: transparent;
                border: none;
            """)
            
            # Flash verde sutil de finalización
            self.bg_overlay.setStyleSheet("background-color: rgba(16, 185, 129, 0.4);")
            
            self.anim_fade.start()
            self.anim_fade.finished.connect(self.close)
            
        self.anim_group.finished.connect(on_convergencia)
        self.anim_group.start()
        
    def resizeEvent(self, event):
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.bg_overlay.setGeometry(0, 0, self.width(), self.height())
        self.w = self.width()
        self.h = self.height()
        self.lbl_msg.setGeometry(0, self.h // 2 - 60, self.w, 120)
        super().resizeEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CajaFacil Pro 2026 - Industrial POS")
        self.resize(1240, 820)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget); self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.btn_flotante = BotonFlotanteRegreso(self)
        self.btn_flotante.clicked_return.connect(self.return_to_terminal_refresh)
        self.btn_flotante.hide()
        self._supervisor_mode = False

        # Console y Thread de Instalación
        from src.ui.console_widget import ConsoleWidget
        from src.hardware.background_installer import BackgroundInstallerThread

        self.console = ConsoleWidget(self)
        self.main_layout.addWidget(self.console)

        self.installer_thread = BackgroundInstallerThread(self)
        # Conexiones de señales
        self.installer_thread.progress_update.connect(self.console.update_progress)
        self.installer_thread.progress.connect(self.console.append_message)
        self.installer_thread.error.connect(self.console.append_message)
        self.installer_thread.finished.connect(lambda: self.console.append_message("✅ Instalación completada"))

        # Importar gestión de cajón y otras utilidades
        from src.hardware.cash_drawer import drawer_manager

        # Restablecer cajón y cargar pantallas y atajos
        drawer_manager.reset_all()
        self._init_screens()
        self._init_shortcuts()
        self.apply_roles()
        self._init_global_alarm()
        self._init_security_monitor()
        self._init_update_banner()


        # Iniciar la instalación en segundo plano
        self.installer_thread.start()

        # Chequear actualizaciones 10 segundos después de que arranque la UI
        QTimer.singleShot(10000, self._chequear_actualizaciones_bg)

        """ Inicializa el sistema de latido para tolerancia a fallos LAN. """
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self._check_heartbeat)
        self.heartbeat_timer.start(5000) # Cada 5 segundos

    def _check_heartbeat(self):
        from src.database import db_manager
        from src.config import config
        import datetime
        from PyQt5.QtWidgets import QMessageBox
        import json
        import os
        from src.utils.paths import get_base_path

        # Si es Máster (local), enviar latido
        if db_manager.is_master:
            db_manager.actualizar_latido()
        else:
            # Si es Espectador (LAN), comprobar latido
            latido_str = db_manager.obtener_latido()
            if latido_str:
                try:
                    latido_dt = datetime.datetime.strptime(latido_str, "%Y-%m-%d %H:%M:%S")
                    ahora_utc = datetime.datetime.utcnow()
                    diff = (ahora_utc - latido_dt).total_seconds()
                    
                    if diff > 15: # 15 segundos sin latido
                        self.heartbeat_timer.stop()
                        msg = ("El servidor principal no responde (Latido perdido).\n\n"
                               "¿Desea convertir esta PC en el nuevo Máster?\n"
                               "Las nuevas ventas se guardarán localmente hasta que vuelva a conectarse a la red.")
                        
                        resp = QMessageBox.question(self, "Desconexión de Red Detectada", msg,
                                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                        
                        if resp == QMessageBox.Yes:
                            # Promover a Máster
                            base_path = get_base_path()
                            cfg_path = os.path.join(base_path, "config.json")
                            try:
                                with open(cfg_path, "r", encoding="utf-8") as f:
                                    cfg_data = json.load(f)
                                cfg_data["db_path"] = ""
                                with open(cfg_path, "w", encoding="utf-8") as f:
                                    json.dump(cfg_data, f, indent=4)
                                
                                QMessageBox.information(self, "Promovido", "La aplicación se reiniciará en Modo Máster Local.")
                                import sys
                                sys.exit(1) # O reiniciar suavemente, pero exit 1 reinicia si hay un wrapper, o lo cerramos
                            except Exception as e:
                                logger.error(f"Error asumiendo master: {e}")
                        else:
                            self.heartbeat_timer.start(5000)
                except Exception as e:
                    logger.error(f"Error procesando fecha de latido: {e}")

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
                from src.updater.update_client import (
                    verificar_actualizaciones, ResultadoActualizacion
                )
                res = verificar_actualizaciones(dry_run=True)
                if res.hay_cambios:
                    n = len(res.actualizados)
                    canal = res.canal.upper()
                    ver   = res.version_nueva
                    msg = (f"Nueva version {ver} ({canal}) — "
                           f"{n} modulo{'s' if n!=1 else ''} listo{'s' if n!=1 else ''} para instalar")
                    # Volver al hilo de Qt para actualizar la UI
                    QTimer.singleShot(0, lambda: self._mostrar_banner_update(msg))
            except Exception:
                pass  # Sin conexion o sin servidor — silencio total
        threading.Thread(target=_check, daemon=True).start()

    def _mostrar_banner_update(self, mensaje: str):
        if hasattr(self, '_lbl_update_msg'):
            self._lbl_update_msg.setText(mensaje)
        if hasattr(self, '_update_banner'):
            self._posicionar_banner()
            self._update_banner.show()
            self._update_banner.raise_()

    def _instalar_actualizacion_rapida(self):
        """Un clic: descarga, instala y ofrece reiniciar. Igual que el celular."""
        from src.admin.admin15_actualizaciones import UpdateWorker
        self._update_banner.hide()

        # Dialogo de progreso minimalista
        from PyQt5.QtWidgets import QProgressDialog
        dlg = QProgressDialog(
            "Descargando e instalando actualizacion...", None, 0, 0, self)
        dlg.setWindowTitle("Actualizando TPV Pro")
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(0)
        dlg.setValue(0)
        dlg.show()

        self._uw = UpdateWorker(canal="stable", dry_run=False)

        def on_progreso(pct, msg):
            dlg.setLabelText(msg)
            QApplication.processEvents()

        def on_terminado(res):
            dlg.close()
            if res.hay_cambios:
                n = len(res.actualizados)
                ret = QMessageBox.information(
                    self, "\u2705 Actualizacion instalada",
                    f"Se instalaron {n} modulo(s) correctamente.\n\n"
                    "\u26a0\ufe0f Reinicia el programa para que los cambios tomen efecto.",
                    QMessageBox.Ok
                )
                if res.necesita_reinicio:
                    ret2 = QMessageBox.question(
                        self, "Reiniciar ahora",
                        "\u00bfReiniciar ahora para aplicar todos los cambios?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if ret2 == QMessageBox.Yes:
                        QApplication.exit(99)
            else:
                QMessageBox.information(self, "Sin cambios",
                    "Ya estas en la ultima version.")

        self._uw.progreso.connect(on_progreso)
        self._uw.terminado.connect(on_terminado)
        self._uw.start()

    def return_to_terminal_refresh(self):
        """ Regresa al terminal y fuerza el refresco de datos. """
        self._supervisor_mode = False
        self.btn_flotante.hide()
        self.pantalla_ventas.refresh_terminal_data()
        self.switch_tab(1)

    def _init_screens(self):
        from src.admin.admin16_lan_connection import Admin16LANConnection
        self.pantalla_dashboard = Admin0Dashboard()
        self.pantalla_ventas = Paso5Terminal()
        self.pantalla_ventas.request_admin_jump = self.jump_to_admin_secure
        self.pantalla_inventario = Admin1Inventario()
        
        self.screens = [
            self.pantalla_dashboard,     # 0
            self.pantalla_ventas,        # 1
            self.pantalla_inventario,    # 2
            Admin2Ofertas(),            # 3
            Admin3Reportes(),           # 4
            Admin5Configuracion(),       # 5
            Admin7Cierre(self),          # 6
            Admin4Gastos(),             # 7
            AdminEtiquetas(),           # 8
            Admin9Contabilidad(),        # 9
            Admin10MP(),                # 10
            Admin11Proveedores(),        # 11
            Admin12AIBoss(),             # 12
            Admin13Hardware(),          # 13
            Admin14VentasDigitales(),   # 14
            Admin15Actualizaciones(),   # 15
            Admin16LANConnection()      # 16
        ]
        for s in self.screens:
            self.stacked_widget.addWidget(s)
            if hasattr(s, 'request_dashboard'):
                s.request_dashboard.connect(lambda: self.switch_tab(0))
            if hasattr(s, 'request_screen'):
                s.request_screen.connect(self.switch_tab)

    def _init_shortcuts(self):
        # F11: ÚNICO atajo para intervención de supervisor / pantalla completa
        QShortcut(QKeySequence("F11"), self).activated.connect(self.handle_f11_global)
        
        # F3: Historial rápido (Cajero) o Reportes (Admin)
        QShortcut(QKeySequence("F3"), self).activated.connect(self._handle_f3_logic)
        
        # F12: Cierre Z (Admin) o Cierre de Caja (Cajero) - BLINDADO
        QShortcut(QKeySequence("F12"), self).activated.connect(self._handle_f12_logic)

    def _handle_f3_logic(self):
        if self.stacked_widget.currentIndex() == 1: # Estamos en Ventas
            self.pantalla_ventas.abrir_historial_dia()
        elif config.current_user.get('role') == 'admin':
            self.switch_tab(4)

    def _handle_f12_logic(self):
        # Si estamos en el terminal de ventas, F12 SIEMPRE es para el cajero
        if self.stacked_widget.currentIndex() == 1:
            self.pantalla_ventas.abrir_cierre_caja()
        # Si estamos en el Dashboard de Admin, F12 va a Auditoría/Cierre Z
        elif config.current_user.get('role') == 'admin':
            self.switch_tab(6)

    def jump_to_admin_secure(self):
        from src.login_pantalla import LoginPantalla
        if LoginPantalla(role="admin").exec_():
            self._supervisor_mode = True
            self.btn_flotante.show()
            self.switch_tab(0)
            self.apply_roles()

    def handle_f11_global(self):
        if self.stacked_widget.currentIndex() == 1: 
            # Iniciar salto administrativo seguro
            from src.login_pantalla import LoginPantalla
            dlg = LoginPantalla(role="admin")
            if dlg.exec_():
                # Registro de Auditoría: Intervención de Supervisor
                from src.cajero.paso5_terminal import CajeroActivo
                supervisor = config.current_user.get('username', 'admin')
                cajero = CajeroActivo.nombre
                
                # Registrar apertura autorizada para inspección/reparación
                db_manager.execute_non_query(
                    "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones) VALUES ('INTERVENCION', 0, ?, ?)",
                    (supervisor, f"Supervisor {supervisor} asiste a {cajero} (F11)")
                )
                
                # Abrir cajón para mantenimiento de impresora/inspección
                from src.hardware.printer import printer_manager
                self.pantalla_ventas._apertura_autorizada = True 
                printer_manager.abrir_cajon()
                
                self._supervisor_mode = True
                self.btn_flotante.show()
                self.btn_flotante.raise_()
                self.switch_tab(0)
                self.apply_roles()
        else:
            if self.isFullScreen(): self.showMaximized()
            else: self.showFullScreen()

    def switch_tab(self, index):
        # Lógica de botón flotante: Solo aparece si NO estamos en el terminal (index 1)
        # O si hay productos pendientes de cobro/intervención / modo supervisor
        hay_venta = self.pantalla_ventas.tabla.rowCount() > 0
        is_supervisor = getattr(self, '_supervisor_mode', False)
        
        if index == 1:
            self._supervisor_mode = False
            self.btn_flotante.hide()
            self.showFullScreen()
            # Refrescar datos y título del terminal al activarlo
            if hasattr(self.pantalla_ventas, 'refresh_terminal_data'):
                self.pantalla_ventas.refresh_terminal_data()
        else:
            # Mostrar si estamos fuera de ventas y HAY UNA VENTA PENDIENTE o es INTERVENCIÓN DE SUPERVISOR
            if hay_venta or is_supervisor:
                self.btn_flotante.show()
                self.btn_flotante.raise_()
            else:
                self.btn_flotante.hide()
            self.showMaximized()
        
        self.stacked_widget.setCurrentIndex(index)
        
        # Cargas pesadas on-demand para mantener el 'Zero Lag'
        s = self.screens[index]
        if hasattr(s, 'cargar_datos'): s.cargar_datos()

    def apply_roles(self):
        user = config.current_user
        if not user: return
        role = user.get("role", "cajero").lower()
        # Si es cajero, va directo al terminal. Si es admin, al dashboard.
        self.switch_tab(1 if role != "admin" else 0)

    def iniciar_reconstruccion_scifi(self):
        """ Inicia la animación holográfica de reconstrucción de interfaz desde las esquinas al centro. """
        try:
            from src.utils.particle_transition import ParticleReconstructionOverlay
            self.overlay_transition = ParticleReconstructionOverlay(self)
            self.overlay_transition.show()
            self.overlay_transition.raise_()
        except Exception as e:
            from src.logger import logger
            logger.warning(f"No se pudo cargar la transición de partículas: {e}")
            self.overlay_transition = ScifiReconstructionOverlay(self)
            self.overlay_transition.show()
            self.overlay_transition.raise_()
            self.overlay_transition.start_animation()

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
        if self.btn_flotante.isVisible():
            self.btn_flotante.move(self.width() - 100, 80)
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

    def _toggle_blink_alerta(self):
        self._blink_state = not self._blink_state
        if self._blink_state:
            # ESTADO ROJO TOTAL
            self.marco_alerta.setStyleSheet("border: 60px solid #7F1D1D; background: rgba(185, 28, 28, 150);")
            if hasattr(self.pantalla_ventas, 'lbl_terminal_title'):
                self.pantalla_ventas.lbl_terminal_title.setText("🚨 ALERTA DE SEGURIDAD 🚨")
            try: import PyQt5.QtWidgets as qw; qw.QApplication.beep()
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
    sys.exit(app.exec_())
