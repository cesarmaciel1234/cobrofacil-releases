from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                              QMessageBox, QFrame, QGraphicsDropShadowEffect, QComboBox,
                              QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QColor
import hashlib
from src.config import config
from src.inicio_y_perfiles.logica.auth_controller import AuthController
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
        self.setFixedSize(520, 600) # Más alto para evitar que se aplaste
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
        self.container.setProperty("rol", self.role)
        
        outer_shadow = QGraphicsDropShadowEffect(self)
        outer_shadow.setBlurRadius(10) # Optimizado (antes 45)
        outer_shadow.setColor(QColor(accent_r, accent_g, accent_b, 35))
        outer_shadow.setOffset(0, 12)
        self.container.setGraphicsEffect(outer_shadow)
        root.addWidget(self.container)

        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Header (Integrado y transparente) ─────────────────────────────────
        header_frame = QFrame()
        header_frame.setObjectName("LoginHeader")
        header_lay = QVBoxLayout(header_frame)
        header_lay.setContentsMargins(0, 24, 0, 8)

        header_lbl = QLabel(f"🔐  AUTENTICACIÓN: {role_label}")
        header_lbl.setObjectName("LoginHeaderLbl")
        header_lay.addWidget(header_lbl, alignment=Qt.AlignCenter)
        main_lay.addWidget(header_frame)

        # ── Contenido Principal ──────────────────────────────────────────────
        content_lay = QVBoxLayout()
        content_lay.setContentsMargins(40, 20, 40, 40)
        content_lay.setSpacing(16)

        # Avatar / Icono Central
        avatar_lay = QHBoxLayout()
        
        # Badge
        badge_lbl = QLabel("ÁREA RESTRINGIDA")
        badge_lbl.setObjectName("LoginBadge")
        badge_lbl.setAlignment(Qt.AlignCenter)
        
        # Icono
        avatar_lbl = QLabel(role_icon)
        avatar_lbl.setObjectName("LoginAvatar")
        avatar_lbl.setAlignment(Qt.AlignCenter)
        
        avatar_lay.addStretch()
        v_avatar = QVBoxLayout()
        v_avatar.addWidget(badge_lbl, alignment=Qt.AlignCenter)
        v_avatar.addWidget(avatar_lbl, alignment=Qt.AlignCenter)
        avatar_lay.addLayout(v_avatar)
        avatar_lay.addStretch()
        content_lay.addLayout(avatar_lay)

        title_lbl = QLabel(f"Hola, {role_label.split()[0].title()}")
        title_lbl.setObjectName("LoginTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        content_lay.addWidget(title_lbl)
        content_lay.addSpacing(10)
        
        auth_controller = AuthController()

        # Selector de Usuario
        lbl_user = QLabel("SELECCIONA TU USUARIO")
        lbl_user.setObjectName("LoginFieldLbl")
        content_lay.addWidget(lbl_user)

        self.txt_user = ClickableComboBox()
        self.txt_user.setObjectName("LoginUserCb")
        self.txt_user.setCursor(Qt.PointingHandCursor)
        
        # Populate users
        try:
            users = auth_controller.get_users_by_role(self.role)
            self.txt_user.addItems(users)
        except Exception as e:
            print(f"Error cargando usuarios: {e}")
            
        content_lay.addWidget(self.txt_user)
        
        # Autoseleccionar el primer usuario si existe
        if self.txt_user.count() > 0:
            self.txt_user.setCurrentIndex(0)

        # Contraseña
        lbl_pass = QLabel("CONTRASEÑA")
        lbl_pass.setObjectName("LoginFieldLbl")
        content_lay.addWidget(lbl_pass)

        self.txt_pass = QLineEdit()
        self.txt_pass.setObjectName("LoginPass")
        self.txt_pass.setPlaceholderText("••••••••")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.returnPressed.connect(self.verificar)
        content_lay.addWidget(self.txt_pass)
        
        # Auto-cargar contraseña para admin si es el único y estamos en pruebas
        if self.role == "admin" and self.txt_user.currentText() == "admin":
            self.txt_pass.setText("admin")

        content_lay.addSpacing(15)

        # Botón Ingresar
        btn_login = QPushButton("INGRESAR")
        btn_login.setObjectName("BtnLogin")
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.setFixedHeight(48)
        
        btn_shadow = QGraphicsDropShadowEffect(btn_login)
        btn_shadow.setBlurRadius(15)
        btn_shadow.setColor(QColor(accent_r, accent_g, accent_b, 60))
        btn_shadow.setOffset(0, 4)
        btn_login.setGraphicsEffect(btn_shadow)
        btn_login.clicked.connect(self.verificar)
        content_lay.addWidget(btn_login)

        # Botón Cancelar
        btn_cancel = QPushButton("Cancelar y volver")
        btn_cancel.setObjectName("BtnLoginCancel")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        content_lay.addWidget(btn_cancel)

        main_lay.addLayout(content_lay)
    def verificar(self):
        user = self.txt_user.currentText().strip()
        pwd  = self.txt_pass.text().strip()
        if not user or not pwd:
            return

        auth_controller = AuthController()
        user_dict = auth_controller.authenticate(user, pwd)
        
        if not user_dict:
            QMessageBox.critical(self, "Error", "Credenciales inválidas.")
            self.txt_pass.clear(); self.txt_pass.setFocus()
            return
            
        # Si es correcto
        auth_controller.set_current_user(user_dict)
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso4")
        except: pass
        self.accept()
