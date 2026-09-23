from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout

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
        self.setFixedHeight(124)
        self.setObjectName("TerminalCabecera")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 12, 36, 12)
        layout.setSpacing(28)

        self.bloque_estado = BloqueEstado(self)
        self.bloque_caja = BloqueCaja(self)
        self.zona_alertas = ZonaAlertas(self)
        self.etiqueta_titulo = BloqueTitulo(titulo_inicial, self)

        self.grupo = QFrame(self)
        self.grupo.setObjectName("TerminalCabeceraGrupo")
        grupo = QVBoxLayout(self.grupo)
        grupo.setContentsMargins(0, 0, 0, 0)
        grupo.setSpacing(4)
        self.grupo.setMinimumWidth(360)
        self.grupo.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        derecha = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        self.marco_titulo = QFrame(self)
        self.marco_titulo.setObjectName("TerminalCabeceraMarcoTitulo")
        self.marco_titulo.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        titulo_lay = QHBoxLayout(self.marco_titulo)
        titulo_lay.setContentsMargins(0, 0, 0, 0)

        self.marco_fecha = QFrame(self)
        self.marco_fecha.setObjectName("TerminalCabeceraMarcoFecha")
        self.marco_fecha.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        fecha_lay = QHBoxLayout(self.marco_fecha)
        fecha_lay.setContentsMargins(0, 0, 0, 0)

        self.columna_marca = QFrame(self)
        self.columna_marca.setObjectName("TerminalCabeceraMarca")
        self.columna_marca.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        marca = QVBoxLayout(self.columna_marca)
        marca.setContentsMargins(0, 0, 0, 0)
        marca.setSpacing(4)

        self.separador = QFrame(self)
        self.separador.setObjectName("TerminalCabeceraSeparador")
        self.separador.setFixedSize(1, 40)

        self.etiqueta_estado = self.bloque_estado.etiqueta_estado
        self.etiqueta_instalacion = self.bloque_estado.etiqueta_instalacion
        self.luz_indicadora = self.bloque_caja.luz_indicadora
        self.etiqueta_caja = self.bloque_caja.etiqueta_caja
        self.etiqueta_fecha = self.bloque_caja.etiqueta_fecha
        self.etiqueta_titulo.setWordWrap(False)
        self.etiqueta_titulo.setAlignment(derecha)
        self.etiqueta_titulo.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.etiqueta_fecha.setWordWrap(False)
        self.etiqueta_fecha.setAlignment(derecha)
        titulo_lay.addWidget(self.etiqueta_titulo)
        fecha_lay.addWidget(self.etiqueta_fecha)
        marca.addWidget(self.marco_titulo, 0, Qt.AlignmentFlag.AlignRight)
        marca.addWidget(self.marco_fecha, 0, Qt.AlignmentFlag.AlignRight)

        centro = Qt.AlignmentFlag.AlignVCenter
        grupo.addWidget(self.bloque_estado, 0, centro)
        grupo.addWidget(self.bloque_caja, 0, centro)
        layout.addWidget(self.grupo, 0, centro)
        layout.addStretch()
        layout.addWidget(self.zona_alertas, 0, centro)
        layout.addWidget(self.separador, 0, centro)
        layout.addWidget(self.columna_marca, 0, centro)

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
