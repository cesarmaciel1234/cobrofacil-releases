import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication, QFrame
from PyQt5.QtCore import Qt, QEvent, QPoint
from PyQt5.QtGui import QKeyEvent

class VirtualKeyboard(QWidget):
    """
    Teclado Virtual Industrial para entornos táctiles de escritorio.
    Diseñado para flotar sobre la aplicación y enviar pulsaciones sin robar el foco.
    Estética de colores claros estilo Android (Gboard Light Theme) con tamaño optimizado para escritorio (48x48px).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Atributos de ventana
        self.setWindowFlags(
            Qt.Tool | 
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Estado del teclado
        self.shift_active = False
        self.layout_mode = "abc"  # "abc" o "123"
        self.letter_buttons = {}  # Guarda referencia para cambiar a mayúsculas/minúsculas
        self._drag_position = QPoint()
        
        # Mapeo completo de caracteres a Qt.Key
        self.key_map = {
            'a': Qt.Key_A, 'b': Qt.Key_B, 'c': Qt.Key_C, 'd': Qt.Key_D, 'e': Qt.Key_E,
            'f': Qt.Key_F, 'g': Qt.Key_G, 'h': Qt.Key_H, 'i': Qt.Key_I, 'j': Qt.Key_J,
            'k': Qt.Key_K, 'l': Qt.Key_L, 'm': Qt.Key_M, 'n': Qt.Key_N, 'o': Qt.Key_O,
            'p': Qt.Key_P, 'q': Qt.Key_Q, 'r': Qt.Key_R, 's': Qt.Key_S, 't': Qt.Key_T,
            'u': Qt.Key_U, 'v': Qt.Key_V, 'w': Qt.Key_W, 'x': Qt.Key_X, 'y': Qt.Key_Y,
            'z': Qt.Key_Z,
            'ñ': Qt.Key_Ntilde,
            '0': Qt.Key_0, '1': Qt.Key_1, '2': Qt.Key_2, '3': Qt.Key_3, '4': Qt.Key_4,
            '5': Qt.Key_5, '6': Qt.Key_6, '7': Qt.Key_7, '8': Qt.Key_8, '9': Qt.Key_9,
            '-': Qt.Key_Minus, '=': Qt.Key_Equal, '+': Qt.Key_Plus, '*': Qt.Key_Asterisk,
            '/': Qt.Key_Slash, '%': Qt.Key_Percent, '$': Qt.Key_Dollar, '@': Qt.Key_At,
            '&': Qt.Key_Ampersand, '?': Qt.Key_Question, '!': Qt.Key_Exclam,
            '(': Qt.Key_ParenLeft, ')': Qt.Key_ParenRight, '[': Qt.Key_BracketLeft, ']': Qt.Key_BracketRight,
            '{': Qt.Key_BraceLeft, '}': Qt.Key_BraceRight, '<': Qt.Key_Less, '>': Qt.Key_Greater,
            '#': Qt.Key_NumberSign, '_': Qt.Key_Underscore, '\\': Qt.Key_Backslash, '|': Qt.Key_Bar,
            ';': Qt.Key_Semicolon, ':': Qt.Key_Colon, '"': Qt.Key_QuoteDbl, ',': Qt.Key_Comma,
            '.': Qt.Key_Period
        }
        
        self.init_ui()

    def set_layout_mode(self, mode):
        """Establece el layout ('abc' o '123') y reconstruye las teclas."""
        if mode in ("abc", "123") and self.layout_mode != mode:
            self.layout_mode = mode
            if hasattr(self, 'keys_layout'):
                self.build_keys()

    def init_ui(self):
        # Contenedor principal con estilo premium claro
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: #F1F5F9;
                border: 2px solid #CBD5E1;
                border-radius: 12px;
            }
        """)
        
        self.main_layout = QVBoxLayout(self.main_frame)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(6)
        
        # 1. Barra de Arrastre (Titlebar simulado)
        drag_bar = QWidget()
        drag_bar.setFixedHeight(30)
        drag_bar.setStyleSheet("background-color: #E2E8F0; border-radius: 6px;")
        
        drag_layout = QHBoxLayout(drag_bar)
        drag_layout.setContentsMargins(10, 0, 10, 0)
        
        self.title_lbl = QLabel("⌨️ TECLADO VIRTUAL POS")
        self.title_lbl.setStyleSheet("color: #475569; font-weight: 800; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        drag_layout.addWidget(self.title_lbl)
        drag_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setFocusPolicy(Qt.NoFocus)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748B;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                color: #EF4444;
                background-color: rgba(239, 68, 68, 0.1);
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.hide)
        drag_layout.addWidget(close_btn)
        
        self.main_layout.addWidget(drag_bar)
        
        # Contenedor para el layout de teclas dinámico
        self.keys_container = QWidget()
        self.keys_layout = QVBoxLayout(self.keys_container)
        self.keys_layout.setContentsMargins(0, 0, 0, 0)
        self.keys_layout.setSpacing(5)
        self.main_layout.addWidget(self.keys_container)
        
        # Construir las teclas iniciales
        self.build_keys()
        
        # Layout principal de la ventana
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_frame)
        
    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def build_keys(self):
        # Limpiar el layout existente
        self.clear_layout(self.keys_layout)
        self.letter_buttons.clear()
        
        # Estilo de botones de teclas (Estilo Gboard Claro - Tamaño Escritorio 48x48px)
        key_style = """
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
        
        # Definir filas según el layout activo (removiendo las flechas)
        if self.layout_mode == "abc":
            rows = [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "⌫"],
                ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
                ["A", "S", "D", "F", "G", "H", "J", "K", "L", "Ñ"],
                ["⚡ SHIFT", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "?123"],
                ["ESPACIO", "ENTER"]
            ]
        else:
            rows = [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "⌫"],
                ["+", "-", "*", "/", "=", "%", "$", "@", "&"],
                ["?", "!", "(", ")", "[", "]", "{", "}"],
                ["<", ">", "#", "_", "\\", "|", ";", ":", "\"", "ABC"],
                ["ESPACIO", "ENTER"]
            ]
            
        for i, row in enumerate(rows):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(5)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            for key in row:
                btn = QPushButton(key)
                btn.setStyleSheet(key_style)
                btn.setFocusPolicy(Qt.NoFocus)
                btn.setCursor(Qt.PointingHandCursor)
                
                # Sizing y colores especiales para teclas de control (Tamaño de escritorio adaptado)
                if key == "⌫":
                    btn.setMinimumWidth(70)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #E2E8F0; color: #EF4444; border-color: #CBD5E1; }")
                elif key == "⚡ SHIFT":
                    btn.setMinimumWidth(95)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #E2E8F0; color: #D97706; border-color: #CBD5E1; }")
                elif key in ("?123", "ABC"):
                    btn.setMinimumWidth(115)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #E2E8F0; color: #1E40AF; border-color: #CBD5E1; }")
                elif key == "ESPACIO":
                    btn.setMinimumWidth(350)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #FFFFFF; }")
                elif key == "ENTER":
                    btn.setMinimumWidth(170)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #1A73E8; color: white; border-color: #1557B0; border-bottom: 2px solid #0D3E8C; }")
                    
                # Guardar referencia de botones de letras para cambiar mayús/minús (sólo modo abc)
                if len(key) == 1 and key.isalpha() and self.layout_mode == "abc":
                    self.letter_buttons[key] = btn
                    if not self.shift_active:
                        btn.setText(key.lower())
                    
                btn.clicked.connect(lambda checked, k=key: self.on_key_press(k))
                row_layout.addWidget(btn)
                
            self.keys_layout.addLayout(row_layout)
            
    def on_key_press(self, key_text):
        focused = QApplication.focusWidget()
        if not focused:
            return
            
        if key_text == "⚡ SHIFT":
            self.shift_active = not self.shift_active
            # Cambiar texto visual de botones de letras
            for orig_char, btn in self.letter_buttons.items():
                btn.setText(orig_char.upper() if self.shift_active else orig_char.lower())
            return
            
        elif key_text == "?123":
            self.layout_mode = "123"
            self.build_keys()
            return
            
        elif key_text == "ABC":
            self.layout_mode = "abc"
            self.build_keys()
            return
            
        # Determinar el caracter y key code correspondientes
        modifiers = Qt.ShiftModifier if self.shift_active else Qt.NoModifier
        
        if key_text == "⌫":
            self.send_key_event(focused, Qt.Key_Backspace, "", modifiers)
        elif key_text == "ESPACIO":
            self.send_key_event(focused, Qt.Key_Space, " ", modifiers)
        elif key_text == "ENTER":
            # Envía el Enter
            self.send_key_event(focused, Qt.Key_Return, "\n", modifiers)
            # Se oculta automático como en celulares
            self.hide()
            return
        else:
            # Letra o caracter normal
            char_to_send = key_text
            if self.layout_mode == "abc" and not self.shift_active and len(char_to_send) == 1:
                char_to_send = char_to_send.lower()
                
            key_code = self.key_map.get(char_to_send.lower() if len(char_to_send) == 1 else char_to_send, Qt.Key_unknown)
            self.send_key_event(focused, key_code, char_to_send, modifiers)

    def send_key_event(self, target, key_code, text, modifiers):
        # Enviar evento de presionar tecla
        event_press = QKeyEvent(QEvent.KeyPress, key_code, modifiers, text)
        QApplication.sendEvent(target, event_press)
        
        # Enviar evento de liberar tecla
        event_release = QKeyEvent(QEvent.KeyRelease, key_code, modifiers, text)
        QApplication.sendEvent(target, event_release)

    # Implementar arrastre de la ventana frameless
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()
