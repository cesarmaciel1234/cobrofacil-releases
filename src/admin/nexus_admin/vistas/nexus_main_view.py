from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from src.admin.nexus_admin.vistas.componentes.panel_izquierdo.nexus_panel_izq import NexusPanelIzq
from src.admin.nexus_admin.vistas.componentes.panel_central.nexus_panel_cen import NexusPanelCen
from src.admin.nexus_admin.vistas.componentes.panel_derecho.nexus_panel_der import NexusPanelDer
from src.utils.theme_manager import theme_manager

class NexusMainView(QWidget):
    def __init__(self, parent_main=None):
        super().__init__(parent_main)
        self.parent_main = parent_main
        self.original_style = ""
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- HEADER HUD ---
        layout_hud = QHBoxLayout()
        self.btn_abort = QPushButton("- SALIR DE NEXUS")
        self.btn_abort.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_abort.setStyleSheet('''
            QPushButton {
                background: #3B82F6; color: white; font-weight: 800; font-size: 11px;
                padding: 6px 15px; border-radius: 4px; border: none; letter-spacing: 1px;
            }
            QPushButton:hover { background: #2563EB; }
        ''')
        if hasattr(self.parent_main, 'request_dashboard'):
            self.btn_abort.clicked.connect(self.parent_main.request_dashboard.emit)

        layout_hud.addWidget(self.btn_abort)
        
        self.lbl_reloj = QLabel("00:00:00  //  00-00-0000")
        self.lbl_reloj.setStyleSheet("color: #64748B; font-weight: bold; font-size: 13px; margin-left: 15px;")
        layout_hud.addWidget(self.lbl_reloj)
        
        layout_hud.addStretch()

        self.lbl_titulo = QLabel("N E X U S  //  CONTROL CENTER")
        layout_hud.addWidget(self.lbl_titulo)
        
        layout_hud.addStretch()
        # Para mantener el equilibrio del stretch de la derecha
        right_spacer = QLabel("")
        right_spacer.setFixedWidth(300)
        layout_hud.addWidget(right_spacer)
        
        main_layout.addLayout(layout_hud)

        # --- PANELES ---
        layout_paneles = QHBoxLayout()
        layout_paneles.setSpacing(10)
        layout_paneles.setContentsMargins(0, 0, 0, 0)

        self.panel_izq = NexusPanelIzq()
        layout_paneles.addWidget(self.panel_izq, 25)

        self.panel_cen = NexusPanelCen()
        layout_paneles.addWidget(self.panel_cen, 35)

        self.panel_der = NexusPanelDer()
        layout_paneles.addWidget(self.panel_der, 40)

        main_layout.addLayout(layout_paneles, 1)

        self._aplicar_estilos(theme_manager.current_theme)
        theme_manager.theme_changed.connect(self._aplicar_estilos)

    def _aplicar_estilos(self, theme="light"):
        if theme == "dark":
            bg_main = "#0F172A"
            text_color = "#F8FAFC"
            header_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:1 #3B82F6)"
        else:
            bg_main = "#F8FAFC"
            text_color = "#1E293B"
            header_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D97706, stop:1 #3B82F6)"

        self.setStyleSheet(f"QWidget {{ background: {bg_main}; }}")
        self.original_style = self.styleSheet()

        self.lbl_titulo.setStyleSheet(f'''
            font-size: 18px; font-weight: 900; letter-spacing: 5px;
            background: {header_bg}; color: white; padding: 5px 15px; border-radius: 5px;
        ''')
        self.lbl_reloj.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {text_color}; background: transparent; border: none;")

        self.panel_cen.update_theme(theme)
        self.panel_izq.update_theme(theme)
        self.panel_der.update_theme(theme)

    def _play_sound(self, sound_type):
        from PyQt6.QtCore import QUrl
        from PyQt6.QtMultimedia import QSoundEffect
        try:
            effect = QSoundEffect(self)
            import os
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            s_map = {
                "sale": os.path.join(base, "assets", "sounds", "ui_click.wav"),
                "alert": os.path.join(base, "assets", "sounds", "error.wav")
            }
            if os.path.exists(s_map.get(sound_type, "")):
                effect.setSource(QUrl.fromLocalFile(s_map[sound_type]))
                effect.play()
        except Exception as e:
            print("Sound error:", e)
