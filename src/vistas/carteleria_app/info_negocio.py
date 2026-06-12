from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QTimer, QTime
from src.vistas.carteleria_app.theme import C_THEME, apply_apple_shadow

class InfoNegocio(QWidget):
    """
    Controla la barra superior (Título del negocio, Reloj y botón de cambio de vista)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo / Título
        self.logo = QLabel("Cargando...")
        self.logo.setStyleSheet(f"font-family: -apple-system; font-size: 26px; font-weight: 800; color: {C_THEME['text']}; background: transparent;")
        
        # Reloj
        self.lbl_reloj = QLabel("00:00:00")
        self.lbl_reloj.setStyleSheet(f"font-family: -apple-system; font-size: 26px; font-weight: 700; color: {C_THEME['blue']}; background: transparent;")
        
        # Timer reloj
        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self._actualizar_reloj)
        self.timer_reloj.start(1000)
        self._actualizar_reloj()
        
        # Botón estilo Apple
        self.btn_modo = QPushButton("    Siguiente Vista    ")
        self.btn_modo.setFixedSize(180, 40)
        self.btn_modo.setStyleSheet(f"background: rgba(255, 255, 255, 0.9); color: {C_THEME['text']}; font-family: -apple-system; font-weight: 600; border-radius: 20px; border: 1px solid rgba(0,0,0,0.1);")
        apply_apple_shadow(self.btn_modo, blur=10, alpha=15, y_offset=2)
        
        self.layout.addWidget(self.logo)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.lbl_reloj)
        self.layout.addStretch()
        self.layout.addWidget(self.btn_modo)

    def _actualizar_reloj(self):
        hora_actual = QTime.currentTime().toString("HH:mm:ss")
        self.lbl_reloj.setText(hora_actual)

    def actualizar_nombre(self, nombre):
        if not nombre: nombre = "Carnicería"
        self.logo.setText(f"🥩 {nombre}")
