from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from src.config import config

class TecladoNumericoLateral(QFrame):
    """
    Componente extraído de paso6_cobro.py: Teclado Numérico Lateral.
    Emite la señal 'key_clicked(str)' con el valor de la tecla presionada.
    """
    key_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("KeyboardFrame")
        self.setMinimumHeight(330)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.apply_theme()
        
        kb_layout = QVBoxLayout(self)
        kb_layout.setContentsMargins(10, 10, 10, 10)
        kb_layout.setSpacing(5)
        
        rows = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            [",", "0", "⌫"],
            ["Salir", "ENTER"]
        ]
        
        theme = config.get("theme", "light")
        if theme == "dark":
            btn_style = """
                QPushButton {
                    background-color: #334155;
                    color: #F8FAFC;
                    font-size: 16px;
                    font-weight: 800;
                    font-family: 'Segoe UI', sans-serif;
                    border: none;
                    border-radius: 14px;
                    min-width: 48px;
                    min-height: 48px;
                }
                QPushButton:hover {
                    background-color: #475569;
                }
            """
            bg_backspace = "#7F1D1D"
            color_backspace = "#FCA5A5"
            bg_esc = "#EF4444"
            color_esc = "#FFFFFF"
        else:
            btn_style = """
                QPushButton {
                    background-color: #FFFFFF;
                    color: #1E293B;
                    font-size: 16px;
                    font-weight: 800;
                    font-family: 'Segoe UI', sans-serif;
                    border: none;
                    border-radius: 14px;
                    min-width: 48px;
                    min-height: 48px;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                }
            """
            bg_backspace = "#FEE2E2"
            color_backspace = "#EF4444"
            bg_esc = "#EF4444"
            color_esc = "#FFFFFF"
        
        for row in rows:
            row_lay = QHBoxLayout()
            row_lay.setSpacing(5)
            row_lay.setContentsMargins(0, 0, 0, 0)
            
            for key in row:
                btn = QPushButton(key)
                btn.setStyleSheet(btn_style)
                btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                
                # Estilos específicos para teclas especiales
                if key == "⌫":
                    btn.setStyleSheet(btn_style + f"QPushButton {{ background-color: {bg_backspace}; color: {color_backspace}; }}")
                elif key == "Salir":
                    btn.setStyleSheet(btn_style + f"QPushButton {{ background-color: {bg_esc}; color: {color_esc}; }}")
                elif key == "ENTER":
                    btn.setStyleSheet(btn_style + "QPushButton { background-color: #3B82F6; color: white; }")
                
                btn.clicked.connect(lambda checked, k=key: self.key_clicked.emit(k))
                row_lay.addWidget(btn, 1)
                
            kb_layout.addLayout(row_lay)

    def apply_theme(self):
        theme = config.get("theme", "light")
        if theme == "dark":
            self.setStyleSheet("""
                QFrame#KeyboardFrame {
                    background-color: #1E293B;
                    border: 1px solid #334155;
                    border-radius: 24px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#KeyboardFrame {
                    background-color: #F1F5F9;
                    border: none;
                    border-radius: 24px;
                }
            """)
