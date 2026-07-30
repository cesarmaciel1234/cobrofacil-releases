from PyQt6.QtWidgets import QScrollArea, QFrame, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from src.carteleria.theme import C_THEME, apply_apple_shadow

class GrillaPrecios(QFrame):
    """
    Zona 2: Lista AutoScroll (Envuelto en un Frame estilo Apple)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        from src.carteleria.motor_carteleria.motor_grilla import MotorGrilla
        self.motor = MotorGrilla(self)
        self.motor.datos_listos.connect(self.set_items)
        
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.motor.start)
        self.auto_refresh_timer.start(30000) # 30 segundos
        self.motor.start() # Carga inicial
        from src.carteleria.theme import get_active_theme_name
        if get_active_theme_name() == "temu":
            # Estilo asiático: Borde sólido Naranja brillante sin defectos de renderización
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; border: 4px solid #FF5722;")
        else:
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
            apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8) # Margen optimizado para evitar pérdida de espacio en pantallas estrechas
        
        from PyQt6.QtWidgets import QSizePolicy
        self.scroll_area = _AutoScrollList()
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.scroll_area)
        
        self.last_items = {}
        
    def set_layout_mode(self, mode):
        self.scroll_area.current_mode = mode
        if self.last_items:
            self.set_items(self.last_items)
            
    def set_items(self, items_by_category):
        self.last_items = items_by_category
        self.scroll_area.set_items(items_by_category)


class _AutoScrollList(QScrollArea):
    """Componente interno que maneja el scroll y renderizado de ítems"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: transparent; border: none;")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        
        # ¡BLINDAJE DEFINITIVO CONTRA RECORTE HORIZONTAL!
        # Sobreescribimos minimumSizeHint para que el ancho mínimo sea 0 y Qt NUNCA extienda el contenedor más allá del viewport
        from PyQt6.QtCore import QSize
        self.container.minimumSizeHint = lambda: QSize(0, self.container.layout().minimumSize().height() if self.container.layout() else 0)
        
        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(2, 4, 2, 4) # Márgenes internos compactos
        self.inner_layout.setSpacing(10)
        self.setWidget(self.container)
        
        self._scroll_pos = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._do_scroll)
        self.current_mode = 4

    def set_items(self, items_by_category):
        # Evitar reconstruir la UI si los datos no cambiaron (previene congelamiento)
        current_data_repr = str(items_by_category)
        if getattr(self, '_last_data_repr', None) == current_data_repr:
            return
        self._last_data_repr = current_data_repr

        for i in reversed(range(self.inner_layout.count())):
            w = self.inner_layout.itemAt(i).widget()
            if w: w.deleteLater()
                
        for _ in range(3): 
            for categoria, productos in items_by_category.items():
                if not productos:
                    continue # Nunca dibujar categorías vacías (ej: 'ACHURAS' sin stock)
                
                # ── CATEGORÍA: ESTILO BANNER MULTINACIONAL CON ICONO ──
                cat_upper = categoria.upper()
                icono = "⭐"
                if any(w in cat_upper for w in ["CARNE", "VACUNO", "ASADO", "LOMO", "BIFE", "NOVILLO", "TERNERA", "ACHURAS", "ACHURA", "MENUDENCIAS", "MONDONGO"]):
                    icono = "🥩"
                elif any(w in cat_upper for w in ["POLLO", "AVE", "PATA", "SUPREMA", "PECHUGA", "ALITA"]):
                    icono = "🍗"
                elif any(w in cat_upper for w in ["CERDO", "BONDIOLA", "PECHITO", "CHUCHETO", "LECHON"]):
                    icono = "🥓"
                elif any(w in cat_upper for w in ["CHORIZO", "MORCILLA", "EMBUTIDO", "SALCHICHA", "SALAME"]):
                    icono = "🌭"
                elif any(w in cat_upper for w in ["OFERTA", "PROMO", "COMBO", "DESTACADO", "RELAMPAGO"]):
                    icono = "🔥"
                elif any(w in cat_upper for w in ["QUESO", "FIAMBRE", "LACTEO", "JAMON", "PROVOLETA"]):
                    icono = "🧀"

                lbl_cat = QLabel(f"{icono} {cat_upper}")
                from src.carteleria.theme import get_active_theme_name
                is_temu = (get_active_theme_name() == "temu")
                
                if is_temu:
                    fs_cat = 46 if self.current_mode == 1 else 36
                    # Degradado Azul Zafiro Premium con borde luminoso
                    lbl_cat.setStyleSheet(f"""
                        QLabel {{ 
                            font-family: 'Arial Black', 'Segoe UI Black', sans-serif; 
                            font-size: {fs_cat}px; 
                            font-weight: 900; 
                            color: #FFFFFF; 
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #002663, stop:0.5 #0045B5, stop:1 #002663); 
                            border: 2px solid #3B82F6; 
                            padding: 8px 14px; 
                            border-radius: 14px; 
                            margin-top: 16px; 
                            margin-bottom: 6px; 
                            letter-spacing: 1px; 
                        }}
                    """)
                else:
                    fs_cat = 42 if self.current_mode == 1 else 32
                    lbl_cat.setStyleSheet(f"""
                        QLabel {{ 
                            font-family: -apple-system, 'Segoe UI'; 
                            font-size: {fs_cat}px; 
                            font-weight: 900; 
                            color: #FFFFFF; 
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:0.5 #2563EB, stop:1 #1E3A8A); 
                            border: 1px solid #60A5FA; 
                            padding: 8px 14px; 
                            border-radius: 14px; 
                            margin-top: 16px; 
                            margin-bottom: 6px; 
                        }}
                    """)
                lbl_cat.setWordWrap(True)
                lbl_cat.setMinimumWidth(0)
                from PyQt6.QtWidgets import QSizePolicy
                lbl_cat.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.MinimumExpanding)
                lbl_cat.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.inner_layout.addWidget(lbl_cat)
                
                # ── PRODUCTOS: TARJETAS MODULARES CON SUB-CONTENEDORES ESTRICTOS ──
                from src.carteleria.interfaz_principal.tarjeta_producto import TarjetaProducto
                for nombre, precio, precio_oferta, regla in productos:
                    if not nombre or not nombre.strip():
                        continue
                    tarjeta = TarjetaProducto(nombre, precio, precio_oferta, regla, modo_tv=self.current_mode, parent=self.container)
                    self.inner_layout.addWidget(tarjeta)
                    
        # Resorte inferior para que, si hay pocos productos, se alineen limpiamente arriba en vez de estirarse
        self.inner_layout.addStretch(1)
        self.timer.start(50)

    def _do_scroll(self):
        bar = self.verticalScrollBar()
        max_val = bar.maximum()
        if max_val == 0: return
        self._scroll_pos += 2
        if self._scroll_pos > (max_val * 0.6):
            self._scroll_pos = 0
        bar.setValue(self._scroll_pos)
