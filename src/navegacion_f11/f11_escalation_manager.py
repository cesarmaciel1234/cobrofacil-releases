import time
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QObject

from src.utils.floating_widgets import BotonFlotanteRegreso
from src.config import config
from src.base_de_datos.database import db_manager
from src.utils.qt_compat import qt_exec

class GestorEscaladaF11(QObject):
    """
    Gestor que maneja la Pirámide de Escalada de Accesos de F11.
    Extraído de main_window.py para mayor modularidad.
    """
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        
        # Crear botón flotante
        self.btn_flotante = BotonFlotanteRegreso(self.main_window)
        self.btn_flotante.clicked_return.connect(self.return_to_terminal_refresh)
        self.btn_flotante.hide()
        
        # Registrar atajo global F11
        self._sc_f11 = QShortcut(QKeySequence(Qt.Key_F11), self.main_window)
        self._sc_f11.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._sc_f11.activated.connect(self.handle_f11_global)
        
        self._last_f11_ts = 0.0

    def update_floating_button_visibility(self, index: int, hay_venta: bool, is_supervisor: bool):
        """Llamar a este método al cambiar de pestaña."""
        if index in (1, 21):
            self.btn_flotante.hide()
        else:
            if hay_venta or is_supervisor:
                self.btn_flotante.show()
                self.btn_flotante.raise_()
            else:
                self.btn_flotante.hide()

    def update_floating_button_position(self, width: int, height: int):
        """Llamar a este método en el resizeEvent de main_window."""
        if self.btn_flotante.isVisible():
            self.btn_flotante.move(width - 100, 80)

    def jump_to_admin_secure(self):
        from src.inicio_y_perfiles.login_pantalla import LoginPantalla
        if qt_exec(LoginPantalla(role="admin", parent=self.main_window)):
            self.main_window._supervisor_mode = True
            self.btn_flotante.show()
            self.main_window.switch_tab(0)
            self.main_window.apply_roles()

    def handle_f11_global(self):
        """Sistema de escalada piramidal de acceso."""
        now = time.monotonic()
        if now - self._last_f11_ts < 0.4:
            return
        self._last_f11_ts = now

        from src.inicio_y_perfiles.login_pantalla import LoginPantalla
        _u = config.current_user or {}
        role = config.current_role

        if role == "cajero":
            self.main_window._prev_user_before_escalation = config.current_user.copy() if config.current_user else None

            dlg = LoginPantalla(role="admin", parent=self.main_window)
            if qt_exec(dlg):
                self.main_window.setUpdatesEnabled(False)
                try:
                    from src.cajero.cajero_activo import CajeroActivo
                    supervisor = config.current_user.get('username', 'admin')
                    cajero     = CajeroActivo.nombre
                    db_manager.execute_non_query(
                        "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones)"
                        " VALUES ('INTERVENCION', 0, ?, ?)",
                        (supervisor, f"Supervisor {supervisor} asiste a {cajero} (F11)")
                    )
                    
                    self.main_window._came_from_cajero  = True
                    self.main_window._supervisor_mode   = True
                    self.main_window._escalando = True
                    self.main_window.apply_roles()
                    self.main_window.switch_tab(0)  # IR A PANEL ADMIN
                    self.btn_flotante.show()
                    self.btn_flotante.raise_()
                finally:
                    self.main_window._escalando = False
                    self.main_window.setUpdatesEnabled(True)
            return

        if role == "admin":
            self.main_window._admin_user_before_escalation = config.current_user.copy() if config.current_user else None
            
            dlg = LoginPantalla(role="jefe", parent=self.main_window)
            if qt_exec(dlg):
                self.main_window.setUpdatesEnabled(False)
                try:
                    self.main_window._supervisor_mode = True
                    self.main_window._escalando = True
                    self.main_window.apply_roles()
                    # ELIMINADO: self.main_window.switch_tab(0) porque forcejeaba al Panel Admin. apply_roles ya rutea a Jefe.
                    self.btn_flotante.show()
                    self.btn_flotante.raise_()
                finally:
                    self.main_window._escalando = False
                    self.main_window.setUpdatesEnabled(True)
            return

        if self.main_window.isFullScreen():
            self.main_window.showMaximized()
        else:
            self.main_window.showFullScreen()

    def return_to_terminal_refresh(self):
        """Botón flotante — desciende UN nivel en la pirámide."""
        current = self.main_window.stacked_widget.currentIndex()

        if current == 19:
            self.main_window.setUpdatesEnabled(False)
            try:
                if hasattr(self.main_window, '_admin_user_before_escalation') and self.main_window._admin_user_before_escalation:
                    config.current_user = self.main_window._admin_user_before_escalation.copy()
                else:
                    self.main_window._restore_user_role(0)
                    
                self.main_window._escalando = True
                self.main_window.apply_roles()
                self.main_window._escalando = False
                
                if getattr(self.main_window, '_came_from_cajero', False):
                    self.main_window.switch_tab(1)
                else:
                    self.btn_flotante.show()
                    self.btn_flotante.raise_()
            finally:
                self.main_window.setUpdatesEnabled(True)

        elif getattr(self.main_window, '_came_from_cajero', False):
            self.main_window.setUpdatesEnabled(False)
            try:
                self.main_window._came_from_cajero  = False
                self.main_window._supervisor_mode   = False
                self.btn_flotante.hide()
                
                if hasattr(self.main_window, '_prev_user_before_escalation') and self.main_window._prev_user_before_escalation:
                    config.current_user = self.main_window._prev_user_before_escalation.copy()
                    
                if hasattr(self.main_window, 'pantalla_ventas'):
                    self.main_window.pantalla_ventas.refresh_terminal_data()
                
                self.main_window.apply_roles()
            finally:
                self.main_window.setUpdatesEnabled(True)
        else:
            self.main_window._came_from_cajero  = False
            self.main_window._supervisor_mode   = False
            self.btn_flotante.hide()
            self.main_window.switch_tab(1)
