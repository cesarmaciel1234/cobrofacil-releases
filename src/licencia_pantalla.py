from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect, QLineEdit
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QLinearGradient, QPalette, QBrush

class LicenciaPantalla(QDialog):
    """
    PASO 1: BOOT CINEMÁTICO ELITE 2026
    Interfaz de entrada de alta gama con estética Midnight Industrial.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 320)
        self.setup_ui()
        self.apply_glow()

    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(35)
        glow.setColor(QColor(30, 58, 138, 200)) # Azul Neón Profundo
        glow.setOffset(0, 0)
        self.container.setGraphicsEffect(glow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            QFrame#MainContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #0F172A);
                border: 1px solid #3B82F6;
                border-radius: 20px;
            }
        """)
        layout.addWidget(self.container)
        
        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(40, 40, 40, 40)
        main_lay.setSpacing(20)
        
        # Logo o Ícono Gigante
        lbl_icon = QLabel("💎")
        lbl_icon.setStyleSheet("font-size: 50px; background: transparent; border: none;")
        lbl_icon.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(lbl_icon)
        
        # Título
        lbl_tit = QLabel("CAJAFACIL PRO 2026")
        lbl_tit.setStyleSheet("""
            font-size: 24px; font-weight: 900; color: #F8FAFC; 
            letter-spacing: 4px; background: transparent; border: none;
        """)
        lbl_tit.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(lbl_tit)
        
        # Subtítulo
        self.lbl_sub = QLabel("SISTEMA DE GESTIÓN INDUSTRIAL")
        self.lbl_sub.setStyleSheet("font-size: 10px; font-weight: 700; color: #94A3B8; letter-spacing: 2px; border: none;")
        self.lbl_sub.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(self.lbl_sub)
        
        main_lay.addStretch()
        
        # Campo para clave de licencia (oculto por defecto)
        self.txt_license = QLineEdit()
        self.txt_license.setPlaceholderText("Ingrese clave de activación (ej: PRO-1234)")
        self.txt_license.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                color: white; font-size: 13px; font-weight: bold;
                padding: 10px; border-radius: 8px; border: 1px solid #3B82F6;
            }
        """)
        self.txt_license.setAlignment(Qt.AlignCenter)
        self.txt_license.hide()
        main_lay.addWidget(self.txt_license)

        # Botón de Entrada Premium
        self.btn_enter = QPushButton("INICIAR TERMINAL")
        self.btn_enter.setCursor(Qt.PointingHandCursor)
        self.btn_enter.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3B82F6, stop:1 #1D4ED8);
                color: white; font-size: 13px; font-weight: 900; letter-spacing: 2px;
                padding: 15px; border-radius: 12px; border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60A5FA, stop:1 #2563EB);
            }
            QPushButton:pressed {
                background: #1E40AF;
            }
        """)
        self.btn_enter.clicked.connect(self.verificar_acceso)
        main_lay.addWidget(self.btn_enter)
        
        # Footer
        self.lbl_foot = QLabel("Verificando integridad de datos...")
        self.lbl_foot.setStyleSheet("font-size: 9px; color: #475569; border: none;")
        self.lbl_foot.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(self.lbl_foot)

        self._check_status()

    def _check_status(self):
        from src.config import config
        import datetime
        
        license_key = config.get("license_key", "")
        if license_key == "PRO-2026-ELITE":
            self.lbl_sub.setText("VERSIÓN PRO ACTIVADA")
            return
            
        install_date = config.get("install_date", "")
        if not install_date:
            install_date = datetime.datetime.now().isoformat()
            config.set("install_date", install_date)
            
        dt_install = datetime.datetime.fromisoformat(install_date)
        dias_restantes = 15 - (datetime.datetime.now() - dt_install).days
        
        if dias_restantes <= 0:
            self.lbl_sub.setText("TRIAL EXPIRADO - INGRESE CLAVE")
            self.lbl_sub.setStyleSheet("font-size: 12px; font-weight: 700; color: #EF4444; letter-spacing: 2px; border: none;")
            self.txt_license.show()
            self.btn_enter.setText("ACTIVAR PRODUCTO")
            self.lbl_foot.setText("El periodo de prueba ha finalizado.")
        else:
            self.lbl_sub.setText(f"TRIAL ACTIVO ({dias_restantes} DÍAS RESTANTES)")
            self.lbl_foot.setText("Puede adquirir una licencia definitiva en cualquier momento.")

    def verificar_acceso(self):
        from src.config import config
        from PyQt5.QtWidgets import QMessageBox
        import datetime
        
        if self.txt_license.isVisible():
            key = self.txt_license.text().strip()
            if key == "PRO-2026-ELITE": # Hardcoded master key for now
                config.set("license_key", key)
                QMessageBox.information(self, "Activado", "¡Licencia PRO activada con éxito!")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Clave de licencia inválida.")
        else:
            # Si no está visible, es que está en Trial o ya está Pro.
            self.accept()

def check_license_active():
    from src.config import config
    import datetime
    
    # 1. Chequear clave de producto
    if config.get("license_key", "") == "PRO-2026-ELITE":
        return True
        
    # 2. Chequear periodo de gracia de 15 días
    install_date = config.get("install_date", "")
    if not install_date:
        return False # Force showing the dialog to initialize install date
        
    try:
        dt_install = datetime.datetime.fromisoformat(install_date)
        if (datetime.datetime.now() - dt_install).days <= 15:
            return True # Still in trial
    except:
        pass
        
    return False # Expired and no license

