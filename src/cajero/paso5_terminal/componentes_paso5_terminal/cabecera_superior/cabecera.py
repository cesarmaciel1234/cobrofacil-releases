from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from src.cajero.paso5_terminal.componentes_paso5_terminal.cabecera_superior.alertas import (
    ZonaAlertas,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.cabecera_superior.caja import (
    BloqueCaja,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.cabecera_superior.estado import (
    BloqueEstado,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.cabecera_superior.titulo import (
    BloqueTitulo,
)


class CabeceraSuperior(QFrame):
    """Arma el cabezal. Cada dato vive en su carpeta."""

    def __init__(self, titulo_inicial="Punto de Venta", parent=None):
        super().__init__(parent)
        self.setFixedHeight(128)
        self.setObjectName("TerminalCabecera")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(36, 16, 40, 16)
        layout.setSpacing(40)

        self.bloque_estado = BloqueEstado(self)
        self.bloque_caja = BloqueCaja(self)
        self.zona_alertas = ZonaAlertas(self)
        self.etiqueta_titulo = BloqueTitulo(titulo_inicial, self)

        self.grupo = QFrame(self)
        self.grupo.setObjectName("TerminalCabeceraGrupo")
        grupo = QVBoxLayout(self.grupo)
        grupo.setContentsMargins(18, 10, 22, 10)
        grupo.setSpacing(6)

        self.separador = QFrame(self)
        self.separador.setObjectName("TerminalCabeceraSeparador")
        self.separador.setFixedSize(1, 42)

        self.etiqueta_estado = self.bloque_estado.etiqueta_estado
        self.etiqueta_instalacion = self.bloque_estado.etiqueta_instalacion
        self.luz_indicadora = self.bloque_caja.luz_indicadora
        self.etiqueta_caja = self.bloque_caja.etiqueta_caja
        self.etiqueta_fecha = self.bloque_caja.etiqueta_fecha

        centro = Qt.AlignmentFlag.AlignVCenter
        grupo.addWidget(self.bloque_estado, 0, centro)
        grupo.addWidget(self.bloque_caja, 0, centro)
        layout.addWidget(self.grupo, 0, centro)
        layout.addWidget(self.etiqueta_fecha, 0, centro)
        layout.addStretch()
        layout.addWidget(self.zona_alertas, 0, centro)
        layout.addWidget(self.separador, 0, centro)
        layout.addWidget(self.etiqueta_titulo, 0, centro)

    def actualizar_reloj(self, momento=None):
        self.bloque_caja.actualizar_reloj(momento)

    def actualizar_datos_caja(self, texto_caja: str):
        self.etiqueta_caja.setText(texto_caja)

    def actualizar_estado(self, online, _):
        self.luz_indicadora.setProperty("estado", "normal" if online else "alerta")
        self.luz_indicadora.style().unpolish(self.luz_indicadora)
        self.luz_indicadora.style().polish(self.luz_indicadora)

    def actualizar_instalacion(self, texto_instalacion: str):
        self.etiqueta_instalacion.setText(texto_instalacion)

    def actualizar_titulo(self, titulo: str):
        self.etiqueta_titulo.setText(titulo)

    def establecer_color_luz(self, color_hex: str, border_color: str = "rgba(255,255,255,0.5)"):
        pass
