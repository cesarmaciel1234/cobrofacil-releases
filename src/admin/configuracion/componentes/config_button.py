from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor, QFont, QColor
import os, shutil, datetime, glob
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class ConfigButton(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, icon_emoji, text, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 100)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Estilo tipo botón interactivo
        self.setStyleSheet("""
            ConfigButton {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            ConfigButton:hover {
                background-color: #F8FAFC;
                border: 1px solid #3B82F6;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 15, 5, 5)
        layout.setSpacing(8)
        
        # Icono (Emoji)
        self.lbl_icon = QLabel(icon_emoji)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        layout.addWidget(self.lbl_icon)
        
        # Texto
        self.lbl_text = QLabel(text)
        self.lbl_text.setAlignment(Qt.AlignCenter)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet("font-size: 11px; font-weight: bold;  background: transparent; border: none;")
        layout.addWidget(self.lbl_text)
        
        # Botón Ayuda (Absoluto)
        self.btn_help = QPushButton("❓", self)
        self.btn_help.setFixedSize(22, 22)
        self.btn_help.move(85, 5)
        self.btn_help.setStyleSheet("border: none; font-size: 12px; background: transparent;")
        self.btn_help.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_help.clicked.connect(self._show_help)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def _show_help(self):
        from PyQt6.QtWidgets import QMessageBox
        explicaciones = {
            "Alertas de\nEfectivo": "Te avisa si hay mucho dinero en la caja para que lo guardes (evita robos).",
            "Opciones\nhabilitadas": "Activa o desactiva módulos clave como vender sin stock, fiar, imprimir solo, etc.",
            "Cajeros": "Crea usuarios y contraseñas para tus empleados.",
            "Base de datos\nPC Esclava": "Cambia la contraseña maestra usada para conectar computadoras secundarias por red.",
            "Administrar\nCajas": "Conecta varias computadoras para que cobren juntas en red.",
            "Logotipo del\nPrograma": "Cambia el nombre de tu negocio y el diseño del ticket.",
            "Ticket": "Diseña cómo sale el ticket impreso para el cliente.",
            "Impuestos": "Agrega el IVA u otros impuestos a tus ventas si lo necesitas.",
            "Símbolo de\nMoneda": "Elige si usas $ (Pesos/Dólares) o € (Euros).",
            "Unidades de\nMedida": "Para vender productos por Kilo, Litro, Unidad, Metro, etc.",
            "Dos Tiketeras\n2 Cajas": "Si tienes 2 empleados en la misma compu, cada uno usa su impresora.",
            "Lector de\nCódigos": "Una prueba para ver si tu escáner o pistola de códigos funciona bien.",
            "Cajón de\nDinero": "Hace que el cajón de billetes salte solo cuando terminas de cobrar.",
            "Báscula": "Conecta una balanza electrónica para que el peso pase solo a la pantalla.",
            "Terminal\nTPV": "Conecta MercadoPago Point o Clover para cobrar directo con tarjeta.",
            "Hardware\nIndustrial": "Opciones avanzadas para equipos grandes de supermercado.",
            "App\nCobro Fácil": "Búscanos en las redes para tener tu App Móvil de Jefe, donde podrás ver cada billete que entra o sale de la caja en tiempo real por nuestras alarmas de apertura de caja sin permiso.",
            "Integraciones\nNube": "Conecta otros servicios de internet.",
            "Notificaciones\npor Correo": "Te manda un email al celular cada vez que cierran la caja.",
            "Respaldo": "Guarda una copia de seguridad en un pendrive para no perder nada.",
            "Licencia": "Mira tu plan actual o compra la versión completa.",
            "Actualizaciones": "Descarga las últimas mejoras del programa gratis."
        }
        texto = explicaciones.get(self.lbl_text.text(), "Configura esta opción del sistema.")
        msg = f"ℹ️ {self.lbl_text.text().replace(chr(10), ' ')}\n\n{texto}"
        QMessageBox.information(self, "Ayuda Rápida", msg)

