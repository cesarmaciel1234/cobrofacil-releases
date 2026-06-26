from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect, QLineEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QLinearGradient, QPalette, QBrush

class LicenciaPantalla(QDialog):
    """
    PASO 1: BOOT CINEMÁTICO ELITE 2026
    Interfaz de entrada de alta gama con estética Midnight Industrial.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(650, 790)
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
        layout.setContentsMargins(30, 30, 30, 30)
        
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
        main_lay.setContentsMargins(48, 48, 48, 48)
        main_lay.setSpacing(26)
        
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
        
        self.lbl_hwid = QLabel("")
        self.lbl_hwid.setStyleSheet("font-size: 12px; font-weight: bold; color: #FCD34D; border: none;")
        self.lbl_hwid.setAlignment(Qt.AlignCenter)
        self.lbl_hwid.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_hwid.hide()
        main_lay.addWidget(self.lbl_hwid)
        
        main_lay.addStretch()
        
        # Campo para clave de licencia (oculto por defecto)
        self.txt_license = QLineEdit()
        self.txt_license.setPlaceholderText("Ingrese clave de activación (ej: PRO-1234)")
        self.txt_license.setMinimumHeight(44)
        self.txt_license.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                color: white; font-size: 13px; font-weight: bold;
                padding: 12px 16px; border-radius: 8px; border: 1px solid #3B82F6;
            }
        """)
        self.txt_license.setAlignment(Qt.AlignCenter)
        self.txt_license.hide()
        main_lay.addWidget(self.txt_license)

        # Botón de Entrada Premium
        self.btn_enter = QPushButton("INICIAR TERMINAL")
        self.btn_enter.setCursor(Qt.PointingHandCursor)
        self.btn_enter.setMinimumHeight(48)
        self.btn_enter.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3B82F6, stop:1 #1D4ED8);
                color: white; font-size: 13px; font-weight: 900; letter-spacing: 2px;
                padding: 16px 20px; border-radius: 12px; border: none;
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
        
        # Botón de WhatsApp (Nuevo)
        self.btn_whatsapp = QPushButton("💬 Pedir Licencia Gratuita por WhatsApp")
        self.btn_whatsapp.setCursor(Qt.PointingHandCursor)
        self.btn_whatsapp.setMinimumHeight(44)
        self.btn_whatsapp.setStyleSheet("""
            QPushButton {
                background: #25D366;
                color: white; font-size: 13px; font-weight: 900;
                padding: 12px 16px; border-radius: 8px; border: none;
            }
            QPushButton:hover { background: #128C7E; }
        """)
        self.btn_whatsapp.clicked.connect(self._abrir_whatsapp)
        self.btn_whatsapp.hide()
        main_lay.addWidget(self.btn_whatsapp)

        # Advertencia de Bomba Nuclear (Oculta por defecto)
        self.lbl_nuke_warning = QLabel("☢️ ¡ADVERTENCIA CRÍTICA! ☢️\nAl 3er intento fallido el sistema se AUTO-DESTRUIRÁ.")
        self.lbl_nuke_warning.setAlignment(Qt.AlignCenter)
        self.lbl_nuke_warning.setWordWrap(True)
        self.lbl_nuke_warning.setMinimumHeight(96)
        self.lbl_nuke_warning.setStyleSheet("""
            font-size: 12px; font-weight: 900; color: #EF4444; 
            background: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; 
            border-radius: 8px; padding: 28px 24px; margin-top: 12px;
            line-height: 1.6;
        """)
        self.lbl_nuke_warning.hide()
        main_lay.addWidget(self.lbl_nuke_warning)

        # Footer
        self.lbl_foot = QLabel("Verificando integridad de datos...")
        self.lbl_foot.setStyleSheet("font-size: 9px; color: #475569; border: none;")
        self.lbl_foot.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(self.lbl_foot)

        self._check_status()

    def _abrir_whatsapp(self):
        import webbrowser
        hwid = self._get_hwid()
        # REEMPLAZA ESTE NÚMERO POR TU NÚMERO DE WHATSAPP REAL (con código de país ej: 591, 52, 54, etc sin el +)
        numero_whatsapp = "0000000000" 
        mensaje = f"Hola, quiero solicitar mi Licencia Gratuita para Cobro Fácil POS. Mi ID de máquina es: {hwid}"
        url = f"https://wa.me/{numero_whatsapp}?text={mensaje.replace(' ', '%20')}"
        webbrowser.open(url)

    def _get_hwid(self):
        import platform, socket
        import hashlib
        # Generar un ID único basado en el nombre de la PC y el sistema
        raw_id = f"{platform.node()}-{platform.machine()}-PUNPRO"
        hwid = hashlib.md5(raw_id.encode()).hexdigest()[:8].upper()
        return hwid

    def _generar_llave_valida(self, hwid):
        import hashlib, datetime
        # La llave cambia CADA MES. Así los obligamos a volver por otra.
        mes_actual = datetime.datetime.now().strftime("%Y-%m")
        secreto = f"{hwid}-{mes_actual}-ELITE2026-X"
        return "PRO-" + hashlib.md5(secreto.encode()).hexdigest()[:8].upper()

    def _check_status(self):
        from src.config import config
        import datetime
        
        hwid = self._get_hwid()

        install_date = config.get("install_date", "")
        if not install_date:
            install_date = datetime.datetime.now().isoformat()
            config.set("install_date", install_date)
            
        dt_install = datetime.datetime.fromisoformat(install_date)
        dias_usados = (datetime.datetime.now() - dt_install).days
        dias_restantes = 30 - dias_usados
        
        self.en_gracia = False
        if dias_restantes <= 0:
            dias_gracia_restantes = 3 + dias_restantes # 0 -> 3, -1 -> 2, -2 -> 1, -3 -> 0
            
            if dias_gracia_restantes > 0:
                self.lbl_sub.setText(f"RENOVACIÓN REQUERIDA - GRACIA: {dias_gracia_restantes} DÍAS")
                self.lbl_sub.setStyleSheet("font-size: 12px; font-weight: 700; color: #F59E0B; letter-spacing: 2px; border: none;") # Naranja
                self.lbl_hwid.setText(f"ID MÁQUINA: {hwid}")
                self.lbl_hwid.show()
                self.txt_license.show()
                self.txt_license.setPlaceholderText("Ingrese Token de Renovación Mensual")
                self.btn_whatsapp.show()
                self.btn_enter.setText("CONTINUAR (PERIODO DE GRACIA)")
                self.lbl_foot.setText("Mande un mensaje para renovar su mes de uso gratuito.")
                self.lbl_nuke_warning.show()
                self.en_gracia = True
            else:
                self.lbl_sub.setText("SISTEMA BLOQUEADO - REQUIERE RENOVACIÓN")
                self.lbl_sub.setStyleSheet("font-size: 12px; font-weight: 700; color: #EF4444; letter-spacing: 2px; border: none;") # Rojo
                self.lbl_hwid.setText(f"ID MÁQUINA: {hwid}")
                self.lbl_hwid.show()
                self.txt_license.show()
                self.txt_license.setPlaceholderText("Ingrese Token de Renovación Mensual")
                self.btn_whatsapp.show()
                self.btn_enter.setText("ACTIVAR MES")
                self.lbl_foot.setText("Bloqueo mensual. Contacte a soporte para obtener su token de este mes.")
                self.lbl_nuke_warning.show()
        else:
            self.lbl_sub.setText(f"MES ACTIVO ({dias_restantes} DÍAS RESTANTES)")
            self.btn_whatsapp.show() 
            self.btn_whatsapp.setText("💬 Contactar Soporte (WhatsApp)")
            self.lbl_foot.setText("Disfruta de tu mes gratuito. Apóyanos en redes sociales.")
            self.lbl_nuke_warning.hide()

    def verificar_acceso(self):
        from src.config import config
        from PyQt6.QtWidgets import QMessageBox
        
        if self.txt_license.isVisible():
            key = self.txt_license.text().strip().upper()
            
            # Si está en gracia y no puso llave, lo dejamos pasar
            if not key and getattr(self, 'en_gracia', False):
                self.accept()
                return
                
            hwid = self._get_hwid()
            llave_valida = self._generar_llave_valida(hwid)
            
            if key == llave_valida or key == "PRO-2026-MASTER": # Hardcoded master key for emergencies
                import datetime
                # Magia: Reseteamos la fecha de instalación al momento actual. Le damos 30 días más.
                config.set("install_date", datetime.datetime.now().isoformat())
                # Borramos la clave para que no se autovalide el próximo mes (aunque ya no se guarda, nos aseguramos)
                config.set("license_key", "")
                config.set("failed_token_attempts", 0) # Reseteamos los fallos
                
                QMessageBox.information(self, "Renovado", "¡Renovación Mensual exitosa! Disfrute de 30 días más.")
                self.accept()
            else:
                intentos = config.get("failed_token_attempts", 0) + 1
                config.set("failed_token_attempts", intentos)
                
                if intentos >= 3:
                    QMessageBox.critical(self, "ALERTA DE SEGURIDAD", "SISTEMA BLOQUEADO.\nSe superó el límite de intentos fallidos.\n\nEl sistema se cerrará.")
                    self._auto_destruir_y_salir()
                else:
                    restantes = 3 - intentos
                    msg = f"Token inválido. Intentos restantes: {restantes} antes del bloqueo total."
                    if getattr(self, 'en_gracia', False):
                        msg += "\n(Dejando en blanco puede usar su periodo de gracia)."
                    QMessageBox.warning(self, "Fallo de Seguridad", msg)
        else:
            # Si no está visible, es que está dentro de los 30 días.
            self.accept()

    def _auto_destruir_y_salir(self):
        import sys
        from PyQt6.QtWidgets import QApplication
        QApplication.exit(0)
        sys.exit(0)

def check_license_active():
    from src.config import config
    import datetime
    
    # Solo nos importa la fecha de instalación. Ya no hay clave permanente.
    install_date = config.get("install_date", "")
    if not install_date:
        return False # Force showing the dialog to initialize install date
        
    try:
        dt_install = datetime.datetime.fromisoformat(install_date)
        dias_usados = (datetime.datetime.now() - dt_install).days
        # Si usó MENOS O IGUAL a 30 días, pasa directo sin pantalla
        if dias_usados < 30:
            return True 
        # Si usó 30 o más, obligamos a devolver False para que se MUESTRE la pantalla
        # (Así verá la alerta de gracia o el bloqueo final).
    except:
        pass
        
    return False # Expired and no license

