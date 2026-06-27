from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                              QMessageBox, QFrame, QComboBox, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer, QEvent
import hashlib
from src.config import config
from src.base_de_datos.database import db_manager


class ClickableComboBox(QComboBox):
    """QComboBox que abre popup al hacer clic sobre el lineEdit."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        if self.lineEdit():
            self.lineEdit().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.lineEdit() and event.type() == QEvent.MouseButtonPress:
            self.showPopup()
        return super().eventFilter(obj, event)


class LoginPantalla(QDialog):
    """PASO 3: LOGIN — Light Premium 2026 (plano, sin capas 3D ni sombras)."""
    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role
        from src.utils.qt_dpi import scale_px, layout_scale, center_on_primary_screen

        self._ls = layout_scale()
        self.setWindowFlags(Qt.Dialog)
        self.setStyleSheet("QDialog { background-color: #E2E8F0; }")
        self.setFixedSize(scale_px(520, self._ls), scale_px(510, self._ls))
        self._setup_ui()
        try:
            center_on_primary_screen(self)
        except Exception:
            pass
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso3")
        except Exception:
            pass

    def _px(self, n):
        from src.utils.qt_dpi import scale_px
        return max(1, scale_px(n, self._ls))

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(self._px(20), self._px(20), self._px(20), self._px(20))

        if self.role == "admin":
            accent = "#10B981"
            accent_light = "#D1FAE5"
            role_icon = "🛡️"
            role_label = "ADMINISTRADOR"
        elif self.role == "jefe":
            accent = "#F59E0B"
            accent_light = "#FEF3C7"
            role_icon = "👑"
            role_label = "JEFE / DUEÑO"
        else:
            accent = "#3B82F6"
            accent_light = "#DBEAFE"
            role_icon = "🛒"
            role_label = "CAJERO / POS"

        self.container = QFrame()
        self.container.setObjectName("LoginContainer")
        self.container.setStyleSheet(f"""
            QFrame#LoginContainer {{
                background: #FFFFFF;
                border-radius: {self._px(28)}px;
                border: 2px solid {accent};
            }}
        """)
        root.addWidget(self.container)

        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        header_lay = QVBoxLayout(header_frame)
        header_lay.setContentsMargins(0, self._px(24), 0, self._px(8))

        header_lbl = QLabel(f"🔐  AUTENTICACIÓN: {role_label}")
        header_lbl.setStyleSheet(f"""
            color: {accent};
            font-size: {self._px(10)}px; font-weight: 900; letter-spacing: 4px;
            font-family: 'Segoe UI', sans-serif;
            background: transparent; border: none;
        """)
        header_lbl.setAlignment(Qt.AlignCenter)
        header_lay.addWidget(header_lbl)
        main_lay.addWidget(header_frame)

        if db_manager.is_master:
            badge_text = "⚡  Modo: LOCAL  ·  Base de datos activa"
            badge_bg = "#DCFCE7"
            badge_fg = "#059669"
        else:
            badge_text = "⚡  Modo: LAN REMOTA  ·  PC Maestra conectada"
            badge_bg = "#FEF3C7"
            badge_fg = "#D97706"

        badge_lbl = QLabel(badge_text)
        badge_lbl.setAlignment(Qt.AlignCenter)
        badge_lbl.setStyleSheet(f"""
            font-size: {self._px(9)}px; font-weight: 800; letter-spacing: 1px;
            color: {badge_fg};
            background: {badge_bg};
            border: 1px solid {badge_fg};
            border-radius: {self._px(8)}px;
            padding: {self._px(6)}px {self._px(16)}px;
            font-family: 'Segoe UI', sans-serif;
        """)

        badge_wrap = QHBoxLayout()
        badge_wrap.addStretch()
        badge_wrap.addWidget(badge_lbl)
        badge_wrap.addStretch()
        main_lay.addLayout(badge_wrap)

        content = QVBoxLayout()
        content.setContentsMargins(self._px(48), self._px(20), self._px(48), self._px(28))
        content.setSpacing(self._px(14))

        avatar_lbl = QLabel(role_icon)
        avatar_lbl.setFixedSize(self._px(68), self._px(68))
        avatar_lbl.setAlignment(Qt.AlignCenter)
        avatar_lbl.setStyleSheet(f"""
            font-size: {self._px(32)}px;
            background: {accent_light};
            border: 2px solid {accent};
            border-radius: {self._px(34)}px;
        """)
        avatar_wrap = QHBoxLayout()
        avatar_wrap.addStretch()
        avatar_wrap.addWidget(avatar_lbl)
        avatar_wrap.addStretch()
        content.addLayout(avatar_wrap)

        title_lbl = QLabel("Identificación Segura")
        title_lbl.setStyleSheet(f"""
            font-size: {self._px(20)}px; font-weight: 900; color: #0F172A;
            font-family: 'Segoe UI', sans-serif;
            background: transparent; border: none; letter-spacing: -0.3px;
        """)
        title_lbl.setAlignment(Qt.AlignCenter)
        content.addWidget(title_lbl)

        self.txt_user = ClickableComboBox()
        if self.role == "cajero":
            res_users = db_manager.execute_query("SELECT username FROM usuarios WHERE rol = 'cajero'")
        elif self.role == "admin":
            res_users = db_manager.execute_query("SELECT username FROM usuarios WHERE rol = 'admin'")
        elif self.role == "jefe":
            res_users = db_manager.execute_query("SELECT username FROM usuarios WHERE rol = 'jefe'")
        else:
            res_users = db_manager.execute_query(
                "SELECT username FROM usuarios WHERE rol = ?", (self.role,))

        if res_users:
            self.txt_user.addItems([row['username'] for row in res_users])
        self.txt_user.setPlaceholderText("Usuario operativo...")

        field_style = f"""
            QComboBox, QLineEdit {{
                background: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: {self._px(16)}px;
                padding: {self._px(12)}px {self._px(16)}px;
                font-size: {self._px(14)}px;
                color: #1E293B;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
            }}
            QComboBox:focus, QLineEdit:focus {{
                border: 2px solid {accent};
                background: #FFFFFF;
                color: #0F172A;
            }}
            QComboBox::drop-down {{ border: none; width: {self._px(28)}px; }}
            QComboBox QAbstractItemView {{
                background: #FFFFFF;
                border: 1px solid #EEF2F8;
                border-radius: {self._px(12)}px;
                selection-background-color: {accent_light};
                selection-color: #0F172A;
                font-size: {self._px(13)}px;
                color: #1E293B;
                padding: {self._px(6)}px;
            }}
        """
        self.txt_user.setStyleSheet(field_style)
        if self.role == "admin":
            self.txt_user.setCurrentText("admin")
        elif self.role == "jefe":
            index = self.txt_user.findText("jefe")
            self.txt_user.setCurrentIndex(index if index >= 0 else (0 if self.txt_user.count() else -1))
        else:
            index = self.txt_user.findText("cajero")
            self.txt_user.setCurrentIndex(index if index >= 0 else (0 if self.txt_user.count() else -1))
        content.addWidget(self.txt_user)

        self.txt_pass = QLineEdit()
        if self.role == "admin":
            self.txt_pass.setPlaceholderText("Contraseña Operativa")
        elif self.role == "jefe":
            self.txt_pass.setPlaceholderText("Contraseña Gerencial")
        else:
            self.txt_pass.setPlaceholderText("Contraseña Operativa")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setStyleSheet(field_style)
        self.txt_pass.returnPressed.connect(self.verificar)
        content.addWidget(self.txt_pass)

        content.addSpacing(self._px(4))

        btn_login = QPushButton("VERIFICAR CREDENCIALES")
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.setFixedHeight(self._px(50))
        btn_login.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                color: white;
                font-size: {self._px(12)}px; font-weight: 900; letter-spacing: 2.5px;
                border-radius: {self._px(25)}px;
                border: none;
                font-family: 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{ background-color: {accent}; }}
            QPushButton:pressed {{ background-color: #334155; }}
        """)
        btn_login.clicked.connect(self.verificar)
        content.addWidget(btn_login)

        btn_cancel = QPushButton("Cancelar y volver")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                color: #94A3B8; font-size: {self._px(11)}px; font-weight: 600;
                border: none; background: transparent;
                font-family: 'Segoe UI', sans-serif; padding: {self._px(6)}px;
            }}
            QPushButton:hover {{ color: #EF4444; }}
        """)
        btn_cancel.clicked.connect(self.reject)
        content.addWidget(btn_cancel)

        main_lay.addLayout(content)
        QTimer.singleShot(100, self.txt_pass.setFocus if self.txt_user.currentText() else self.txt_user.setFocus)

    def verificar(self):
        user = self.txt_user.currentText().strip()
        pwd = self.txt_pass.text().strip()
        if not user or not pwd:
            return

        res = db_manager.execute_query(
            "SELECT id, username, password_hash, rol FROM usuarios WHERE username = ?", (user,))
        if not res:
            QMessageBox.critical(self, "Error", "Credenciales inválidas.")
            self.txt_pass.clear()
            self.txt_pass.setFocus()
            return

        db_user = res[0]
        user_rol = db_user['rol'].lower()

        if hashlib.sha256(pwd.encode()).hexdigest() != db_user['password_hash']:
            QMessageBox.critical(self, "Error", "Credenciales inválidas.")
            self.txt_pass.clear()
            self.txt_pass.setFocus()
            return

        ACCESO = {
            "cajero": {"cajero"},
            "admin": {"admin"},
            "jefe": {"jefe"},
        }
        permitidos = ACCESO.get(self.role, {self.role})

        if user_rol not in permitidos:
            QMessageBox.critical(
                self, "Acceso Denegado",
                f"El usuario '{db_user['username']}' (rol: {user_rol.upper()})\n"
                f"no tiene permiso para acceder como {self.role.upper()}."
            )
            return

        config.current_user = {
            "id": db_user['id'],
            "username": db_user['username'],
            "role": db_user['rol'],
        }
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.txt_pass.setFocus()
        self.txt_pass.selectAll()
