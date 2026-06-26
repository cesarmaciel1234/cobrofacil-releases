from PyQt6.QtWidgets import QFrame, QGridLayout, QPushButton, QApplication, QLineEdit
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent

class VirtualKeyboardPaso6(QFrame):
    """
    Teclado Virtual Industrial para Paso 6 (Cobro).
    Incrustado directamente en la interfaz.
    Diseño de 5 filas, tamaño fijo de 240x330px.
    """
    def __init__(self, parent_dialog, parent=None):
        super().__init__(parent)
        self.parent_dialog = parent_dialog
        
        self.setObjectName("KeyboardFrame")
        self.setStyleSheet("""
            QFrame#KeyboardFrame {
                background-color: #F1F5F9;
                border: 2px solid #CBD5E1;
                border-radius: 12px;
            }
        """)
        self.setFixedSize(240, 330)
        
        self.init_ui()
        
    def init_ui(self):
        kb_layout = QGridLayout(self)
        kb_layout.setContentsMargins(8, 8, 8, 8)
        kb_layout.setSpacing(6)
        
        # Mapeo de teclas de caracteres comunes
        self.teclado_key_map = {
            '0': Qt.Key_0, '1': Qt.Key_1, '2': Qt.Key_2, '3': Qt.Key_3, '4': Qt.Key_4,
            '5': Qt.Key_5, '6': Qt.Key_6, '7': Qt.Key_7, '8': Qt.Key_8, '9': Qt.Key_9,
            ',': Qt.Key_Comma, '.': Qt.Key_Period
        }
        
        btn_style = """
            QPushButton {
                background-color: #FFFFFF;
                color: #0F172A;
                font-size: 15px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
                border: 1px solid #E2E8F0;
                border-bottom: 2px solid #CBD5E1;
                border-radius: 6px;
                min-width: 48px;
                min-height: 48px;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
        """
        
        keys = [
            ("1", 0, 0, 1, 1), ("2", 0, 1, 1, 1), ("3", 0, 2, 1, 1),
            ("4", 1, 0, 1, 1), ("5", 1, 1, 1, 1), ("6", 1, 2, 1, 1),
            ("7", 2, 0, 1, 1), ("8", 2, 1, 1, 1), ("9", 2, 2, 1, 1),
            (",", 3, 0, 1, 1), ("0", 3, 1, 1, 1), ("⌫", 3, 2, 1, 1),
            ("ESC", 4, 0, 1, 1), ("ENTER", 4, 1, 1, 2)
        ]
        
        for key, row, col, rowspan, colspan in keys:
            btn = QPushButton(key)
            btn.setStyleSheet(btn_style)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCursor(Qt.PointingHandCursor)
            
            # Estilos específicos para teclas especiales
            if key == "⌫":
                btn.setStyleSheet(btn_style + "QPushButton { background-color: #E2E8F0; color: #EF4444; border-color: #CBD5E1; }")
            elif key == "ESC":
                btn.setStyleSheet(btn_style + "QPushButton { background-color: #E2E8F0; color: #D97706; border-color: #CBD5E1; }")
            elif key == "ENTER":
                btn.setStyleSheet(btn_style + "QPushButton { background-color: #1A73E8; color: white; border-color: #1557B0; border-bottom: 2px solid #0D3E8C; }")
            
            btn.clicked.connect(lambda checked, k=key: self.on_teclado_key_clicked(k))
            kb_layout.addWidget(btn, row, col, rowspan, colspan)
            
    def on_teclado_key_clicked(self, key):
        focused = getattr(self.parent_dialog, 'ultimo_foco', None)
        if not focused or not isinstance(focused, QLineEdit):
            focused = getattr(self.parent_dialog, 'txt_pago', None)
            
        if not focused:
            return
            
        # Asegurar foco visual en el widget de texto activo
        focused.setFocus()
        
        if key == "⌫":
            event_press = QKeyEvent(QEvent.KeyPress, Qt.Key_Backspace, Qt.NoModifier, "")
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.KeyRelease, Qt.Key_Backspace, Qt.NoModifier, "")
            QApplication.sendEvent(focused, event_release)
        elif key == "ESC":
            self.parent_dialog.reject()
        elif key == "ENTER":
            event_press = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier, "\n")
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.KeyRelease, Qt.Key_Return, Qt.NoModifier, "\n")
            QApplication.sendEvent(focused, event_release)
        else:
            key_code = self.teclado_key_map.get(key, Qt.Key_unknown)
            event_press = QKeyEvent(QEvent.KeyPress, key_code, Qt.NoModifier, key)
            QApplication.sendEvent(focused, event_press)
            event_release = QKeyEvent(QEvent.KeyRelease, key_code, Qt.NoModifier, key)
            QApplication.sendEvent(focused, event_release)
