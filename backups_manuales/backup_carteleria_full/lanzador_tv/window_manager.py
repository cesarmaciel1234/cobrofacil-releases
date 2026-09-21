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

        self.shortcut_esc = QShortcut(QKeySequence(Qt.Key_Escape), self.main)
        self.shortcut_esc.activated.connect(self.f11_pressed)

        # F10 — Selector de monitor / toggle fullscreen
        self.shortcut_f10 = QShortcut(QKeySequence(Qt.Key_F10), self.main)
        self.shortcut_f10.activated.connect(self.f10_pressed)

    def f11_pressed(self):
        try:
            if hasattr(self.main, "detener_carteleria"):
                self.main.detener_carteleria()
        except Exception:
            pass
        top_window = self.main.window()
        if top_window and top_window.isFullScreen():
            top_window.showNormal()

    def f10_pressed(self):
        """F10: elige monitor de TV si hay más de uno; si no, pantalla completa de la consola."""
        app = QApplication.instance()
        if app and len(app.screens()) > 1:
            self.mostrar_selector_monitor()
            return
        if hasattr(self.main, "emitir_en_monitor"):
            self.main.emitir_en_monitor(0)
            return
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
                    background: #FFFFFF;
                    border: 1px solid #CBD5E1;
                    border-radius: 6px;
                }
                QPushButton {
                    background: #F8FAFC;
                    color: #0F172A;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 12px 18px;
                    font-size: 14px;
                    font-weight: 700;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: #EFF6FF;
                    border-color: #2563EB;
                }
                QPushButton:pressed {
                    background: #DBEAFE;
                }
            """)
            v = QVBoxLayout(panel)
            v.setContentsMargins(20, 18, 20, 18)
            v.setSpacing(12)

            titulo = QLabel(f"📺  Mover a monitor  (F10 = fullscreen aquí)")
            titulo.setStyleSheet("color: #0F172A; font-size: 13px; font-weight: bold; border: none; background: transparent;")
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
        """Mueve el kiosk de TV al monitor indicado. La consola Qt se queda donde está."""
        if self.selector_monitor:
            self.selector_monitor.hide()

        if hasattr(self.main, "emitir_en_monitor"):
            self.main.emitir_en_monitor(screen_index)
            return

        app = QApplication.instance()
        screens = app.screens()
        if screen_index >= len(screens):
            screen_index = 0

        target_screen = screens[screen_index]
        geo = target_screen.geometry()

        top_window = self.main.window()
        if top_window:
            top_window.showNormal()
            top_window.setGeometry(geo)
            QTimer.singleShot(120, top_window.showFullScreen)
