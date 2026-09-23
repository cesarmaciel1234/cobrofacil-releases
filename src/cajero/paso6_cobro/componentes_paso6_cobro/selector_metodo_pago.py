import os
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QGridLayout
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPixmap
from src.config import config

class SelectorMetodoPago(QWidget):
    """
    Componente extraído de paso6_cobro.py: Botones superiores de métodos de pago.
    """
    metodo_seleccionado = pyqtSignal(str) # Emite 'Efectivo', 'Tarjeta', 'Fiado', etc.

    def __init__(self, parent=None):
        super().__init__(parent)
        self.btns = {}

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(self.grid_layout)

        self.metodos = [
            ("💰", "Efectivo", "Efectivo"),
            ("💳", "Crédito", "Tarjeta"),
            ("🏦", "Transf.", "Transferencia"),
            ("📱", "QR", "QR"),
            ("🔀", "Mixto", "Mixto")
        ]

        self.build_ui()

    def build_ui(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        assets_dir = os.path.join(base_dir, "assets")
        self.theme = config.get("theme", "light")

        row, col = 0, 0

        for icon, text, key in self.metodos:
            container = QFrame()
            container.setObjectName("Paso6TarjetaMetodo")
            container.setFixedSize(180, 160)
            container.setCursor(Qt.CursorShape.PointingHandCursor)

            if self.theme == "dark":
                container.setStyleSheet("""
                    QFrame#Paso6TarjetaMetodo {
                        background: #1E293B;
                        border: 1px solid #334155;
                        border-radius: 16px;
                    }
                    QFrame#Paso6TarjetaMetodo[active="true"] {
                        background: #1E293B;
                        border: 2px solid #F8FAFC;
                    }
                    QFrame#Paso6TarjetaMetodo:hover {
                        border-color: #64748B;
                    }
                """)
            else:
                container.setStyleSheet("""
                    QFrame#Paso6TarjetaMetodo {
                        background: #FFFFFF;
                        border: 1px solid #E2E8F0;
                        border-radius: 16px;
                    }
                    QFrame#Paso6TarjetaMetodo[active="true"] {
                        background: #F8FAFC;
                        border: 2px solid #15293C;
                    }
                    QFrame#Paso6TarjetaMetodo:hover {
                        border-color: #94A3B8;
                    }
                """)
            container.setProperty("active", False)

            c_lay = QVBoxLayout(container)
            c_lay.setContentsMargins(12, 16, 12, 12)
            c_lay.setSpacing(6)

            lbl_icon = QLabel()
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon_path = os.path.join(assets_dir, f"{key.lower()}.png")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                lbl_icon.setPixmap(pixmap.scaled(80, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                lbl_icon.setStyleSheet("background: transparent; border: none;")
            else:
                lbl_icon.setText(icon)
                lbl_icon.setStyleSheet("font-size: 34px; background: transparent; border: none;")

            color_txt = "#F8FAFC" if self.theme == "dark" else "#0F172A"
            lbl_text = QLabel(text.upper())
            lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_text.setStyleSheet(
                f"font-size: 16px; font-weight: 600; color: {color_txt}; background: transparent; border: none; letter-spacing: 0.6px;"
            )

            c_lay.addWidget(lbl_icon)
            c_lay.addWidget(lbl_text)

            # Boton invisible superpuesto para capturar clicks
            btn_overlay = QPushButton(container)
            btn_overlay.setFixedSize(180, 160)
            btn_overlay.setStyleSheet("background: transparent; border: none;")
            btn_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_overlay.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            btn_overlay.clicked.connect(lambda checked, k=key: self.metodo_seleccionado.emit(k))

            self.btns[key] = {
                "frame": container,
                "lbl_text": lbl_text,
                "overlay": btn_overlay
            }

            self.grid_layout.addWidget(container, row, col)

            col += 1
            if col > 4:
                col = 0
                row += 1

    def get_botones(self):
        """Devuelve el diccionario de botones para compatibilidad con paso6_cobro."""
        return self.btns
