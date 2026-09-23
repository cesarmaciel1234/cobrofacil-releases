from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt
from src.config import config
from .keys_layout import get_layout

def init_ui(keyboard):
    # Contenedor principal con estilo premium claro
    keyboard.main_frame = QFrame(keyboard)
    keyboard.main_frame.setObjectName("MainFrame")
    keyboard.main_frame.setObjectName("VkMainFrame")

    keyboard.main_layout = QVBoxLayout(keyboard.main_frame)
    keyboard.main_layout.setContentsMargins(8, 8, 8, 8)
    keyboard.main_layout.setSpacing(6)

    # 1. Barra de Arrastre (Titlebar simulado)
    keyboard.drag_bar = QWidget()
    keyboard.drag_bar.setFixedHeight(30)
    keyboard.drag_bar.setObjectName("VkDragBar")

    drag_layout = QHBoxLayout(keyboard.drag_bar)
    drag_layout.setContentsMargins(10, 0, 10, 0)

    keyboard.title_lbl = QLabel("⌨️ TECLADO VIRTUAL PASO 5")
    keyboard.title_lbl.setObjectName("VkTitle")
    drag_layout.addWidget(keyboard.title_lbl)
    drag_layout.addStretch()

    close_btn = QPushButton("✕")
    close_btn.setFixedSize(22, 22)
    close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    close_btn.setObjectName("VkCloseBtn")
    close_btn.clicked.connect(keyboard.hide)
    drag_layout.addWidget(close_btn)

    keyboard.main_layout.addWidget(keyboard.drag_bar)

    # Contenedor para el layout de teclas dinámico
    keyboard.keys_container = QWidget()
    keyboard.keys_layout = QVBoxLayout(keyboard.keys_container)
    keyboard.keys_layout.setContentsMargins(0, 0, 0, 0)
    keyboard.keys_layout.setSpacing(5)
    keyboard.main_layout.addWidget(keyboard.keys_container)

    # Construir las teclas iniciales e inicializar tema
    apply_theme(keyboard)

    # Layout principal de la ventana
    layout = QVBoxLayout(keyboard)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(keyboard.main_frame)

def apply_theme(keyboard):
    theme = config.get("theme", "light")
    if theme == "dark":
        keyboard.main_frame.setStyleSheet("""
            QFrame#VkMainFrame {
                background-color: #1E293B;
                border: 2px solid #334155;
                border-radius: 12px;
            }
            QLabel#VkTitle { color: #94A3B8; font-size: 11px; font-weight: bold; }
            QPushButton#VkCloseBtn { background: #334155; color: #F8FAFC; border: none; border-radius: 11px; font-weight: 800; font-size: 12px; }
            QPushButton#VkCloseBtn:hover { background: #EF4444; color: #FFFFFF; }
        """)
        keyboard.main_frame.setObjectName("VkMainFrame")
        if hasattr(keyboard, 'drag_bar'):
            keyboard.drag_bar.setObjectName("VkDragBar")
        if hasattr(keyboard, 'title_lbl'):
            keyboard.title_lbl.setObjectName("VkTitle")
    else:
        keyboard.main_frame.setStyleSheet("""
            QFrame#VkMainFrame {
                background-color: #F8FAFC;
                border: 2px solid #CBD5E1;
                border-radius: 12px;
            }
            QLabel#VkTitle { color: #64748B; font-size: 11px; font-weight: bold; }
            QPushButton#VkCloseBtn { background: #E2E8F0; color: #0F172A; border: none; border-radius: 11px; font-weight: 800; font-size: 12px; }
            QPushButton#VkCloseBtn:hover { background: #EF4444; color: #FFFFFF; }
        """)
        keyboard.main_frame.setObjectName("VkMainFrame")
        if hasattr(keyboard, 'drag_bar'):
            keyboard.drag_bar.setObjectName("VkDragBar")
        if hasattr(keyboard, 'title_lbl'):
            keyboard.title_lbl.setObjectName("VkTitle")

    if hasattr(keyboard, 'keys_layout'):
        build_keys(keyboard)

def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())

def build_keys(keyboard):
    clear_layout(keyboard.keys_layout)
    keyboard.letter_buttons.clear()

    theme = config.get("theme", "light")

    if theme == "dark":
        key_style = """
            QPushButton {
                background-color: #334155;
                color: #F8FAFC;
                font-size: 15px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
                border: 1px solid #475569;
                border-bottom: 2px solid #1E293B;
                border-radius: 6px;
                min-width: 48px;
                min-height: 48px;
            }
            QPushButton:hover {
                background-color: #475569;
                border-color: #64748B;
            }
        """
    else:
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

    keyboard.keys_container.setStyleSheet(key_style)

    rows = get_layout(keyboard.layout_mode)

    for row in rows:
        row_layout = QHBoxLayout()
        row_layout.setSpacing(5)
        row_layout.setContentsMargins(0, 0, 0, 0)

        for key in row:
            btn = QPushButton(key)
            btn.setObjectName("VkKey")
            
            if key in ["Ctrl", "Alt", "Cmd", "Fn", "Win", "Opt"]:
                btn.setProperty("tipo", "ctrl")
            elif key in ["Backspace", "←", "⌫"]:
                btn.setProperty("tipo", "backspace")
            elif key in ["Shift", "⇧", "⚡ SHIFT"]:
                btn.setProperty("tipo", "shift")
            elif key in ["?123", "ABC", "123", "SYM", "#+="]:
                btn.setProperty("tipo", "symbol")
            elif key in ["Enter", "↵", "ENTER"]:
                btn.setProperty("tipo", "enter")
                btn.setStyleSheet(key_style + "QPushButton { background-color: #1A73E8; color: white; border-color: #1557B0; border-bottom: 2px solid #0D3E8C; }")

            if len(key) == 1 and key.isalpha() and keyboard.layout_mode == "abc":
                keyboard.letter_buttons[key] = btn
                if not keyboard.shift_active:
                    btn.setText(key.lower())

            btn.clicked.connect(lambda checked, k=key: keyboard.on_key_press(k))
            row_layout.addWidget(btn)

        keyboard.keys_layout.addLayout(row_layout)
