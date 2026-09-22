from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

_ESTILO = """
QFrame#PanelTotales {
    background: #FFFFFF;
    border-top: 1px solid #E2E8F0;
}
QLineEdit#TerminalScan {
    background: #F8FAFC;
    border: 2px solid #CBD5E1;
    border-radius: 12px;
    padding: 12px 18px;
    font-size: 26px;
    font-weight: 800;
    color: #0F172A;
    min-height: 60px;
}
QLineEdit#TerminalScan:focus {
    border: 2px solid #3B82F6;
    background: #FFFFFF;
}
QFrame#CajaResumen {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}
QFrame#CajaResumen QLabel[tipo="titulo"] {
    color: #64748B;
    font-weight: 800;
    font-size: 13px;
    border: none;
    background: transparent;
}
QFrame#CajaResumen QLabel[tipo="valor"] {
    color: #0F172A;
    font-weight: 900;
    font-size: 16px;
    border: none;
    background: transparent;
}
QFrame#CajaResumen QLabel#TituloCambio { color: #EF4444; }
QFrame#CajaResumen QLabel[tipo="valor"][resaltado="true"] {
    color: #059669;
    font-size: 18px;
}
"""


class PanelDeTotales(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelTotales")
        self.setFixedHeight(140)
        self.setStyleSheet(_ESTILO)

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(16, 12, 16, 12)
        layout_principal.setSpacing(16)

        self.entrada_codigo = QLineEdit()
        self.entrada_codigo.setObjectName("TerminalScan")
        self.entrada_codigo.setPlaceholderText("Código o Producto (F1)...")
        layout_principal.addWidget(self.entrada_codigo, stretch=2)

        self.etiqueta_ahorro = QLabel("")
        self.etiqueta_ahorro.setObjectName("EtiquetaAhorro")
        self.etiqueta_ahorro.hide()

        self.etiqueta_total_grande = QLabel("$0,00")
        self.etiqueta_total_grande.setObjectName("TotalGrande")
        self.etiqueta_total_grande.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.etiqueta_total_grande.setMinimumWidth(280)
        self.etiqueta_total_grande.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.etiqueta_total_grande.setAutoFillBackground(False)
        # Flat Premium Design: Sin sombras, bordes redondeados limpios, contraste alto.
        self.etiqueta_total_grande.setStyleSheet(
            "QLabel#TotalGrande {"
            " background-color: #FFFFFF; color: #16A34A;"
            " border: 2px solid #DCFCE7; border-radius: 12px;"
            " font-size: 56px; font-weight: 900; padding: 0 18px;"
            "}"
        )

        layout_totales = QHBoxLayout()
        layout_totales.addWidget(self.etiqueta_total_grande, 1)
        layout_totales.addWidget(self.etiqueta_ahorro)
        layout_principal.addLayout(layout_totales, stretch=3)

        self.caja_resumen = QFrame()
        self.caja_resumen.setObjectName("CajaResumen")
        self.caja_resumen.setMinimumWidth(240)
        layout_resumen = QVBoxLayout(self.caja_resumen)
        layout_resumen.setContentsMargins(16, 10, 16, 10)
        layout_resumen.setSpacing(4)

        self.titulo_cant, self.valor_cant = self._crear_fila(layout_resumen, "ARTÍCULOS")
        self.titulo_total, self.valor_total = self._crear_fila(layout_resumen, "TOTAL")
        self.titulo_ahorro, self.valor_ahorro = self._crear_fila(layout_resumen, "AHORRO")
        self.titulo_pagos, self.valor_pagos = self._crear_fila(layout_resumen, "PAGOS")
        self.titulo_cambio, self.valor_cambio = self._crear_fila(layout_resumen, "CAMBIO")
        self.titulo_cambio.setObjectName("TituloCambio")

        for item in [self.titulo_ahorro, self.valor_ahorro]:
            item.hide()

        layout_principal.addWidget(self.caja_resumen, stretch=1)

    def _crear_fila(self, layout, titulo):
        fila = QHBoxLayout()
        t = QLabel(titulo)
        v = QLabel("0")
        t.setProperty("tipo", "titulo")
        v.setProperty("tipo", "valor")
        v.setAlignment(Qt.AlignmentFlag.AlignRight)
        fila.addWidget(t)
        fila.addWidget(v)
        layout.addLayout(fila)
        return t, v

    def actualizar_estilo_cambio(self, es_resaltado=False):
        self.valor_cambio.setProperty("resaltado", "true" if es_resaltado else "false")
        self.valor_cambio.style().unpolish(self.valor_cambio)
        self.valor_cambio.style().polish(self.valor_cambio)
