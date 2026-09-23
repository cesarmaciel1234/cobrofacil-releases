from PyQt6.QtWidgets import QFrame, QHBoxLayout

from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.ahorro_banner.ahorro import (
    AhorroBanner,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.entrada_codigo.entrada import (
    EntradaCodigo,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.estilos import (
    ESTILO_BARRA,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.resumen.caja import (
    CajaResumen,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.total_grande.total import (
    TotalGrande,
)


class PanelDeTotales(QFrame):
    """Barra inferior: código, total verde, ahorro y resumen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelTotales")
        self.setFixedHeight(140)
        self.setStyleSheet(ESTILO_BARRA)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(20)

        self.entrada_codigo = EntradaCodigo(self)
        self.etiqueta_total_grande = TotalGrande(self)
        self.etiqueta_ahorro = AhorroBanner(self)
        self.caja_resumen = CajaResumen(self)

        layout.addWidget(self.entrada_codigo, stretch=4)
        layout.addWidget(self.etiqueta_total_grande, stretch=5)
        layout.addWidget(self.etiqueta_ahorro, stretch=4)
        layout.addWidget(self.caja_resumen, stretch=2)

        self.titulo_cant = self.caja_resumen.articulos.titulo
        self.valor_cant = self.caja_resumen.articulos.valor
        self.titulo_total = self.caja_resumen.total.titulo
        self.valor_total = self.caja_resumen.total.valor
        self.titulo_ahorro = self.caja_resumen.ahorro.titulo
        self.valor_ahorro = self.caja_resumen.ahorro.valor
        self.titulo_pagos = self.caja_resumen.pagos.titulo
        self.valor_pagos = self.caja_resumen.pagos.valor
        self.titulo_cambio = self.caja_resumen.cambio.titulo
        self.valor_cambio = self.caja_resumen.cambio.valor

    def actualizar_estilo_cambio(self, es_resaltado=False):
        self.caja_resumen.cambio.marcar_resaltado(es_resaltado)
