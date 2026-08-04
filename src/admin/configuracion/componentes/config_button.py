"""Tile de configuración — premium liviano (solo QSS, sin sombras Qt)."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont


class ConfigButton(QFrame):
    clicked = pyqtSignal()

    def __init__(self, icon_emoji, text, parent=None):
        super().__init__(parent)
        self.setObjectName("ConfigTile")
        self.setFixedSize(118, 108)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("""
            QFrame#ConfigTile {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            QFrame#ConfigTile:hover {
                background-color: #EFF6FF;
                border: 1px solid #2563EB;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 14, 6, 8)
        layout.setSpacing(6)

        self.lbl_icon = QLabel(icon_emoji)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI Emoji", 24)
        font.setStyleStrategy(
            QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality
        )
        self.lbl_icon.setFont(font)
        self.lbl_icon.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.lbl_icon)

        self.lbl_text = QLabel(text)
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet(
            "font-family: 'Segoe UI'; font-size: 11px; font-weight: 700; "
            "color: #0F172A; background: transparent; border: none;"
        )
        layout.addWidget(self.lbl_text)

        self.btn_help = QPushButton("?", self)
        self.btn_help.setFixedSize(20, 20)
        self.btn_help.move(92, 6)
        self.btn_help.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_help.setStyleSheet(
            "QPushButton { border: none; font-size: 11px; font-weight: 700; "
            "color: #94A3B8; background: transparent; }"
            "QPushButton:hover { color: #2563EB; }"
        )
        self.btn_help.clicked.connect(self._show_help)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _show_help(self):
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
            "Actualizaciones": "Descarga las últimas mejoras del programa gratis.",
        }
        texto = explicaciones.get(self.lbl_text.text(), "Configura esta opción del sistema.")
        msg = f"{self.lbl_text.text().replace(chr(10), ' ')}\n\n{texto}"
        QMessageBox.information(self, "Ayuda rápida", msg)
