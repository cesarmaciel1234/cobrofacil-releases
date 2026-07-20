import os
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QGraphicsDropShadowEffect, QGridLayout
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
        self.grid_layout.setSpacing(25)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(self.grid_layout)
        
        self.metodos = [
            ("💰", "Efectivo", "Efectivo"), 
            ("💳", "Crédito", "Tarjeta"), 
            ("🏦", "Transf.", "Transferencia"),
            ("📱", "QR", "QR"),
            ("👥", "Fiado", "Fiado"),
            ("👤", "Clientes", "Clientes"),
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
            container.setFixedSize(170, 160)
            container.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if self.theme == "dark":
                container.setStyleSheet("""
                    QFrame {
                        background: #1E293B;
                        border: 1.5px solid #334155;
                        border-radius: 24px;
                        margin-top: 4px;
                        margin-bottom: 0px;
                    }
                    QFrame[active="true"] {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 rgba(59, 130, 246, 0.15), 
                            stop:1 rgba(59, 130, 246, 0.05)
                        );
                        border: 2.5px solid #3B82F6;
                    }
                    QFrame:hover {
                        background: #334155;
                        border-color: #3B82F6;
                        margin-top: 0px;
                        margin-bottom: 4px;
                    }
                """)
            else:
                container.setStyleSheet("""
                    QFrame {
                        background: #FFFFFF;
                        border: 1.5px solid #EEF2F8;
                        border-radius: 24px;
                        margin-top: 4px;
                        margin-bottom: 0px;
                    }
                    QFrame[active="true"] {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 rgba(59, 130, 246, 0.08), 
                            stop:1 rgba(59, 130, 246, 0.03)
                        );
                        border: 2.5px solid #3B82F6;
                    }
                    QFrame:hover {
                        background: #F8FAFC;
                        border-color: #3B82F6;
                        margin-top: 0px;
                        margin-bottom: 4px;
                    }
                """)
            container.setProperty("active", False)
            
            c_lay = QVBoxLayout(container)
            c_lay.setContentsMargins(10, 15, 10, 10)
            c_lay.setSpacing(5)
            
            lbl_icon = QLabel()
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            icon_path = os.path.join(assets_dir, f"{key.lower()}.png")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                lbl_icon.setPixmap(pixmap.scaled(100, 85, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                lbl_icon.setStyleSheet("background: transparent; border: none;")
            else:
                lbl_icon.setText(icon)
                lbl_icon.setStyleSheet("font-size: 45px; background: transparent; border: none;")
            
            lbl_text = QLabel(text.upper())
            lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_text.setStyleSheet("font-size: 15px; font-weight: bold; color: #64748B; background: transparent; border: none;")
            
            c_lay.addWidget(lbl_icon)
            c_lay.addWidget(lbl_text)
            
            # Boton invisible superpuesto para capturar clicks
            btn_overlay = QPushButton(container)
            btn_overlay.setFixedSize(170, 160)
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
            if col > 3:
                col = 0
                row += 1

    def get_botones(self):
        """Devuelve el diccionario de botones para compatibilidad con paso6_cobro."""
        return self.btns
