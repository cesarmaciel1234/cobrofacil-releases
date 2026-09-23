from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout

from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.atajos import (
    BotonesAtajos,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.bloquear import (
    BotonBloquear,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.chatbot import (
    BotonChatbot,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.espera import (
    BotonEspera,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.teclado import (
    BotonTeclado,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.tema import (
    BotonTema,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.version import (
    EtiquetaVersion,
)


class BarraDeHerramientasInferior(QFrame):
    teclado_presionado = pyqtSignal()
    tema_presionado = pyqtSignal()
    espera_presionado = pyqtSignal()
    tecla_f_presionada = pyqtSignal(str)
    bloquear_presionado = pyqtSignal()
    chatbot_presionado = pyqtSignal()

    def __init__(self, mostrar_teclado=True, version_sistema="COBRO FACIL", parent=None):
        super().__init__(parent)
        self.setFixedHeight(55)

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 0, 5, 0)

        if mostrar_teclado:
            self.boton_teclado = BotonTeclado()
            self.boton_teclado.clicked.connect(self.teclado_presionado.emit)
            layout_principal.addWidget(self.boton_teclado)
            layout_principal.addSpacing(10)

        self.boton_tema = BotonTema()
        self.boton_tema.clicked.connect(self.tema_presionado.emit)
        layout_principal.addWidget(self.boton_tema)
        layout_principal.addSpacing(10)

        self.etiqueta_version = EtiquetaVersion(version_sistema)
        layout_principal.addWidget(self.etiqueta_version)
        layout_principal.addSpacing(10)

        layout_principal.addStretch(1)

        self.boton_espera = BotonEspera()
        self.boton_espera.clicked.connect(self.espera_presionado.emit)
        layout_principal.addWidget(self.boton_espera)

        layout_principal.addStretch(1)

        self.scroll_atajos = BotonesAtajos()
        self.scroll_atajos.tecla_f_presionada.connect(self.tecla_f_presionada.emit)
        layout_principal.addWidget(self.scroll_atajos, stretch=2)
        layout_principal.addSpacing(10)

        self.boton_bloquear = BotonBloquear()
        self.boton_bloquear.clicked.connect(self.bloquear_presionado.emit)
        layout_principal.addWidget(self.boton_bloquear)

        self.boton_chatbot = BotonChatbot()
        self.boton_chatbot.clicked.connect(self.chatbot_presionado.emit)
        layout_principal.addWidget(self.boton_chatbot)

    def actualizar_texto_espera(self, texto: str):
        self.boton_espera.setText(texto)

    def set_tema_texto(self, texto: str):
        self.boton_tema.setText(texto)
