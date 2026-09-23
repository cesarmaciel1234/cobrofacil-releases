from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout


def _cargar(ruta, nombre):
    """Si una pieza no viajó en el ejecutable, la barra sigue y la venta abre."""
    try:
        modulo = __import__(ruta, fromlist=[nombre])
        return getattr(modulo, nombre)
    except ImportError:
        return None


BotonesAtajos = _cargar(
    "src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.atajos",
    "BotonesAtajos",
)
BotonBloquear = _cargar(
    "src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.bloquear",
    "BotonBloquear",
)
BotonChatbot = _cargar(
    "src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.chatbot",
    "BotonChatbot",
)
BotonEspera = _cargar(
    "src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.espera",
    "BotonEspera",
)
BotonTeclado = _cargar(
    "src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.teclado",
    "BotonTeclado",
)
BotonTema = _cargar(
    "src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.tema",
    "BotonTema",
)
EtiquetaVersion = _cargar(
    "src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.version",
    "EtiquetaVersion",
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
        self.setFixedHeight(70)
        self.setStyleSheet('''
            BarraDeHerramientasInferior {
                background-color: #F8FAFC;
                border-top: 1px solid #E2E8F0;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #475569;
                border-radius: 10px;
                color: #0F172A;
                font-weight: 800;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #334155;
            }
            QPushButton:pressed {
                background-color: #F1F5F9;
                border-color: #94A3B8;
            }
            QPushButton[is_shortcut="true"] {
                color: #1E3A8A;
                font-size: 15px;
                font-weight: 800;
            }
            QPushButton#BtnTeclado, QPushButton#BtnTheme, QPushButton#BtnEspera {
                padding: 0 16px;
                font-size: 14px;
                font-weight: 800;
                letter-spacing: 0.4px;
            }
            QPushButton#TerminalBtnBloquear {
                background-color: #15293C;
                border: none;
                border-radius: 8px;
            }
            QPushButton#TerminalBtnBloquear:hover {
                background-color: #1E3A4C;
            }
            QPushButton#TerminalBtnChatbot {
                background-color: #15803D;
                border: none;
                border-radius: 8px;
            }
            QPushButton#TerminalBtnChatbot:hover {
                background-color: #166534;
            }
            QLabel {
                font-size: 14px;
                font-weight: 800;
                color: #64748B;
            }
        ''')

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 0, 15, 0)

        self.boton_teclado = None
        if mostrar_teclado and BotonTeclado is not None:
            self.boton_teclado = BotonTeclado()
            self.boton_teclado.clicked.connect(self.teclado_presionado.emit)
            layout_principal.addWidget(self.boton_teclado)
            layout_principal.addSpacing(10)

        self.boton_tema = None
        if BotonTema is not None:
            self.boton_tema = BotonTema()
            self.boton_tema.clicked.connect(self.tema_presionado.emit)
            layout_principal.addWidget(self.boton_tema)
            layout_principal.addSpacing(10)

        self.etiqueta_version = None
        if EtiquetaVersion is not None:
            self.etiqueta_version = EtiquetaVersion(version_sistema)
            layout_principal.addWidget(self.etiqueta_version)
            layout_principal.addSpacing(10)

        layout_principal.addStretch(1)

        self.boton_espera = None
        if BotonEspera is not None:
            self.boton_espera = BotonEspera()
            self.boton_espera.clicked.connect(self.espera_presionado.emit)
            layout_principal.addWidget(self.boton_espera)

        layout_principal.addStretch(1)

        self.scroll_atajos = None
        if BotonesAtajos is not None:
            self.scroll_atajos = BotonesAtajos()
            self.scroll_atajos.tecla_f_presionada.connect(self.tecla_f_presionada.emit)
            layout_principal.addWidget(self.scroll_atajos, stretch=2)
            layout_principal.addSpacing(10)

        self.boton_bloquear = None
        if BotonBloquear is not None:
            self.boton_bloquear = BotonBloquear()
            self.boton_bloquear.clicked.connect(self.bloquear_presionado.emit)
            layout_principal.addWidget(self.boton_bloquear)

        self.boton_chatbot = None
        if BotonChatbot is not None:
            self.boton_chatbot = BotonChatbot()
            self.boton_chatbot.clicked.connect(self.chatbot_presionado.emit)
            layout_principal.addWidget(self.boton_chatbot)

    def actualizar_texto_espera(self, texto: str):
        if self.boton_espera is not None:
            self.boton_espera.setText(texto)

    def set_tema_texto(self, texto: str):
        if self.boton_tema is not None:
            self.boton_tema.setText(texto)
