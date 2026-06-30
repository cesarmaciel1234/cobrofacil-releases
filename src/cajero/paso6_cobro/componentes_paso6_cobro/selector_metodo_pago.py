import os
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QGraphicsDropShadowEffect
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
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(25)
        
        self.metodos = [
            ("💰", "Efectivo", "Efectivo"), 
            ("💳", "Crédito", "Tarjeta"), 
            ("🏦", "Transf.", "Transferencia"),
            ("📱", "QR", "QR"),
            ("👥", "Fiado", "Fiado"),
            ("🔀", "Mixto", "Mixto")
        ]
        
        self.build_ui()

    def build_ui(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        assets_dir = os.path.join(base_dir, "assets")
        theme = config.get("theme", "light")
        
        self.main_layout.addStretch()
        
        for icon, text, key in self.metodos:
            container = QFrame()
            container.setFixedSize(120, 105)
            
            if theme == "dark":
                container.setStyleSheet("""
                    QFrame {
                        background: #1E293B;
                        border: 1.5px solid #334155;
                        border-radius: 24px;
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
                        border-color: rgba(59, 130, 246, 0.60);
                    }
                """)
            else:
                container.setStyleSheet("""
                    QFrame {
                        background: #FFFFFF;
                        border: 1.5px solid #EEF2F8;
                        border-radius: 24px;
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
                        border-color: rgba(59, 130, 246, 0.40);
                    }
                """)
            container.setProperty("active", False)
            
            # Se elimina la sombra para optimizar rendimiento en W10 de bajos recursos y evitar artefactos gráficos
            
            c_lay = QVBoxLayout(container)
            c_lay.setContentsMargins(5, 5, 5, 5)
            c_lay.setSpacing(0)
            
            lbl_icon = QLabel()
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            icon_path = os.path.join(assets_dir, f"{key.lower()}.png")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                lbl_icon.setPixmap(pixmap.scaled(96, 82, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                lbl_icon.setStyleSheet("background: transparent; border: none;")
            else:
                lbl_icon.setText(icon)
                lbl_icon.setStyleSheet("font-size: 38px; background: transparent; border: none;")
            
            c_lay.addWidget(lbl_icon)
            
            # Boton invisible superpuesto para capturar clicks
            btn_overlay = QPushButton(container)
            btn_overlay.setFixedSize(120, 105)
            btn_overlay.setStyleSheet("background: transparent; border: none;")
            btn_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_overlay.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            
            btn_overlay.clicked.connect(lambda checked, k=key: self.metodo_seleccionado.emit(k))
            
            self.btns[key] = {
                "frame": container,
                "lbl_text": None,
                "overlay": btn_overlay
            }
            
            self.main_layout.addWidget(container)
            
        self.main_layout.addStretch()

    def get_botones(self):
        """Devuelve el diccionario de botones para compatibilidad con paso6_cobro."""
        return self.btns
