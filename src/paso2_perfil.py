from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

class ProfileCard(QPushButton):
    def __init__(self, color, hover_bg, parent=None):
        super().__init__(parent)
        self.color = color
        self.hover_bg = hover_bg
        self.is_active = False
        
        # Sombra suave inicial (iOS Float Style)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 20))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)

    def set_active(self, active):
        self.is_active = active
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        
        if active:
            self.shadow.setBlurRadius(28)
            r, g, b = self.hex_to_rgb(self.color)
            self.shadow.setColor(QColor(r, g, b, 75)) # Brillo del color del rol activo
            self.shadow.setOffset(0, 8)
        else:
            self.shadow.setBlurRadius(15)
            self.shadow.setColor(QColor(0, 0, 0, 20))
            self.shadow.setOffset(0, 4)

    def enterEvent(self, event):
        super().enterEvent(event)
        # Si no está activo, dar el efecto de flotación temporal en hover
        if not self.is_active:
            self.shadow.setBlurRadius(28)
            r, g, b = self.hex_to_rgb(self.color)
            self.shadow.setColor(QColor(r, g, b, 75))
            self.shadow.setOffset(0, 8)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        # Si no está activo, regresar al estado de reposo al salir
        if not self.is_active:
            self.shadow.setBlurRadius(15)
            self.shadow.setColor(QColor(0, 0, 0, 20))
            self.shadow.setOffset(0, 4)

    def hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

class Paso2Perfil(QDialog):
    """
    PASO 2: SELECCIÓN DE PERFIL ELITE 2026
    Tarjetas interactivas con glassmorphism estilo iOS y sombras de elevación dinámicas.
    Incluye navegación por teclado con flechas y enter.
    """
    perfil_seleccionado = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(650, 420)
        self.selected_index = 1 # Seleccionar por defecto "Cajero / POS" (el rol más común)
        self.setup_ui()
        self.apply_glow()
        self.update_selection_ui()

    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(0, 0, 0, 60))
        glow.setOffset(0, 5)
        self.container.setGraphicsEffect(glow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.container = QFrame()
        # Gradiente sutil para el fondo que resalta el efecto cristal de las tarjetas
        self.container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F8FAFC, stop:1 #EFF6FF);
                border-radius: 20px; 
                border: 1px solid #E2E8F0;
            }
        """)
        layout.addWidget(self.container)
        
        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        
        # Header esmerilado
        header = QLabel("IDENTIFICACIÓN DE ENTORNO")
        header.setStyleSheet("""
            background-color: rgba(248, 250, 252, 0.85); color: #64748B; font-size: 11px; 
            font-weight: 900; letter-spacing: 3px; padding: 20px;
            border-top-left-radius: 19px; border-top-right-radius: 19px;
            border-bottom: 1px solid rgba(226, 232, 240, 0.8);
        """)
        header.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(header)
        
        content = QVBoxLayout()
        content.setContentsMargins(40, 30, 40, 40)
        content.setSpacing(30)
        
        title = QLabel("Bienvenido, selecciona tu rol operativo")
        title.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E293B; border: none; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        content.addWidget(title)
        
        btns_lay = QHBoxLayout()
        btns_lay.setSpacing(30)
        
        # --- TARJETA ADMIN ---
        self.btn_admin = self.create_profile_card(
            "👔", "ADMINISTRADOR", "Gestión, Inventarios y Reportes", "#10B981"
        )
        self.btn_admin.clicked.connect(lambda: self.elegir("admin"))
        
        # --- TARJETA CAJERO ---
        self.btn_cajero = self.create_profile_card(
            "🛒", "CAJERO / POS", "Ventas rápidas y Cobro directo", "#3B82F6"
        )
        self.btn_cajero.clicked.connect(lambda: self.elegir("cajero"))
        
        btns_lay.addWidget(self.btn_admin)
        btns_lay.addWidget(self.btn_cajero)
        content.addLayout(btns_lay)
        
        main_lay.addLayout(content)
 
    def create_profile_card(self, icon, title, desc, color):
        # Seleccionar gradiente de hover / active según rol
        if color == "#10B981": # Admin (emerald/green)
            hover_bg = """
                stop:0 rgba(240, 253, 250, 0.95), 
                stop:0.46 rgba(204, 251, 241, 0.85), 
                stop:0.47 rgba(153, 246, 228, 0.55), 
                stop:1 rgba(204, 251, 241, 0.75)
            """
        else: # Cajero (blue)
            hover_bg = """
                stop:0 rgba(243, 248, 255, 0.95), 
                stop:0.46 rgba(224, 237, 255, 0.85), 
                stop:0.47 rgba(191, 219, 254, 0.55), 
                stop:1 rgba(219, 234, 254, 0.75)
            """

        btn = ProfileCard(color, hover_bg)
        btn.setFixedSize(250, 180)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.NoFocus) # Permitir que los eventos de teclado se gestionen en el diálogo principal
        
        # Aplicar el estilo Glassmorphism y el hover personalizado
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.8), 
                    stop:0.46 rgba(255, 255, 255, 0.65), 
                    stop:0.47 rgba(255, 255, 255, 0.3), 
                    stop:1 rgba(255, 255, 255, 0.5)
                );
                border: 1px solid rgba(255, 255, 255, 0.65); 
                border-radius: 22px;
            }}
            QPushButton[active="true"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, {hover_bg});
                border: 2.5px solid {color};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, {hover_bg});
                border: 2.5px solid {color};
            }}
        """)
        
        l = QVBoxLayout(btn)
        l.setContentsMargins(20, 20, 20, 20)
        l.setSpacing(5)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 40px; border: none; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        
        tit_lbl = QLabel(title)
        tit_lbl.setStyleSheet("font-size: 14px; font-weight: 900; color: #1E293B; border: none; background: transparent;")
        tit_lbl.setAlignment(Qt.AlignCenter)
        
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("font-size: 11px; color: #64748B; border: none; background: transparent;")
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        
        l.addWidget(icon_lbl)
        l.addWidget(tit_lbl)
        l.addWidget(desc_lbl)
        
        return btn

    def update_selection_ui(self):
        # Admin es index 0, Cajero es index 1
        self.btn_admin.set_active(self.selected_index == 0)
        self.btn_cajero.set_active(self.selected_index == 1)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            self.selected_index = 1 if self.selected_index == 0 else 0
            self.update_selection_ui()
            event.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.elegir("admin" if self.selected_index == 0 else "cajero")
            event.accept()
        else:
            super().keyPressEvent(event)

    def elegir(self, rol):
        self.perfil_seleccionado.emit(rol)
        self.accept()
