from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                              QMessageBox, QFrame, QHBoxLayout, QCompleter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

if hasattr(Qt, 'AlignmentFlag'):
    Qt.AlignCenter = Qt.AlignmentFlag.AlignCenter
if hasattr(Qt, 'CursorShape'):
    Qt.PointingHandCursor = Qt.CursorShape.PointingHandCursor
if hasattr(Qt, 'WindowType'):
    Qt.FramelessWindowHint = Qt.WindowType.FramelessWindowHint
    Qt.Dialog = Qt.WindowType.Dialog
if hasattr(Qt, 'WidgetAttribute'):
    Qt.WA_TranslucentBackground = Qt.WidgetAttribute.WA_TranslucentBackground
if hasattr(Qt, 'MouseButton'):
    Qt.LeftButton = Qt.MouseButton.LeftButton

from src.inicio_y_perfiles.logica.auth_controller import AuthController


_ESTILO_CAMPOS = """
QLineEdit#LoginUserCb, QLineEdit#LoginPass {
    background: #FFFFFF;
    color: #0F172A;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 12px 16px;
    min-height: 52px;
    font-size: 16px;
    font-weight: 600;
    selection-background-color: #DBEAFE;
    selection-color: #0F172A;
}
QLineEdit#LoginUserCb:focus, QLineEdit#LoginPass:focus {
    border: 2px solid #3B82F6;
    background: #FFFFFF;
}
QLabel#LoginFieldLbl {
    color: #64748B;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 0.6px;
    background: transparent;
    border: none;
    padding: 0px;
    margin-top: 12px;
    margin-bottom: 2px;
}
QLabel#LoginTitle {
    color: #0F172A !important;
    font-size: 26px;
    font-weight: 900;
    background: transparent;
    border: none;
    letter-spacing: -0.5px;
}
QLabel#LoginBadge {
    color: #64748B;
    background: #F1F5F9;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 10px;
    font-weight: 800;
}
QLabel#LoginHeaderLbl {
    color: #0F172A !important;
    font-size: 13px;
    font-weight: 800;
}
QPushButton#BtnLogin {
    background: #10B981;
    color: #FFFFFF;
    border: none;
    border-radius: 14px;
    font-size: 16px;
    font-weight: 800;
}
QPushButton#BtnLogin:hover {
    background: #059669;
}
QPushButton#BtnLoginCancel {
    color: #64748B;
    background: transparent;
    border: none;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#BtnLoginCancel:hover {
    color: #0F172A;
    text-decoration: underline;
}
"""


class UsuarioCampo(QLineEdit):
    """Campo de texto + Tab completa el usuario y salta a contraseña."""

    def __init__(self, on_tab_siguiente, parent=None):
        super().__init__(parent)
        self._on_tab = on_tab_siguiente
        self._usuarios = []
        self.setPlaceholderText("Escribí el usuario")

    def set_usuarios(self, users):
        self._usuarios = list(users or [])
        # Autocompletado eliminado a peticion del usuario
    def completar(self):
        txt = (self.text() or "").strip()
        if not txt:
            return
        bajos = txt.lower()
        exactos = [u for u in self._usuarios if u.lower() == bajos]
        if exactos:
            self.setText(exactos[0])
            return
        prefijos = [u for u in self._usuarios if u.lower().startswith(bajos)]
        if prefijos:
            self.setText(prefijos[0])
            return
        contiene = [u for u in self._usuarios if bajos in u.lower()]
        if contiene:
            self.setText(contiene[0])

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.completar()
            if self._on_tab:
                self._on_tab()
            return
        super().keyPressEvent(event)


class LoginPantalla(QDialog):
    """PASO 3: LOGIN — Light Premium 2026."""
    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("theme", "light")
        self.setStyleSheet(
            "QDialog { background-color: #F8FAFC; }"
            "QFrame#LoginContainer {"
            " background-color: #FFFFFF; border-radius: 24px; border: 1px solid #E2E8F0;"
            "}"
            "QLabel { color: #0F172A; background: transparent; }"
        )
        if parent is not None:
            w = min(max(560, int(parent.width() * 0.32)), 720)
            h = min(max(640, int(parent.height() * 0.72)), 860)
        else:
            w, h = 600, 760
        self.setFixedSize(w, h)
        
        self._dragging = False
        self._drag_pos = QPoint()

        self._setup_ui()
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso3")
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        if self.role == "admin":
            role_icon = "🛡️"
            role_label = "ADMINISTRADOR"
        elif self.role == "jefe":
            role_icon = "👑"
            role_label = "JEFE / DUEÑO"
        else:
            role_icon = "🛒"
            role_label = "CAJERO / POS"

        self.container = QFrame()
        self.container.setObjectName("LoginContainer")
        self.container.setProperty("rol", self.role)
        self.container.setGraphicsEffect(None)
        root.addWidget(self.container)

        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        header_frame = QFrame()
        header_frame.setObjectName("LoginHeader")
        header_lay = QHBoxLayout(header_frame)
        header_lay.setContentsMargins(16, 16, 16, 4)

        spacer_left = QFrame()
        spacer_left.setFixedSize(28, 28)
        spacer_left.setStyleSheet("background: transparent; border: none;")
        header_lay.addWidget(spacer_left)
        header_lay.addStretch()

        header_lbl = QLabel(f"AUTENTICACIÓN: {role_label}")
        header_lbl.setObjectName("LoginHeaderLbl")
        header_lay.addWidget(header_lbl, alignment=Qt.AlignCenter)
        header_lay.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setObjectName("BtnCloseLogin")
        btn_close.setToolTip("Cerrar")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet("""
            QPushButton#BtnCloseLogin {
                background: rgba(0, 0, 0, 0.04);
                color: #64748B;
                border: none;
                border-radius: 14px;
                font-size: 14px;
                font-weight: 900;
            }
            QPushButton#BtnCloseLogin:hover {
                background: #FEE2E2;
                color: #DC2626;
            }
        """)
        btn_close.clicked.connect(self.reject)
        header_lay.addWidget(btn_close)
        main_lay.addWidget(header_frame)

        content_lay = QVBoxLayout()
        content_lay.setContentsMargins(40, 20, 40, 40)
        content_lay.setSpacing(8)

        badge_lbl = QLabel("ÁREA RESTRINGIDA")
        badge_lbl.setObjectName("LoginBadge")
        badge_lbl.setAlignment(Qt.AlignCenter)

        avatar_lbl = QLabel(role_icon)
        avatar_lbl.setObjectName("LoginAvatar")
        avatar_lbl.setAlignment(Qt.AlignCenter)

        avatar_lay = QHBoxLayout()
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
        content_lay.addSpacing(12)

        campos = QFrame()
        campos.setStyleSheet(_ESTILO_CAMPOS)
        campos_lay = QVBoxLayout(campos)
        campos_lay.setContentsMargins(0, 0, 0, 0)
        campos_lay.setSpacing(8)

        auth_controller = AuthController()

        lbl_user = QLabel("SELECCIONA TU USUARIO")
        lbl_user.setObjectName("LoginFieldLbl")
        campos_lay.addWidget(lbl_user)

        self.txt_user = UsuarioCampo(on_tab_siguiente=self._foco_password)
        self.txt_user.setObjectName("LoginUserCb")
        try:
            users = auth_controller.get_users_by_role(self.role)
            self.txt_user.set_usuarios(users)
        except Exception as e:
            print(f"Error cargando usuarios: {e}")
            self.txt_user.set_usuarios([])
        if self.txt_user.text():
            self.txt_user.selectAll()
        campos_lay.addWidget(self.txt_user)

        lbl_pass = QLabel("CONTRASEÑA")
        lbl_pass.setObjectName("LoginFieldLbl")
        campos_lay.addWidget(lbl_pass)

        self.txt_pass = QLineEdit()
        self.txt_pass.setObjectName("LoginPass")
        self.txt_pass.setPlaceholderText("Ingresá tu contraseña")
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.returnPressed.connect(self.verificar)
        campos_lay.addWidget(self.txt_pass)
        content_lay.addWidget(campos)

        content_lay.addSpacing(16)

        btn_login = QPushButton("INGRESAR")
        btn_login.setObjectName("BtnLogin")
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.setFixedHeight(52)
        btn_login.setGraphicsEffect(None)
        btn_login.clicked.connect(self.verificar)
        content_lay.addWidget(btn_login)

        btn_cancel = QPushButton("Cancelar y volver")
        btn_cancel.setObjectName("BtnLoginCancel")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        content_lay.addWidget(btn_cancel)

        main_lay.addLayout(content_lay)

    def _foco_password(self):
        self.txt_pass.setFocus()
        self.txt_pass.selectAll()

    def verificar(self):
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text().strip()
        if not user:
            QMessageBox.warning(self, "Acceso", "Seleccioná un usuario.")
            return
        if not pwd:
            QMessageBox.warning(self, "Acceso", "Ingresá la contraseña.")
            self.txt_pass.setFocus()
            return

        auth_controller = AuthController()
        user_dict = auth_controller.authenticate(user, pwd)

        if not user_dict:
            QMessageBox.critical(self, "Acceso Denegado", "Usuario o contraseña incorrectos.")
            self.txt_pass.clear()
            self.txt_pass.setFocus()
            return

        user_role = str(user_dict.get("rol") or user_dict.get("role") or "").strip().lower()
        target_role = str(self.role).strip().lower()

        if user_role != target_role:
            msg = (
                f"Estas credenciales pertenecen al perfil '{user_role.upper()}'.\n"
                f"Estás intentando ingresar al panel de '{target_role.upper()}'.\n\n"
                "Volvé al selector de perfiles y elegí la tarjeta correcta."
            )
            QMessageBox.warning(self, "Perfil Incorrecto", msg)
            self.txt_pass.clear()
            self.txt_pass.setFocus()
            return

        auth_controller.set_current_user(user_dict)
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso4")
        except Exception:
            pass
        self.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and getattr(self, '_drag_pos', None) is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
