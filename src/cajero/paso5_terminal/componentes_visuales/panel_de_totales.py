from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QSizePolicy
from PyQt6.QtCore import Qt
from src.config import config

class PanelDeTotales(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelTotales")
        self.setFixedHeight(140)
        
        # Se han movido los estilos a estilos.qss
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(10, 5, 10, 5)
        
        # --- Buscador ---
        self.entrada_codigo = QLineEdit()
        self.entrada_codigo.setPlaceholderText("🔍 Código o Producto (F1)...")
        layout_principal.addWidget(self.entrada_codigo, stretch=2)
        
        # --- Totales Grandes ---
        self.etiqueta_ahorro = QLabel("")
        self.etiqueta_ahorro.setObjectName("EtiquetaAhorro")
        self.etiqueta_ahorro.hide()
        
        self.etiqueta_total_grande = QLabel("0")
        self.etiqueta_total_grande.setObjectName("TotalGrande")
        self.etiqueta_total_grande.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        layout_totales = QHBoxLayout()
        layout_totales.addWidget(self.etiqueta_total_grande)
        layout_totales.addWidget(self.etiqueta_ahorro)
        layout_principal.addLayout(layout_totales, stretch=3)
        
        # --- Resumen Lateral ---
        self.caja_resumen = QFrame()
        self.caja_resumen.setObjectName("CajaResumen")
        layout_resumen = QVBoxLayout(self.caja_resumen)
        layout_resumen.setContentsMargins(10, 5, 10, 5)
        layout_resumen.setSpacing(2)

        self.titulo_cant, self.valor_cant = self._crear_fila(layout_resumen, "CANTIDAD")
        self.titulo_total, self.valor_total = self._crear_fila(layout_resumen, "TOTAL")
        self.titulo_ahorro, self.valor_ahorro = self._crear_fila(layout_resumen, "AHORRO")
        self.titulo_pagos, self.valor_pagos = self._crear_fila(layout_resumen, "PAGOS")
        self.titulo_cambio, self.valor_cambio = self._crear_fila(layout_resumen, "CAMBIO")
        
        # Ocultar iniciales
        for item in [self.titulo_ahorro, self.valor_ahorro]: item.hide()
        
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