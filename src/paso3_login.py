from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect, QComboBox
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QColor
import hashlib
from src.config import config
from src.database import db_manager

class ClickableComboBox(QComboBox):
    """
    QComboBox especializado que abre el popup desplegable inmediatamente al hacer clic
    sobre su área de texto.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        # Filtro de eventos para capturar el click del mouse dentro de su caja de texto interna
        if self.lineEdit():
            self.lineEdit().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.lineEdit() and event.type() == QEvent.MouseButtonPress:
            self.showPopup()
        return super().eventFilter(obj, event)

class Paso3Login(QDialog):
    """
    PASO 3: LOGIN ELITE 2026
    Seguridad con estética Glassmorphism estilo iOS y sombras cinemáticas.
    """
    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 480)
        self.setup_ui()
        self.apply_glow()

    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(35)
        glow.setColor(QColor(30, 58, 138, 100))
        glow.setOffset(0, 5)
        self.container.setGraphicsEffect(glow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.container = QFrame()
        # Fondo esmerilado de cristal templado (Glassmorphism)
        self.container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255, 255, 255, 0.85), stop:1 rgba(239, 246, 255, 0.75));
                border-radius: 20px; 
                border: 1px solid rgba(255, 255, 255, 0.65);
            }
        """)
        layout.addWidget(self.container)
        
        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Header Glass Oscuro
        header = QLabel(f"🔐 AUTENTICACIÓN: {self.role.upper()}")
        header.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(30, 58, 138, 0.95), stop:1 rgba(17, 24, 39, 0.9));
            color: white; font-size: 11px; 
            font-weight: 900; letter-spacing: 3px; padding: 15px;
            border-top-left-radius: 19px; border-top-right-radius: 19px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
        """)
        header.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(header)

        content = QVBoxLayout()
        content.setContentsMargins(50, 30, 50, 40)
        content.setSpacing(20)

        # Icono de usuario
        lbl_icon = QLabel("👤")
        lbl_icon.setStyleSheet("font-size: 40px; border: none; background: transparent;")
        lbl_icon.setAlignment(Qt.AlignCenter)
        content.addWidget(lbl_icon)

        # Inputs esmerilados con estilo iPhone Glass
        self.txt_user = ClickableComboBox()
        # Cargar usuarios según rol (ocultando admin en el login de cajero)
        if self.role == "cajero":
            res_users = db_manager.execute_query("SELECT username FROM usuarios WHERE rol = 'cajero'")
        elif self.role == "admin":
            res_users = db_manager.execute_query("SELECT username FROM usuarios WHERE rol = 'admin'")
        else:
            res_users = db_manager.execute_query("SELECT username FROM usuarios WHERE rol = ? OR rol = 'admin'", (self.role,))
            
        if res_users:
            self.txt_user.addItems([row['username'] for row in res_users])
        self.txt_user.setPlaceholderText("Selecciona o escribe el usuario...")
        
        self.txt_user.setStyleSheet("""
            QComboBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.8), 
                    stop:0.46 rgba(255, 255, 255, 0.65), 
                    stop:0.47 rgba(255, 255, 255, 0.3), 
                    stop:1 rgba(255, 255, 255, 0.5)
                );
                border: 1px solid rgba(255, 255, 255, 0.7); 
                border-radius: 12px;
                padding: 15px; font-size: 14px; color: #1E293B; font-weight: bold;
            }
            QComboBox:focus { 
                border: 2px solid #3B82F6; 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(243, 248, 255, 0.95), 
                    stop:0.46 rgba(224, 237, 255, 0.85), 
                    stop:0.47 rgba(191, 219, 254, 0.55), 
                    stop:1 rgba(219, 234, 254, 0.75)
                );
            }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox QAbstractItemView {
                background: rgba(255, 255, 255, 0.95); 
                border: 1px solid rgba(226, 232, 240, 0.9);
                border-radius: 10px;
                selection-background-color: #EFF6FF; 
                selection-color: #1E3A8A;
                font-size: 14px;
            }
            QLineEdit {
                background: transparent; border: none; color: #1E293B; font-weight: bold;
            }
        """)
        
        if self.role == "admin": 
            self.txt_user.setCurrentText("admin")
        else:
            self.txt_user.setCurrentIndex(-1) # Vacío por defecto
            
        content.addWidget(self.txt_user)

        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Contraseña Operativa")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.8), 
                    stop:0.46 rgba(255, 255, 255, 0.65), 
                    stop:0.47 rgba(255, 255, 255, 0.3), 
                    stop:1 rgba(255, 255, 255, 0.5)
                );
                border: 1px solid rgba(255, 255, 255, 0.7); 
                border-radius: 12px;
                padding: 15px; font-size: 14px; color: #1E293B; font-weight: bold;
            }
            QLineEdit:focus { 
                border: 2px solid #3B82F6; 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(243, 248, 255, 0.95), 
                    stop:0.46 rgba(224, 237, 255, 0.85), 
                    stop:0.47 rgba(191, 219, 254, 0.55), 
                    stop:1 rgba(219, 234, 254, 0.75)
                );
            }
        """)
        self.txt_pass.returnPressed.connect(self.verificar)
        content.addWidget(self.txt_pass)

        # Botón de Login Estilo iOS Glass Azul
        btn_login = QPushButton("VERIFICAR CREDENCIALES")
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(30, 58, 138, 0.95), 
                    stop:0.46 rgba(26, 50, 117, 0.85), 
                    stop:0.47 rgba(17, 24, 39, 0.75), 
                    stop:1 rgba(26, 50, 117, 0.85)
                );
                color: white; font-size: 12px; font-weight: 900; letter-spacing: 2px;
                padding: 18px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(30, 58, 138, 1.0), 
                    stop:0.46 rgba(17, 24, 39, 0.95), 
                    stop:0.47 rgba(17, 24, 39, 0.85), 
                    stop:1 rgba(17, 24, 39, 0.95)
                );
                border-color: #3B82F6;
            }
        """)
        btn_login.clicked.connect(self.verificar)
        content.addWidget(btn_login)

        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 11px; border: none; background: transparent;")
        btn_cancel.clicked.connect(self.reject)
        content.addWidget(btn_cancel)

        main_lay.addLayout(content)
        QTimer.singleShot(100, self.txt_pass.setFocus if self.txt_user.currentText() else self.txt_user.setFocus)

    def verificar(self):
        user = self.txt_user.currentText().strip()
        pwd = self.txt_pass.text().strip()
        if not user or not pwd: return

        res = db_manager.execute_query("SELECT id, username, password_hash, rol FROM usuarios WHERE username = ?", (user,))
        if res:
            db_user = res[0]
            if hashlib.sha256(pwd.encode()).hexdigest() == db_user['password_hash']:
                if self.role == "cajero" and db_user['rol'].lower() == "admin":
                    QMessageBox.critical(self, "Acceso Denegado", "El usuario Administrador no está permitido en este acceso. Inicie desde el perfil correspondiente o F11.")
                    return
                if db_user['rol'].lower() != self.role.lower() and self.role != "any" and db_user['rol'].lower() != "admin":
                    QMessageBox.critical(self, "Acceso Denegado", f"No tienes permisos de {self.role.upper()}.")
                    return
                config.current_user = {"id": db_user['id'], "username": db_user['username'], "role": db_user['rol']}
                self.accept()
                return
        QMessageBox.critical(self, "Error", "Credenciales inválidas.")
        self.txt_pass.clear(); self.txt_pass.setFocus()
