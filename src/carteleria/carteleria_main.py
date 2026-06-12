import os
import json
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QStackedWidget, QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont, QPixmap

try:
    from src.base_de_datos.database import Database
except ImportError:
    Database = None

logger = logging.getLogger("Carteleria")

# ── Tema de Cartelería ────────────────────────────────────────────────────────
C_THEME = {
    "bg": "#0B0F19",          # Fondo ultra oscuro (High Contrast)
    "surface": "#111827",     # Paneles
    "accent": "#8B5CF6",      # Violeta vibrante
    "text": "#F8FAFC",        # Blanco puro
    "text_muted": "#94A3B8",  # Gris claro
    "sos_bg": "#EF4444",      # Rojo vibrante alerta
    "sos_text": "#FFFFFF",
}

class AutoScrollList(QScrollArea):
    """Lista que hace scroll infinito automáticamente (Efecto Créditos de Película)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background: transparent; border: none;")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        self.setWidget(self.container)
        
        self._scroll_pos = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._do_scroll)

    def set_items(self, items):
        # Limpiar
        for i in reversed(range(self.layout.count())):
            w = self.layout.itemAt(i).widget()
            if w:
                w.deleteLater()
                
        # Llenar 3 veces para dar el efecto de loop infinito más fluido
        for _ in range(3):
            for nombre, precio in items:
                row = QFrame()
                row.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 12px; border: 1px solid #1F2937;")
                row_lay = QHBoxLayout(row)
                row_lay.setContentsMargins(20, 15, 20, 15)
                
                lbl_n = QLabel(nombre.upper())
                lbl_n.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {C_THEME['text']}; font-family: 'Inter';")
                lbl_p = QLabel(f"${precio:,.2f}")
                lbl_p.setStyleSheet(f"font-size: 28px; font-weight: 900; color: #10B981; font-family: 'Inter';")
                
                row_lay.addWidget(lbl_n)
                row_lay.addStretch()
                row_lay.addWidget(lbl_p)
                self.layout.addWidget(row)
                
        self.timer.start(50) # Cada 50ms

    def _do_scroll(self):
        bar = self.verticalScrollBar()
        max_val = bar.maximum()
        if max_val == 0:
            return
            
        self._scroll_pos += 1
        
        # Resetear si llegamos a 1/3 del final (para el loop infinito)
        if self._scroll_pos > (max_val * 0.6):
            self._scroll_pos = 0
            
        bar.setValue(self._scroll_pos)


class CarteleriaMain(QWidget):
    """
    Cartelería Digital Nivel Grido
    Soporta layouts de 2 y 4 zonas, y lanza alertas de "Oferta Relámpago" 
    conectadas a la Base de Datos.
    """
    request_logout = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CarteleriaMain")
        self.setStyleSheet(f"background-color: {C_THEME['bg']};")
        
        self.layout_mode = 2 # 2 o 4 zonas
        self._build_ui()
        
        # Timers
        self.timer_carousel = QTimer(self)
        self.timer_carousel.timeout.connect(self._next_image)
        self.timer_carousel.start(6000) # Cambia cada 6 seg
        
        self.timer_sos = QTimer(self)
        self.timer_sos.timeout.connect(self._check_oferta_relampago)
        self.timer_sos.start(1000) # Chequea cada segundo
        
        self.img_index = 0
        self.images = []

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        # ── STACKED WIDGET (Normal vs Oferta Relámpago) ──
        self.stack = QStackedWidget()
        
        # 1. Pantalla Normal Multi-Zona
        self.page_normal = QWidget()
        self._build_layout_normal()
        self.stack.addWidget(self.page_normal)
        
        # 2. Pantalla Oferta Relámpago (SOS)
        self.page_sos = QWidget()
        self._build_layout_sos()
        self.stack.addWidget(self.page_sos)
        
        root.addWidget(self.stack)

    def _build_layout_normal(self):
        lay = QVBoxLayout(self.page_normal)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(20)
        
        # Botones de control (ocultos o sutiles en producción, útiles para salir)
        top_bar = QHBoxLayout()
        btn_exit = QPushButton("⎋ Salir")
        btn_exit.setFixedSize(100, 36)
        btn_exit.setStyleSheet("background: rgba(255,255,255,0.1); color: #FFF; border-radius: 18px;")
        btn_exit.clicked.connect(self.request_logout.emit)
        
        btn_toggle = QPushButton("◩ Cambiar a 4 Zonas")
        btn_toggle.setFixedSize(180, 36)
        btn_toggle.setStyleSheet("background: #8B5CF6; color: #FFF; border-radius: 18px; font-weight: bold;")
        btn_toggle.clicked.connect(self._toggle_layout)
        
        top_bar.addWidget(btn_exit)
        top_bar.addStretch()
        top_bar.addWidget(btn_toggle)
        lay.addLayout(top_bar)
        
        # Contenedor Grid Principal
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(20)
        
        # Zona 1: Carrusel
        self.lbl_carousel = QLabel("ZONA 1\nEsperando Promociones...")
        self.lbl_carousel.setAlignment(Qt.AlignCenter)
        self.lbl_carousel.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; font-size: 32px; color: {C_THEME['text_muted']}; border: 2px dashed #334155;")
        
        # Zona 2: Lista de Precios Scroll
        self.lista_precios = AutoScrollList()
        
        # Añadir al grid (Por defecto 2 zonas)
        self.grid.addWidget(self.lbl_carousel, 0, 0, 1, 2) # 66% width
        self.grid.addWidget(self.lista_precios, 0, 2, 1, 1) # 33% width
        self.grid.setColumnStretch(0, 2)
        self.grid.setColumnStretch(2, 1)
        
        lay.addWidget(self.grid_container, 1)
        
        # Zona 3: Zócalo de Noticias (Marquesina)
        self.zocalo = QLabel("🚀 ¡Bienvenidos! Las mejores ofertas están aquí. Pregunta en caja por el descuento en efectivo. 🚀")
        self.zocalo.setFixedHeight(60)
        self.zocalo.setStyleSheet(f"background: #1E1B4B; color: #C4B5FD; font-size: 24px; font-weight: 800; border-radius: 30px; padding-left: 20px;")
        lay.addWidget(self.zocalo)

    def _build_layout_sos(self):
        lay = QVBoxLayout(self.page_sos)
        lay.setContentsMargins(0, 0, 0, 0)
        self.page_sos.setStyleSheet(f"background: {C_THEME['sos_bg']};")
        
        self.lbl_sos_title = QLabel("⚡ OFERTA RELÁMPAGO ⚡")
        self.lbl_sos_title.setAlignment(Qt.AlignCenter)
        self.lbl_sos_title.setStyleSheet("font-size: 100px; font-weight: 900; color: #FFFFFF; font-family: 'Inter';")
        
        self.lbl_sos_desc = QLabel("Desc. 50% en Todo el Helado")
        self.lbl_sos_desc.setAlignment(Qt.AlignCenter)
        self.lbl_sos_desc.setStyleSheet("font-size: 60px; font-weight: 800; color: #FEF08A; font-family: 'Inter';")
        
        self.lbl_sos_time = QLabel("¡SOLO POR 15 MINUTOS!")
        self.lbl_sos_time.setAlignment(Qt.AlignCenter)
        self.lbl_sos_time.setStyleSheet("font-size: 40px; font-weight: 900; color: #FFFFFF; background: #B91C1C; border-radius: 20px; padding: 20px;")
        
        lay.addStretch()
        lay.addWidget(self.lbl_sos_title)
        lay.addSpacing(30)
        lay.addWidget(self.lbl_sos_desc)
        lay.addSpacing(50)
        
        wrap_time = QHBoxLayout()
        wrap_time.addStretch()
        wrap_time.addWidget(self.lbl_sos_time)
        wrap_time.addStretch()
        lay.addLayout(wrap_time)
        lay.addStretch()

    def _toggle_layout(self):
        # Limpiar grid
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)
            
        if self.layout_mode == 2:
            self.layout_mode = 4
            self.sender().setText("◧ Cambiar a 2 Zonas")
            
            # ZONA 1 (Top Left)
            self.grid.addWidget(self.lbl_carousel, 0, 0)
            # ZONA 2 (Right Col)
            self.grid.addWidget(self.lista_precios, 0, 1, 2, 1)
            
            # ZONA 3 (Bottom Left 1)
            z3 = QLabel("NOVEDADES\nPróximamente...")
            z3.setAlignment(Qt.AlignCenter)
            z3.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; font-size: 24px; color: #10B981;")
            self.grid.addWidget(z3, 1, 0)
            
            self.grid.setColumnStretch(0, 1)
            self.grid.setColumnStretch(1, 1)
            self.grid.setRowStretch(0, 2)
            self.grid.setRowStretch(1, 1)
        else:
            self.layout_mode = 2
            self.sender().setText("◩ Cambiar a 4 Zonas")
            self.grid.addWidget(self.lbl_carousel, 0, 0, 1, 2)
            self.grid.addWidget(self.lista_precios, 0, 2, 1, 1)
            self.grid.setColumnStretch(0, 2)
            self.grid.setColumnStretch(2, 1)

    def _next_image(self):
        # Simular lectura de carpeta /assets/publicidad
        # Como no tenemos imgs reales ahora, alternamos el fondo
        colors = ["#1E1B4B", "#064E3B", "#451A03", "#082F49"]
        texts = ["🍔 MEGA COMBO FAMILIAR", "🍦 2x1 EN HELADOS POSTRE", "🍕 LLEVÁ 3 PAGÁ 2", "🍟 PAPAS CON CHEDDAR"]
        self.img_index = (self.img_index + 1) % len(colors)
        
        self.lbl_carousel.setText(texts[self.img_index])
        self.lbl_carousel.setStyleSheet(f"background: {colors[self.img_index]}; border-radius: 20px; font-size: 60px; font-weight: 900; color: #FFFFFF;")

    def _check_oferta_relampago(self):
        """Chequea si el Administrador lanzó un SOS desde un archivo JSON o BD"""
        try:
            from src.utils.paths import get_base_path
            path = os.path.join(get_base_path(), "data", "oferta_relampago.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    oferta = json.load(f)
                
                if oferta.get("activa", False):
                    if self.stack.currentIndex() != 1:
                        self.lbl_sos_desc.setText(oferta.get("mensaje", "¡SÚPER DESCUENTO!"))
                        self.stack.setCurrentIndex(1)
                else:
                    if self.stack.currentIndex() != 0:
                        self.stack.setCurrentIndex(0)
            else:
                if self.stack.currentIndex() != 0:
                    self.stack.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error checking SOS Oferta: {e}")

    def cargar_datos(self):
        """Lee productos de la Base de Datos para el Scroll"""
        try:
            if Database:
                db = Database.get_instance()
                rows = db.execute("SELECT nombre, precio FROM productos WHERE precio > 0 ORDER BY nombre LIMIT 50")
                if rows:
                    self.lista_precios.set_items(rows)
                else:
                    self._cargar_demo()
            else:
                self._cargar_demo()
        except Exception as e:
            logger.error(f"DB Error carteleria: {e}")
            self._cargar_demo()

    def _cargar_demo(self):
        demo = [
            ("Combo Hamburguesa + Papas", 8500),
            ("Pizza Muzzarella Grande", 9200),
            ("Helado 1 Kg - Sabores a elección", 6500),
            ("Gaseosa Cola 1.5L", 2100),
            ("Empanadas x Docena (Horno)", 11000),
            ("Lomo Completo c/ Fritas", 9800),
            ("Cerveza Artesanal IPA 500ml", 3500),
            ("Postre Tiramisú Porción", 4200),
        ]
        self.lista_precios.set_items(demo)
