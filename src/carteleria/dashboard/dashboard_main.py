import datetime
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor

# Stats
STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "module_stats.json")

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def increment_stat(module_name):
    try:
        stats = load_stats()
        stats[module_name] = stats.get(module_name, 0) + 1
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4)
    except Exception:
        pass


class CarteleriaCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, icon, color_bg, color_txt, desc="", parent=None):
        super().__init__(parent)
        self.color_bg_light = color_bg
        self.color_txt_light = color_txt
        
        self.color_bg_dark = "#1E293B"
        self.color_txt_dark = "#F8FAFC"
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(220, 150)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 38px; background: transparent; border: none;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_sub = QLabel(desc)
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sub.setWordWrap(True)
        
        lay.addWidget(lbl_icon)
        lay.addWidget(self.lbl_title)
        lay.addWidget(self.lbl_sub)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
        
    def apply_theme(self, is_dark):
        bg = self.color_bg_dark if is_dark else self.color_bg_light
        txt = self.color_txt_dark if is_dark else self.color_txt_light
        border_hover = "#3B82F6" if is_dark else self.color_txt_light
        
        self.setStyleSheet(f"""
            CarteleriaCard {{
                background-color: {bg};
                border: 1px solid {'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.1)'};
                border-radius: 12px;
            }}
            CarteleriaCard:hover {{
                border: 2px solid {border_hover};
            }}
        """)
        
        self.lbl_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {txt}; background: transparent; border: none;")
        self.lbl_sub.setStyleSheet(f"font-size: 11px; color: {txt}; opacity: 0.8; background: transparent; border: none;")


class CarteleriaDashboard(QWidget):
    request_screen = pyqtSignal(int)
    request_exit = pyqtSignal()
    request_launch_tv = pyqtSignal()
    request_admin_tv = pyqtSignal()
    request_inventario = pyqtSignal()
    request_ofertas = pyqtSignal()
    request_red_lan = pyqtSignal()
    request_toggle_theme = pyqtSignal()

    request_proveedores = pyqtSignal()
    request_png_productos = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._png_overlay = None
        self.setup_ui()
        # Timer for clock
        QTimer(self, timeout=self._tick, singleShot=False).start(30000)
        self._tick()

    def setup_ui(self):
        self.setObjectName("CarteleriaDashboard")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── NAVBAR ────────────────────────────────────────────────────────────
        self.nav = QFrame()
        self.nav.setObjectName("NavBar")
        self.nav.setFixedHeight(64)
        nav_lay = QHBoxLayout(self.nav)
        nav_lay.setContentsMargins(32, 0, 32, 0)

        self.brand_lbl = QLabel("🚀 CENTRAL DE CARTELERÍA")
        self.brand_lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #0F172A; background: transparent; border: none;")
        nav_lay.addWidget(self.brand_lbl)
        nav_lay.addStretch()

        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569; background: transparent; border: none; margin-right: 16px;")
        nav_lay.addWidget(self.lbl_clock)
        
        self.btn_theme = QPushButton("☀️ / 🌙 Tema")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.setFixedHeight(34)
        self.btn_theme.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569;
                border: 1.5px solid #E2E8F0; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 12px;
                margin-right: 8px;
            }
            QPushButton:hover { background: #E2E8F0; color: #0F172A; border-color: #CBD5E1; }
        """)
        self.btn_theme.clicked.connect(self.request_toggle_theme.emit)
        nav_lay.addWidget(self.btn_theme)

        self.btn_out = QPushButton("Cerrar")
        self.btn_out.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_out.setFixedHeight(34)
        self.btn_out.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569;
                border: 1.5px solid #E2E8F0; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background: #FEE2E2; color: #EF4444; border-color: #FECACA; }
        """)
        self.btn_out.clicked.connect(self.request_exit.emit)
        nav_lay.addWidget(self.btn_out)
        root.addWidget(self.nav)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.page = QWidget()
        self.page.setStyleSheet("background: transparent;")
        page_lay = QVBoxLayout(self.page)
        page_lay.setContentsMargins(48, 36, 48, 48)
        page_lay.setSpacing(24)

        # Hero
        hero = QFrame()
        hero.setFixedHeight(110)
        hero.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E40AF, stop:1 #3B82F6);
                border-radius: 16px;
            }
        """)
        hero_lay = QVBoxLayout(hero)
        hero_lay.setContentsMargins(32, 0, 32, 0)
        hero_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        lbl_welcome = QLabel("Módulo Autónomo")
        lbl_welcome.setStyleSheet("color: #93C5FD; font-size: 12px; font-weight: bold; background: transparent;")
        
        lbl_hero = QLabel("Control de Cartelería Digital")
        lbl_hero.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        
        hero_lay.addWidget(lbl_welcome)
        hero_lay.addWidget(lbl_hero)
        page_lay.addWidget(hero)

        # Grid de Tarjetas
        self.lbl_modulos = QLabel("Acciones Principales")
        page_lay.addWidget(self.lbl_modulos)

        grid = QGridLayout()
        grid.setSpacing(20)

        # Tarjetas de cartelería
        self.card_tv = CarteleriaCard("Lanzar TV Directo", "📺", "#EFF6FF", "#1D4ED8", "Abre cartelería en modo kiosk (sin consola)")
        self.card_admin = CarteleriaCard("Admin TV (Avanzado)", "⚙️", "#FEF2F2", "#B91C1C", "Modo consola Qt con control avanzado")
        
        self.card_inv = CarteleriaCard("Inventario", "📦", "#FDF4FF", "#A21CAF", "Gestión local de productos y stock")
        self.card_png = CarteleriaCard("PNG Productos", "🖼️", "#ECFDF5", "#047857", "Foto PNG de cada corte en la TV")
        self.card_ofe = CarteleriaCard("Ofertas", "🏷️", "#FFFBEB", "#D97706", "Crear promos y ofertas de TV")
        self.card_red = CarteleriaCard("Red LAN", "🌐", "#F3F4F6", "#374151", "Configurar Maestra o Esclava")
        self.card_prov = CarteleriaCard("Proveedores", "🚚", "#E0F2FE", "#075985", "Compras y Stock")

        self.card_tv.clicked.connect(self._on_launch_tv)
        self.card_admin.clicked.connect(self._on_launch_admin)
        self.card_inv.clicked.connect(self._on_launch_inv)
        self.card_png.clicked.connect(self._on_launch_png)
        self.card_ofe.clicked.connect(self._on_launch_ofe)
        self.card_red.clicked.connect(self._on_launch_red)
        self.card_prov.clicked.connect(self._on_launch_prov)

        grid.addWidget(self.card_tv, 0, 0)
        grid.addWidget(self.card_admin, 0, 1)
        grid.addWidget(self.card_inv, 0, 2)
        grid.addWidget(self.card_png, 1, 0)
        grid.addWidget(self.card_ofe, 1, 1)
        grid.addWidget(self.card_red, 1, 2)
        grid.addWidget(self.card_prov, 2, 0)
        
        page_lay.addLayout(grid)
        page_lay.addStretch()

        self.scroll_area.setWidget(self.page)
        root.addWidget(self.scroll_area)
        
        # Apply initial theme
        from src.utils.theme_manager import theme_manager
        self.apply_dashboard_theme(theme_manager.is_dark())

    def apply_dashboard_theme(self, is_dark):
        if is_dark:
            self.nav.setStyleSheet("background: #0F172A; border-bottom: 1px solid #334155;")
            self.brand_lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #F8FAFC; background: transparent; border: none;")
            self.lbl_clock.setStyleSheet("font-size: 12px; font-weight: 600; color: #94A3B8; background: transparent; border: none; margin-right: 16px;")
            self.btn_theme.setStyleSheet("""
                QPushButton {
                    background: #1E293B; color: #94A3B8;
                    border: 1.5px solid #334155; border-radius: 8px;
                    padding: 0 16px; font-weight: 700; font-size: 12px; margin-right: 8px;
                }
                QPushButton:hover { background: #334155; color: #F8FAFC; border-color: #475569; }
            """)
            self.btn_out.setStyleSheet("""
                QPushButton {
                    background: #1E293B; color: #94A3B8;
                    border: 1.5px solid #334155; border-radius: 8px;
                    padding: 0 16px; font-weight: 700; font-size: 12px;
                }
                QPushButton:hover { background: #7F1D1D; color: #FECACA; border-color: #991B1B; }
            """)
            self.scroll_area.setStyleSheet("QScrollArea { border: none; background: #020617; }")
            self.lbl_modulos.setStyleSheet("font-size: 18px; font-weight: bold; color: #F8FAFC;")
        else:
            self.nav.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
            self.brand_lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #0F172A; background: transparent; border: none;")
            self.lbl_clock.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569; background: transparent; border: none; margin-right: 16px;")
            self.btn_theme.setStyleSheet("""
                QPushButton {
                    background: #F1F5F9; color: #475569;
                    border: 1.5px solid #E2E8F0; border-radius: 8px;
                    padding: 0 16px; font-weight: 700; font-size: 12px; margin-right: 8px;
                }
                QPushButton:hover { background: #E2E8F0; color: #0F172A; border-color: #CBD5E1; }
            """)
            self.btn_out.setStyleSheet("""
                QPushButton {
                    background: #F1F5F9; color: #475569;
                    border: 1.5px solid #E2E8F0; border-radius: 8px;
                    padding: 0 16px; font-weight: 700; font-size: 12px;
                }
                QPushButton:hover { background: #FEE2E2; color: #EF4444; border-color: #FECACA; }
            """)
            self.scroll_area.setStyleSheet("QScrollArea { border: none; background: #F8FAFC; }")
            self.lbl_modulos.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
            
        self.card_tv.apply_theme(is_dark)
        self.card_admin.apply_theme(is_dark)
        self.card_inv.apply_theme(is_dark)
        self.card_png.apply_theme(is_dark)
        self.card_ofe.apply_theme(is_dark)
        self.card_red.apply_theme(is_dark)
        self.card_prov.apply_theme(is_dark)

    def _tick(self):
        ahora = datetime.datetime.now()
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        t_str = f"{ahora.day} {meses[ahora.month-1]} - {ahora.strftime('%H:%M')}"
        self.lbl_clock.setText(t_str)

    def _on_launch_tv(self):
        increment_stat("Lanzar_TV")
        # Usar lanzador directo sin consola Qt intermedia
        try:
            from src.carteleria.lanzador_tv.lanzador_directo import get_lanzador_directo
            lanzador = get_lanzador_directo()
            if not lanzador.lanzar():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "Error",
                    "No se pudo lanzar la cartelería TV.",
                )
        except Exception as e:
            # Fallback al método original con consola Qt
            self.request_launch_tv.emit()

    def _on_launch_admin(self):
        increment_stat("Admin_TV")
        # Modo avanzado con consola Qt (F10/F11 funcionan desde la consola)
        self.request_admin_tv.emit()

    def _on_launch_inv(self):
        increment_stat("Inventario")
        self.request_inventario.emit()

    def _on_launch_png(self):
        increment_stat("PNG_Productos")
        if self.receivers(self.request_png_productos) > 0:
            self.request_png_productos.emit()
            return
        self._abrir_png_local()

    def _abrir_png_local(self):
        from src.carteleria.png_productos.panel_png_productos import PanelPngProductos
        if self._png_overlay is None:
            self._png_overlay = PanelPngProductos(self)
            self._png_overlay.setStyleSheet(
                self._png_overlay.styleSheet() + " QWidget { background: #F8FAFC; }"
            )
            self._png_overlay.volver.connect(self._cerrar_png)
            self.layout().addWidget(self._png_overlay)
        self.scroll_area.hide()
        self.nav.hide()
        self._png_overlay.show()
        self._png_overlay.raise_()

    def _cerrar_png(self):
        if self._png_overlay:
            self._png_overlay.hide()
        self.nav.show()
        self.scroll_area.show()

    def _on_launch_ofe(self):
        increment_stat("Ofertas")
        self.request_ofertas.emit()

    def _on_launch_red(self):
        increment_stat("Red_LAN")
        self.request_red_lan.emit()

    def _on_launch_prov(self):
        increment_stat("Proveedores")
        self.request_proveedores.emit()
