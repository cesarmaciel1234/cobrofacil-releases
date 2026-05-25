import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication, QFrame
from PyQt5.QtCore import Qt, QEvent, QPoint
from PyQt5.QtGui import QKeyEvent

class VirtualKeyboard(QWidget):
    """
    Teclado Virtual Industrial para entornos táctiles.
    Diseñado para flotar sobre la aplicación y enviar pulsaciones sin robar el foco.
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
        self.letter_buttons = {}  # Guarda referencia para cambiar a mayúsculas/minúsculas
        self._drag_position = QPoint()
        
        # Mapeo de caracteres comunes a Qt.Key
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
            '-': Qt.Key_Minus, ',': Qt.Key_Comma, '.': Qt.Key_Period
        }
        
        self.init_ui()

    def init_ui(self):
        # Contenedor principal con estilo premium oscuro
        main_frame = QFrame(self)
        main_frame.setObjectName("MainFrame")
        main_frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: #0F172A;
                border: 2px solid #334155;
                border-radius: 12px;
            }
        """)
        
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # 1. Barra de Arrastre (Titlebar simulado)
        drag_bar = QWidget()
        drag_bar.setFixedHeight(30)
        drag_bar.setStyleSheet("background-color: #1E293B; border-radius: 6px;")
        
        drag_layout = QHBoxLayout(drag_bar)
        drag_layout.setContentsMargins(10, 0, 10, 0)
        
        title_lbl = QLabel("⌨️ TECLADO VIRTUAL POS (Arrastre para mover)")
        title_lbl.setStyleSheet("color: #94A3B8; font-weight: 800; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        drag_layout.addWidget(title_lbl)
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
        
        main_layout.addWidget(drag_bar)
        
        # Estilo de botones de teclas
        key_style = """
            QPushButton {
                background-color: #1E293B;
                color: #F8FAFC;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
                border: 1px solid #334155;
                border-radius: 6px;
                min-width: 42px;
                min-height: 42px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #475569;
            }
        """
        
        # Filas de teclas
        rows = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "⌫"],
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", "Ñ"],
            ["⚡ SHIFT", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "⌨ OCULTAR"],
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
                
                # Sizing especial para teclas de control
                if key == "⌫":
                    btn.setMinimumWidth(60)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #374151; color: #FCA5A5; }")
                elif key == "⚡ SHIFT":
                    btn.setMinimumWidth(80)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #374151; color: #FDE047; }")
                elif key == "⌨ OCULTAR":
                    btn.setMinimumWidth(100)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #374151; color: #94A3B8; }")
                elif key == "ESPACIO":
                    btn.setMinimumWidth(320)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #1E293B; }")
                elif key == "ENTER":
                    btn.setMinimumWidth(150)
                    btn.setStyleSheet(key_style + "QPushButton { background-color: #10B981; color: white; border-color: #059669; }")
                    
                # Guardar referencia de botones de letras para cambiar mayús/minús
                if len(key) == 1 and key.isalpha():
                    self.letter_buttons[key] = btn
                    
                btn.clicked.connect(lambda checked, k=key: self.on_key_press(k))
                row_layout.addWidget(btn)
                
            main_layout.addLayout(row_layout)
            
        # Layout principal de la ventana
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_frame)
        
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
            
        elif key_text == "⌨ OCULTAR":
            self.hide()
            return
            
        # Determinar el caracter y key code correspondientes
        modifiers = Qt.ShiftModifier if self.shift_active else Qt.NoModifier
        
        if key_text == "⌫":
            self.send_key_event(focused, Qt.Key_Backspace, "", modifiers)
        elif key_text == "ESPACIO":
            self.send_key_event(focused, Qt.Key_Space, " ", modifiers)
        elif key_text == "ENTER":
            self.send_key_event(focused, Qt.Key_Return, "\n", modifiers)
        else:
            # Letra o caracter normal
            char_to_send = key_text
            if not self.shift_active:
                char_to_send = char_to_send.lower()
                
            key_code = self.key_map.get(char_to_send.lower(), Qt.Key_unknown)
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
