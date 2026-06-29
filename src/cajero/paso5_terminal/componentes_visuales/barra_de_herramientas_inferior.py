from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal

# Importar los micro-componentes desde la carpeta desglosada
from .componentes_barra_inferior.boton_teclado import BotonTeclado
from .componentes_barra_inferior.boton_tema import BotonTema
from .componentes_barra_inferior.boton_espera import BotonEspera
from .componentes_barra_inferior.botones_atajos import BotonesAtajos
from .componentes_barra_inferior.boton_bloquear import BotonBloquear
from .componentes_barra_inferior.boton_chatbot import BotonChatbot

class BarraDeHerramientasInferior(QFrame):
    # Señales para comunicar las acciones al archivo principal
    teclado_presionado = pyqtSignal()
    tema_presionado = pyqtSignal()
    espera_presionado = pyqtSignal()
    tecla_f_presionada = pyqtSignal(str) # Envía 'F1', 'F3', etc.
    bloquear_presionado = pyqtSignal()
    chatbot_presionado = pyqtSignal()

    def __init__(self, mostrar_teclado=True, version_sistema="COBRO FACIL", parent=None):
        super().__init__(parent)
        self.setFixedHeight(55)
        
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 0, 5, 0)
        
        # --- Botón Teclado Virtual ---
        if mostrar_teclado:
            self.boton_teclado = BotonTeclado()
            self.boton_teclado.clicked.connect(self.teclado_presionado.emit)
            layout_principal.addWidget(self.boton_teclado)
            layout_principal.addSpacing(10)

        # --- Botón Cambio de Tema ---
        self.boton_tema = BotonTema()
        self.boton_tema.clicked.connect(self.tema_presionado.emit)
        layout_principal.addWidget(self.boton_tema)
        layout_principal.addSpacing(10)

        # --- Versión ---
        self.etiqueta_version = QLabel(f"🚀 {version_sistema}")
        self.etiqueta_version.setObjectName("TerminalVersion")
        self.etiqueta_version.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        layout_principal.addWidget(self.etiqueta_version)
        layout_principal.addSpacing(10)
        
        layout_principal.addStretch(1)

        # --- Botón Espera ---
        self.boton_espera = BotonEspera()
        self.boton_espera.clicked.connect(self.espera_presionado.emit)
        layout_principal.addWidget(self.boton_espera)
        
        layout_principal.addStretch(1)

        # --- Botones de atajos (F1, F2...) en scroll area ---
        self.scroll_atajos = BotonesAtajos()
        self.scroll_atajos.tecla_f_presionada.connect(self.tecla_f_presionada.emit)
        layout_principal.addWidget(self.scroll_atajos, stretch=2)
        layout_principal.addSpacing(10)
        
        # --- Botón Bloquear ---
        self.boton_bloquear = BotonBloquear()
        self.boton_bloquear.clicked.connect(self.bloquear_presionado.emit)
        layout_principal.addWidget(self.boton_bloquear)
        
        # --- Botón Chatbot ---
        self.boton_chatbot = BotonChatbot()
        self.boton_chatbot.clicked.connect(self.chatbot_presionado.emit)
        layout_principal.addWidget(self.boton_chatbot)

    def actualizar_texto_espera(self, texto: str):
        self.boton_espera.setText(texto)

    def set_tema_texto(self, texto: str):
        self.boton_tema.setText(texto)
