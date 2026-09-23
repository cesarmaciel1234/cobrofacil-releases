from PyQt6.QtCore import Qt
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
        self.setFixedHeight(168)
        self.setStyleSheet(ESTILO_BARRA)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(16)

        self.entrada_codigo = EntradaCodigo(self)
        self.etiqueta_total_grande = TotalGrande(self)
        self.etiqueta_ahorro = AhorroBanner(self)
        self.caja_resumen = CajaResumen(self)

        self._hay_ahorro = False
        self._ahorro_en_zoom = False
        layout.addWidget(self.entrada_codigo, stretch=0, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.etiqueta_total_grande, stretch=2)
        layout.addWidget(self.etiqueta_ahorro, stretch=0)
        layout.addWidget(self.caja_resumen, stretch=0)
        self.repartir_centro(False)

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

    def repartir_centro(self, hay_ahorro: bool):
        """Sin ahorro el total usa todo el centro. Con ahorro, se parte en dos."""
        self._hay_ahorro = hay_ahorro
        lay = self.layout()
        i_total = lay.indexOf(self.etiqueta_total_grande)
        i_ahorro = lay.indexOf(self.etiqueta_ahorro)
        self.etiqueta_total_grande.setMinimumWidth(0)
        self.etiqueta_ahorro.setMinimumWidth(0)
        if hay_ahorro:
            lay.setStretch(i_total, 1)
            lay.setStretch(i_ahorro, 1)
        else:
            lay.setStretch(i_total, 2)
            lay.setStretch(i_ahorro, 0)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self.ajustar_cuerpo)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ajustar_cuerpo()

    def ajustar_cuerpo(self):
        """El número entra en el ancho real. La altura de la barra no cambia."""
        if self._hay_ahorro:
            self._encajar(self.etiqueta_total_grande, 56, "#15803D")
            if not self._ahorro_en_zoom:
                self._encajar(self.etiqueta_ahorro, 30, "#C2410C")
        else:
            self._encajar(self.etiqueta_total_grande, 84, "#15803D")

    def _encajar(self, etiqueta, techo, color):
        from PyQt6.QtGui import QFont, QFontMetrics

        ancho = max(60, etiqueta.width() - 4)
        texto = etiqueta.text() or "$0,00"
        fuente = QFont(etiqueta.font())
        fuente.setWeight(QFont.Weight.ExtraBold)
        tam = techo
        while tam > 20:
            fuente.setPixelSize(tam)
            if QFontMetrics(fuente).horizontalAdvance(texto) <= ancho:
                break
            tam -= 1
        etiqueta.setStyleSheet(
            f"font-size: {tam}px; font-weight: 800; color: {color}; "
            "background: transparent; border: none; padding: 0px;"
        )
