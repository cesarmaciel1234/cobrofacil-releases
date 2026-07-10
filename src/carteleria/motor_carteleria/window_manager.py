from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QApplication, QPushButton, QFrame, QHBoxLayout, QVBoxLayout, QLabel

class WindowManager:
    def __init__(self, main_window):
        self.main = main_window
        self.selector_monitor = None
        self.timer_selector = None
        self.setup_shortcuts()

    def setup_shortcuts(self):
        # Botón de emergencia F11 (Global para esta ventana)
        self.shortcut_f11 = QShortcut(QKeySequence(Qt.Key_F11), self.main)
        self.shortcut_f11.activated.connect(self.f11_pressed)

        # F10 — Selector de monitor / toggle fullscreen
        self.shortcut_f10 = QShortcut(QKeySequence(Qt.Key_F10), self.main)
        self.shortcut_f10.activated.connect(self.f10_pressed)

    def f11_pressed(self):
        # Intentar volver al dashboard a través de la señal
        try:
            if hasattr(self.main, "request_back"):
                self.main.request_back.emit()
            elif hasattr(self.main, "request_screen"):
                self.main.request_screen.emit(0)
        except Exception: pass
        
        # Solo salir de pantalla completa, NO cerrar la aplicación entera
        top_window = self.main.window()
        if top_window and top_window.isFullScreen():
            top_window.showNormal()

    def f10_pressed(self):
        """F10: Alterna entre pantalla completa y modo ventana."""
        top_window = self.main.window()
        if top_window:
            if top_window.isFullScreen():
                top_window.showNormal()
                top_window.resize(900, 600)
            else:
                top_window.showFullScreen()

    def mostrar_selector_monitor(self):
        """Muestra un panel flotante encima de la ventana para elegir el monitor destino."""
        app = QApplication.instance()
        screens = app.screens()

        # Crear panel flotante si no existe o fue destruido
        if self.selector_monitor is None or not self.selector_monitor.isVisible():
            panel = QFrame(self.main)
            panel.setObjectName("SelectorMonitor")
            panel.setStyleSheet("""
                QFrame#SelectorMonitor {
                    background: rgba(15, 23, 42, 230);
                    border: 2px solid #38BDF8;
                    border-radius: 18px;
                }
                QPushButton {
                    background: #1E3A5F;
                    color: white;
                    border: 1.5px solid #38BDF8;
                    border-radius: 12px;
                    padding: 14px 22px;
                    font-size: 15px;
                    font-weight: bold;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: #2563EB;
                    border-color: #7DD3FC;
                }
                QPushButton:pressed {
                    background: #1D4ED8;
                }
            """)
            v = QVBoxLayout(panel)
            v.setContentsMargins(20, 18, 20, 18)
            v.setSpacing(12)

            titulo = QLabel(f"📺  Mover a monitor  (F10 = fullscreen aquí)")
            titulo.setStyleSheet("color: #7DD3FC; font-size: 13px; font-weight: bold; border: none; background: transparent;")
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(titulo)

            fila = QHBoxLayout()
            fila.setSpacing(12)
            for idx, screen in enumerate(screens):
                geo = screen.geometry()
                label = f"🖥  Monitor {idx + 1}\n{geo.width()}×{geo.height()}"
                btn = QPushButton(label)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                # Highlight del monitor actual
                if self.main.isWindow():
                    win_center = self.main.frameGeometry().center()
                    if screen.geometry().contains(win_center):
                        btn.setStyleSheet(
                            btn.styleSheet() +
                            "background: #065F46; border-color: #34D399;"
                        )
                btn.clicked.connect(lambda checked, i=idx: self.mover_a_monitor(i))
                fila.addWidget(btn)

            v.addLayout(fila)

            nota = QLabel("Presioná F10 de nuevo para volver a pantalla completa")
            nota.setStyleSheet("color: #94A3B8; font-size: 11px; border: none; background: transparent;")
            nota.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(nota)

            panel.adjustSize()
            # Centrar sobre la ventana
            pw, ph = panel.width(), panel.height()
            sx = (self.main.width() - pw) // 2
            sy = (self.main.height() - ph) // 2
            panel.move(sx, sy)
            panel.show()
            panel.raise_()
            self.selector_monitor = panel

            # Auto-ocultar tras 8 segundos
            self.timer_selector = QTimer(self.main)
            self.timer_selector.setSingleShot(True)
            self.timer_selector.timeout.connect(lambda: panel.hide() if panel.isVisible() else None)
            self.timer_selector.start(8000)

    def mover_a_monitor(self, screen_index: int):
        """Mueve la ventana de cartelería al monitor indicado en fullscreen."""
        if self.selector_monitor:
            self.selector_monitor.hide()

        app = QApplication.instance()
        screens = app.screens()
        if screen_index >= len(screens):
            screen_index = 0

        target_screen = screens[screen_index]
        geo = target_screen.geometry()

        top_window = self.main.window()
        if top_window:
            # Quitar fullscreen primero, mover, luego fullscreen
            top_window.showNormal()
            top_window.setGeometry(geo)
            QTimer.singleShot(120, top_window.showFullScreen)
