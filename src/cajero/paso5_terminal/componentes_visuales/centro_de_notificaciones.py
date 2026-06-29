from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class CentroDeNotificaciones(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalNotificacionesContainer")
        # Por defecto no ocupará espacio si no hay alertas
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(4)
        
        # --- Alerta de Stock Mínimo (Amarilla) ---
        self.alerta_stock = QFrame()
        self.alerta_stock.setFixedHeight(36)
        self.alerta_stock.setObjectName("TerminalNotificacionStock")
        self.alerta_stock.hide() # Oculta por defecto
        
        layout_alerta_stock = QHBoxLayout(self.alerta_stock)
        layout_alerta_stock.setContentsMargins(15, 0, 15, 0)
        
        self.etiqueta_alerta_stock = QLabel("🔔 Alerta de Stock: Hay productos por debajo del mínimo")
        self.etiqueta_alerta_stock.setObjectName("TerminalNotificacionStockLbl")
        layout_alerta_stock.addWidget(self.etiqueta_alerta_stock)
        
        # --- Alerta de Urgencia (Roja) ---
        # Si se necesita el banner de urgencia de stock que ya existía, lo inicializamos aquí.
        # Dejaremos un espacio o frame generico para notificaciones rojas
        self.alerta_urgencia = QFrame()
        self.alerta_urgencia.setFixedHeight(36)
        self.alerta_urgencia.setObjectName("TerminalNotificacionUrgencia")
        self.alerta_urgencia.hide()
        
        layout_alerta_urgencia = QHBoxLayout(self.alerta_urgencia)
        layout_alerta_urgencia.setContentsMargins(15, 0, 15, 0)
        
        self.etiqueta_alerta_urgencia = QLabel("🚨 URGENCIA ACTIVA — Venta permitida SIN STOCK")
        self.etiqueta_alerta_urgencia.setObjectName("TerminalNotificacionUrgenciaLbl")
        layout_alerta_urgencia.addWidget(self.etiqueta_alerta_urgencia)
        
        # Añadimos las alertas al contenedor principal
        self.layout_principal.addWidget(self.alerta_stock)
        self.layout_principal.addWidget(self.alerta_urgencia)

    def mostrar_alerta_stock(self, mensaje: str):
        self.etiqueta_alerta_stock.setText(mensaje)
        self.alerta_stock.show()
        
    def ocultar_alerta_stock(self):
        self.alerta_stock.hide()
        
    def mostrar_alerta_urgencia(self, mensaje: str):
        self.etiqueta_alerta_urgencia.setText(mensaje)
        self.alerta_urgencia.show()
        
    def ocultar_alerta_urgencia(self):
        self.alerta_urgencia.hide()
        
    def mostrar_mensaje_sistema(self, mensaje: str):
        """Método adicional para mostrar otros eventos (puede reutilizar la alerta amarilla)"""
        self.mostrar_alerta_stock(f"ℹ️ {mensaje}")
