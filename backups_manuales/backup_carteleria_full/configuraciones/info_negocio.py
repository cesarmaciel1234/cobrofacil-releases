from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal
from src.carteleria.theme import C_THEME, apply_apple_shadow
from src.carteleria.configuraciones.reloj_widget import RelojWidget
from src.carteleria.configuraciones.indicador_red_widget import IndicadorRedWidget

class InfoNegocio(QWidget):
    """
    Contenedor ultra-ligero que agrupa la cabecera:
    Logo + Indicador de Red + Reloj + Botón Vista
    """
    config_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C_THEME['surface']}; border: 1px solid {C_THEME['border']}; border-radius: 6px;")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo / Título
        self.logo = QLabel("Cargando...")
        self.logo.setStyleSheet(f"font-family: -apple-system; font-size: 26px; font-weight: 800; color: {C_THEME['text']}; background: transparent;")
        
        # Bloques de Lego extraidos
        self.indicador_red = IndicadorRedWidget(self)
        self.reloj = RelojWidget(self)
        
        # Botón estilo Apple
        self.btn_modo = QPushButton("    Siguiente Vista    ")
        self.btn_modo.setFixedSize(180, 40)
        self.btn_modo.setStyleSheet(f"background: #FFFFFF; color: {C_THEME['text']}; font-weight: 600; border-radius: 6px; border: 1px solid {C_THEME['border']};")
        apply_apple_shadow(self.btn_modo)
        
        # Ensamblaje Visual
        self.layout.addWidget(self.logo)
        self.layout.addStretch()
        self.layout.addWidget(self.indicador_red)
        self.layout.addSpacing(16)
        self.layout.addWidget(self.reloj)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.btn_modo)

    def actualizar_nombre(self, nombre):
        self.logo.setText(f"🛒 {nombre}")

    def on_heartbeat_terminal(self, origen):
        self.indicador_red.on_heartbeat_terminal(origen)
        
    def set_estado_red(self, estado: str, txt: str = ""):
        self.indicador_red.set_estado_red(estado, txt)

    def set_clima(self, icon_name, text):
        pass # Optional clima handling if needed in header