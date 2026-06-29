from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from datetime import datetime

class CabeceraSuperior(QFrame):
    def __init__(self, titulo_inicial="Punto de Venta", parent=None):
        super().__init__(parent)
        self.setFixedHeight(130)
        self.setObjectName("TerminalCabecera")
        
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(20, 15, 20, 15)
        
        # Columna 1: Estado e Instalación
        columna1 = QVBoxLayout()
        columna1.setSpacing(0)
        
        self.etiqueta_estado = QLabel("Estado:           MAESTRA")
        self.etiqueta_estado.setObjectName("TerminalCabeceraEstado")
        
        self.etiqueta_instalacion = QLabel("№ 0000-0000-0000")
        self.etiqueta_instalacion.setObjectName("TerminalCabeceraInstalacion")
        
        columna1.addWidget(self.etiqueta_estado)
        columna1.addWidget(self.etiqueta_instalacion)
        layout_principal.addLayout(columna1)
        
        layout_principal.addSpacing(40)
        
        # Columna 2: Caja y Fecha
        columna2 = QVBoxLayout()
        columna2.setSpacing(0)
        
        fila_caja = QHBoxLayout()
        fila_caja.setSpacing(8)
        fila_caja.setContentsMargins(0, 0, 0, 0)
        
        self.luz_indicadora = QLabel()
        self.luz_indicadora.setFixedSize(14, 14)
        self.luz_indicadora.setObjectName("LedStatus")
        self.luz_indicadora.setProperty("estado", "normal")
        
        self.etiqueta_caja = QLabel("Caja №:        [01] SERVER")
        self.etiqueta_caja.setObjectName("TerminalCabeceraCaja")
        
        fila_caja.addWidget(self.luz_indicadora, 0, Qt.AlignmentFlag.AlignVCenter)
        fila_caja.addWidget(self.etiqueta_caja)
        fila_caja.addStretch()
        
        columna2.addLayout(fila_caja)
        
        self.etiqueta_fecha = QLabel(f"Fecha:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.etiqueta_fecha.setObjectName("TerminalCabeceraFecha")
        
        columna2.addWidget(self.etiqueta_fecha)
        layout_principal.addLayout(columna2)
        
        layout_principal.addStretch()
        
        # Título del Terminal (a la derecha)
        self.etiqueta_titulo = QLabel(titulo_inicial)
        self.etiqueta_titulo.setObjectName("TerminalCabeceraTitulo")
        layout_principal.addWidget(self.etiqueta_titulo)

    def actualizar_reloj(self, texto_fecha_hora: str):
        self.etiqueta_fecha.setText(f"Fecha:  {texto_fecha_hora}")
        
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
