from PyQt6.QtWidgets import QSplashScreen, QVBoxLayout, QLabel, QFrame, QProgressBar, QApplication
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap

class CobroFacilSplash(QSplashScreen):
    """
    Splash Screen MODERNA Y EFICIENTE (400x600).
    - Diseño Flat: Sin cálculos pesados de CPU.
    - Renderizado nativo vía QSS.
    """
    def __init__(self):
        # Crear un pixmap transparente como lienzo base
        pixmap = QPixmap(400, 600)
        pixmap.fill(Qt.GlobalColor.transparent)
        super().__init__(pixmap, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Configurar transparencia de la ventana
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Contenedor principal con diseño plano
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 2px solid #3B82F6;
                border-radius: 20px;
            }
        """)
        
        # Layout principal de la ventana
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.container)
        
        # Layout interno del contenedor
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setSpacing(20)
        
        # Logo - Escalado optimizado
        self.img_logo = QLabel()
        self.img_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(r"C:\Users\cesar\OneDrive\Desktop\tpv pro 2026\src\assets\pos_icon.png")
        self.img_logo.setPixmap(pix.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        layout.addWidget(self.img_logo)
        
        # Títulos
        self.lbl_title = QLabel("CAJAFACIL <font color='#60A5FA'>PRO</font>")
        self.lbl_title.setStyleSheet("color: white; font-size: 28px; font-weight: 900; border: none;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_title)
        
        layout.addStretch() # Espaciador flexible
        
        # Barra de progreso plana
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: #1E293B; border-radius: 4px; }
            QProgressBar::chunk { background-color: #3B82F6; border-radius: 4px; }
        """)
        layout.addWidget(self.progress_bar)
        
        # Etiqueta de estado
        self.lbl_status = QLabel("Iniciando motor industrial...")
        self.lbl_status.setStyleSheet("color: #94A3B8; font-size: 12px; border: none;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

    def update_status(self, text, progress_val=None):
        """Actualización ligera de UI."""
        self.lbl_status.setText(text)
        if progress_val is not None:
            self.progress_bar.setValue(progress_val)
        
        # Procesar eventos para mantener la fluidez sin colapsar el hilo
        app = QApplication.instance()
        if app:
            app.processEvents()