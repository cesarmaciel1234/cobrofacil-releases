from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QSizePolicy
from PyQt6.QtCore import Qt

_ESTILO = """
QFrame#PanelTotales {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}
QLineEdit#TerminalScan {
    background: #FFFFFF;
    border: 2px solid #3B82F6;
    border-radius: 22px;
    padding: 10px 18px;
    font-size: 16px;
    font-weight: 600;
    color: #0F172A;
    min-height: 44px;
}
QLineEdit#TerminalScan:focus {
    border: 2px solid #2563EB;
    background: #F8FAFF;
}
QFrame#CajaResumen {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}
QFrame#CajaResumen QLabel[tipo="titulo"] {
    color: #64748B;
    font-weight: 800;
    font-size: 12px;
    border: none;
    background: transparent;
}
QFrame#CajaResumen QLabel[tipo="valor"] {
    color: #0F172A;
    font-weight: 800;
    font-size: 15px;
    border: none;
    background: transparent;
}
QFrame#CajaResumen QLabel#ValorTotal {
    color: #047857;
    font-size: 20px;
    font-weight: 900;
}
QFrame#CajaResumen QLabel#TituloCambio {
    color: #DC2626;
}
QFrame#CajaResumen QLabel[tipo="valor"][resaltado="true"] {
    color: #059669;
    font-size: 18px;
}
"""


class PanelDeTotales(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelTotales")
        self.setFixedHeight(118)
        self.setStyleSheet(_ESTILO)

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(14, 8, 14, 8)
        layout_principal.setSpacing(16)

        self.entrada_codigo = QLineEdit()
        self.entrada_codigo.setObjectName("TerminalScan")
        self.entrada_codigo.setPlaceholderText("Código o Producto (F1)...")
        self.entrada_codigo.setMinimumWidth(280)
        layout_principal.addWidget(self.entrada_codigo, 1)

        self.etiqueta_ahorro = QLabel("")
        self.etiqueta_ahorro.setObjectName("EtiquetaAhorro")
        self.etiqueta_ahorro.hide()

        self.etiqueta_total_grande = QLabel("")
        self.etiqueta_total_grande.setObjectName("TotalGrande")
        self.etiqueta_total_grande.hide()

        self.caja_resumen = QFrame()
        self.caja_resumen.setObjectName("CajaResumen")
        self.caja_resumen.setMinimumWidth(260)
        self.caja_resumen.setMaximumWidth(340)
        layout_resumen = QVBoxLayout(self.caja_resumen)
        layout_resumen.setContentsMargins(14, 8, 14, 8)
        layout_resumen.setSpacing(4)

        self.titulo_cant, self.valor_cant = self._crear_fila(layout_resumen, "ARTÍCULOS")
        self.titulo_total, self.valor_total = self._crear_fila(layout_resumen, "TOTAL")
        self.valor_total.setObjectName("ValorTotal")
        self.titulo_ahorro, self.valor_ahorro = self._crear_fila(layout_resumen, "AHORRO")
        self.titulo_pagos, self.valor_pagos = self._crear_fila(layout_resumen, "PAGOS")
        self.titulo_cambio, self.valor_cambio = self._crear_fila(layout_resumen, "CAMBIO")
        self.titulo_cambio.setObjectName("TituloCambio")

        for item in [self.titulo_ahorro, self.valor_ahorro]:
            item.hide()

        layout_principal.addWidget(self.caja_resumen)

    def _crear_fila(self, layout, titulo):
        fila = QHBoxLayout()
        fila.setSpacing(12)
        t = QLabel(titulo)
        v = QLabel("0")
        t.setProperty("tipo", "titulo")
        v.setProperty("tipo", "valor")
        v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        t.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        v.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        fila.addWidget(t)
        fila.addWidget(v)
        layout.addLayout(fila)
        return t, v

    def actualizar_estilo_cambio(self, es_resaltado=False):
        self.valor_cambio.setProperty("resaltado", "true" if es_resaltado else "false")
        self.valor_cambio.style().unpolish(self.valor_cambio)
        self.valor_cambio.style().polish(self.valor_cambio)
