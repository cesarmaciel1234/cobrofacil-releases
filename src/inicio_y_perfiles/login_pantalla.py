from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                              QMessageBox, QFrame, QGraphicsDropShadowEffect, QComboBox,
                              QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QColor
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
    """PASO 3: LOGIN — Light Premium 2026."""
    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(520, 510)
        self._setup_ui()
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso3")
        except:
            pass

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        # Acento por rol
        if self.role == "admin":
            accent = "#10B981"
            accent_r, accent_g, accent_b = 16, 185, 129
            role_icon = "🛡️"
            role_label = "ADMINISTRADOR"
        elif self.role == "jefe":
            accent = "#F59E0B"
            accent_r, accent_g, accent_b = 245, 158, 11
            role_icon = "👑"
            role_label = "JEFE / DUEÑO"
        else:
            accent = "#3B82F6"
            accent_r, accent_g, accent_b = 59, 130, 246
            role_icon = "🛒"
            role_label = "CAJERO / POS"

        # Contenedor blanco sin bordes duros
        self.container = QFrame()
        self.container.setObjectName("LoginContainer")
        self.container.setStyleSheet(f"""
            QFrame#LoginContainer {{
                background: #FFFFFF;
                border-radius: 28px;
                border: none;
            }}
        """)

        outer_shadow = QGraphicsDropShadowEffect(self)
        outer_shadow.setBlurRadius(45)
        outer_shadow.setColor(QColor(accent_r, accent_g, accent_b, 35))
        outer_shadow.setOffset(0, 12)
        self.container.setGraphicsEffect(outer_shadow)
        root.addWidget(self.container)

        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Header (Integrado y transparente) ─────────────────────────────────
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
            }}
        """)
        header_lay = QVBoxLayout(header_frame)
        header_lay.setContentsMargins(0, 24, 0, 8)

        header_lbl = QLabel(f"🔐  AUTENTICACIÓN: {role_label}")
        header_lbl.setStyleSheet(f"""
            color: {accent};
            font-size: 10px; font-weight: 900; letter-spacing: 4px;
            font-family: 'Segoe UI', sans-serif;
            background: transparent; border: none;
        """)
        header_lbl.setAlignment(Qt.AlignCenter)
        header_lay.addWidget(header_lbl)
        main_lay.addWidget(header_frame)

        # ── Badge conexión (Píldora flotante centrada) ───────────────────────────
        if db_manager.is_master:
            badge_text = "⬡  Modo: LOCAL  ·  Base de datos activa"
            badge_bg    = "rgba(16,185,129,0.08)"
            badge_fg    = "#059669"
        else:
            badge_text = "⬡  Modo: LAN REMOTA  ·  PC Maestra conectada"
            badge_bg    = "rgba(245,158,11,0.08)"
            badge_fg    = "#D97706"

        badge_lbl = QLabel(badge_text)
        badge_lbl.setAlignment(Qt.AlignCenter)
        badge_lbl.setStyleSheet(f"""
            font-size: 9px; font-weight: 800; letter-spacing: 1px;
            color: {badge_fg};
            background: {badge_bg};
            border: none;
            border-radius: 8px;
            padding: 6px 16px;
            font-family: 'Segoe UI', sans-serif;
        """)
        
        badge_wrap = QHBoxLayout()
        badge_wrap.addStretch()
        badge_wrap.addWidget(badge_lbl)
        badge_wrap.addStretch()
        main_lay.addLayout(badge_wrap)

        # ── Content ────────────────────────────────────────────────────────────
        content = QVBoxLayout()
        content.setContentsMargins(48, 20, 48, 28)
        content.setSpacing(14)

        # Avatar
        avatar_lbl = QLabel(role_icon)
        avatar_lbl.setFixedSize(68, 68)
        avatar_lbl.setAlignment(Qt.AlignCenter)
        avatar_lbl.setStyleSheet(f"""
            font-size: 32px;
            background: rgba({accent_r},{accent_g},{accent_b},0.08);
            border: none;
            border-radius: 34px;
        """)
        avatar_wrap = QHBoxLayout()
        avatar_wrap.addStretch()
        avatar_wrap.addWidget(avatar_lbl)
        avatar_wrap.addStretch()
        content.addLayout(avatar_wrap)

        # Título
        title_lbl = QLabel("Identificación Segura")
        title_lbl.setStyleSheet("""
            font-size: 20px; font-weight: 900; color: #0F172A;
            font-family: 'Segoe UI', 'Outfit', sans-serif;
            background: transparent; border: none; letter-spacing: -0.3px;
        """)
        title_lbl.setAlignment(Qt.AlignCenter)
        content.addWidget(title_lbl)

        # ── Campo usuario ──────────────────────────────────────────────────────
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
                border: 1.5px solid #E2E8F0;
                border-radius: 16px;
                padding: 12px 16px;
                font-size: 14px;
                color: #1E293B;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
            }}
            QComboBox:focus, QLineEdit:focus {{
                border: 2px solid {accent};
                background: rgba({accent_r},{accent_g},{accent_b},0.04);
                color: #0F172A;
            }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{
                background: #FFFFFF;
                border: 1px solid #EEF2F8;
                border-radius: 12px;
                selection-background-color: rgba({accent_r},{accent_g},{accent_b},0.08);
                selection-color: #0F172A;
                font-size: 13px;
                color: #1E293B;
                padding: 6px;
            }}
        """
        self.txt_user.setStyleSheet(field_style)
        if self.role == "admin":
            self.txt_user.setCurrentText("admin")
        elif self.role == "jefe":
            index = self.txt_user.findText("jefe")
            if index >= 0:
                self.txt_user.setCurrentIndex(index)
            else:
                self.txt_user.setCurrentIndex(0 if self.txt_user.count() > 0 else -1)
        else:
            # Intenta seleccionar 'cajero' si existe, de lo contrario primer index
            index = self.txt_user.findText("cajero")
            if index >= 0:
                self.txt_user.setCurrentIndex(index)
            else:
                self.txt_user.setCurrentIndex(0 if self.txt_user.count() > 0 else -1)
        content.addWidget(self.txt_user)

        # ── Campo contraseña ───────────────────────────────────────────────────
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

        content.addSpacing(4)

        # ── Botón verificar ────────────────────────────────────────────────────
        btn_login = QPushButton("VERIFICAR CREDENCIALES")
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.setFixedHeight(50)
        btn_login.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgb({accent_r},{accent_g},{accent_b}),
                    stop:1 rgba({accent_r},{accent_g},{accent_b},0.85));
                color: white;
                font-size: 12px; font-weight: 900; letter-spacing: 2.5px;
                border-radius: 25px;
                border: none;
                font-family: 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({accent_r},{accent_g},{accent_b},1.0),
                    stop:1 rgba({accent_r},{accent_g},{accent_b},0.90));
            }}
            QPushButton:pressed {{
                background: rgba({accent_r},{accent_g},{accent_b},0.75);
            }}
        """)
        btn_shadow = QGraphicsDropShadowEffect(btn_login)
        btn_shadow.setBlurRadius(15)
        btn_shadow.setColor(QColor(accent_r, accent_g, accent_b, 60))
        btn_shadow.setOffset(0, 4)
        btn_login.setGraphicsEffect(btn_shadow)
        btn_login.clicked.connect(self.verificar)
        content.addWidget(btn_login)

        # ── Botón cancelar ─────────────────────────────────────────────────────
        btn_cancel = QPushButton("Cancelar y volver")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                color: #94A3B8; font-size: 11px; font-weight: 600;
                border: none; background: transparent;
                font-family: 'Segoe UI', sans-serif; padding: 6px;
            }
            QPushButton:hover { color: #EF4444; }
        """)
        btn_cancel.clicked.connect(self.reject)
        content.addWidget(btn_cancel)

        main_lay.addLayout(content)
        QTimer.singleShot(100, self.txt_pass.setFocus if self.txt_user.currentText() else self.txt_user.setFocus)

    def verificar(self):
        user = self.txt_user.currentText().strip()
        pwd  = self.txt_pass.text().strip()
        if not user or not pwd:
            return

        res = db_manager.execute_query(
            "SELECT id, username, password_hash, rol FROM usuarios WHERE username = ?", (user,))
        if not res:
            QMessageBox.critical(self, "Error", "Credenciales inválidas.")
            self.txt_pass.clear(); self.txt_pass.setFocus()
            return

        db_user  = res[0]
        user_rol = db_user['rol'].lower()

        # Verificar contraseña
        if hashlib.sha256(pwd.encode()).hexdigest() != db_user['password_hash']:
            QMessageBox.critical(self, "Error", "Credenciales inválidas.")
            self.txt_pass.clear(); self.txt_pass.setFocus()
            return

        # ── Tabla de roles permitidos por perfil de acceso ────────────────────
        # cajero → solo cajeros
        # admin  → solo admins
        # jefe   → solo jefes (el admin tiene su propio perfil separado)
        ACCESO = {
            "cajero": {"cajero"},
            "admin":  {"admin"},
            "jefe":   {"jefe"},
        }
        permitidos = ACCESO.get(self.role, {self.role})

        if user_rol not in permitidos:
            QMessageBox.critical(
                self, "Acceso Denegado",
                f"El usuario '{db_user['username']}' (rol: {user_rol.upper()})\n"
                f"no tiene permiso para acceder como {self.role.upper()}."
            )
            return

        # ── Sesión iniciada ───────────────────────────────────────────────────
        config.current_user = {
            "id":       db_user['id'],
            "username": db_user['username'],
            "role":     db_user['rol'],
        }
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.txt_pass.setFocus()
        self.txt_pass.selectAll()
