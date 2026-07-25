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
            # Estilo asiático: Bordes punteados de cupón / Naranja-Rojo brillante
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; border: 6px dashed #FF5722;")
        else:
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
            apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 12) # Simetría perfecta (14px tanto a izquierda como derecha)
        
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
        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(4, 6, 4, 6) # Margen simétrico para que las tarjetas alineen con los banners
        self.inner_layout.setSpacing(12)
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
                # ── CATEGORÍA: ESTILO BANNER MULTINACIONAL CON ICONO ──
                cat_upper = categoria.upper()
                icono = "⭐"
                if any(w in cat_upper for w in ["CARNE", "VACUNO", "ASADO", "LOMO", "BIFE", "NOVILLO", "TERNERA"]):
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
                    # Degradado Azul Zafiro Premium con borde luminoso: genera un contraste irresistible contra los precios rojos y amarillos
                    lbl_cat.setStyleSheet(f"""
                        QLabel {{ 
                            font-family: 'Impact', 'Arial Black', sans-serif; 
                            font-size: {fs_cat}px; 
                            font-weight: 900; 
                            color: #FFFFFF; 
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #002663, stop:0.5 #0045B5, stop:1 #002663); 
                            border: 2px solid #3B82F6; 
                            padding: 8px 18px; 
                            border-radius: 14px; 
                            margin-top: 18px; 
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
                            padding: 8px 18px; 
                            border-radius: 14px; 
                            margin-top: 18px; 
                            margin-bottom: 6px; 
                        }}
                    """)
                lbl_cat.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.inner_layout.addWidget(lbl_cat)
                
                # ── PRODUCTOS: TARJETAS ALTAS ESTILO MULTINACIONAL ──
                for nombre, precio, precio_oferta, regla in productos:
                    row = QFrame()
                    row.setObjectName("PriceRow")
                    
                    # ── ARQUITECTURA DE ALTURA Y SIMETRÍA (NOMBRES LARGOS RECIEN ALTURA DE OFERTA) ──
                    len_n = len(nombre.strip())
                    es_nombre_largo = (len_n > 11) # "Milanesa de Pollo", "Asado Americano", "Bondiola De Cerdo"
                    
                    if self.current_mode == 1:
                        base_h = 142
                        extra_h_largo = 48 if es_nombre_largo else 0
                        extra_h_regla = 46 if regla else 0
                    else:
                        base_h = 118 # Altura incrementada para amoldar el nuevo padding vertical del texto
                        extra_h_largo = 44 if es_nombre_largo else 0
                        extra_h_regla = 38 if regla else 0
                        
                    calc_height = base_h + extra_h_largo + extra_h_regla
                    row.setMinimumHeight(calc_height)
                    from PyQt6.QtWidgets import QSizePolicy
                    row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                    
                    if is_temu:
                        row.setStyleSheet("""
                            #PriceRow { 
                                background: #FFFFFF; 
                                border-radius: 16px; 
                                border: 2px solid #FECACA; 
                            }
                        """)
                    else:
                        row.setStyleSheet("""
                            #PriceRow { 
                                background: #FFFFFF; 
                                border-radius: 16px; 
                                border: 1px solid rgba(0,0,0,0.12); 
                            }
                        """)
                    
                    # Layout Principal de Tarjeta (Márgenes equilibrados que impiden desborde horizontal)
                    card_lay = QVBoxLayout(row) 
                    card_lay.setContentsMargins(14, 12, 14, 12)
                    card_lay.setSpacing(6)
                    card_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                    
                    # ── SECCIÓN SUPERIOR: CORTE A LA IZQ | PRECIOS A LA DERECHA ──
                    top_lay = QHBoxLayout()
                    top_lay.setContentsMargins(0, 0, 0, 0)
                    top_lay.setSpacing(10)
                    top_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                    
                    # Fuente equilibrada y legible (3 niveles adaptativos al largo)
                    if len_n <= 11: # Nombres cortos (Alitas, Lomo, Asado, Carcaza)
                        fs_n = 46 if self.current_mode == 1 else 32
                    elif len_n <= 20: # Nombres medianos (Bondiola De Cerdo, Milanesa de Pollo) -> entran perfecto sin amontonarse
                        fs_n = 42 if self.current_mode == 1 else 27
                    else: # Nombres excepcionalmente largos
                        fs_n = 38 if self.current_mode == 1 else 24
                        
                    lbl_n = QLabel(nombre)
                    lbl_n.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    if is_temu:
                        # Relleno vertical y caja expandida para que los nombres de 2 o 3 líneas jamás sean comprimidos por el layout
                        lbl_n.setStyleSheet(f"QLabel {{ font-family: 'Impact', 'Segoe UI Black', sans-serif; font-size: {fs_n}px; font-weight: 800; color: #1E293B; background: transparent; border: none; letter-spacing: 0.5px; padding: 4px 2px; }}")
                    else:
                        lbl_n.setStyleSheet(f"QLabel {{ font-family: -apple-system, 'Segoe UI'; font-size: {fs_n}px; font-weight: 800; color: {C_THEME['text']}; background: transparent; border: none; padding: 4px 2px; }}")
                    lbl_n.setWordWrap(True)
                    
                    # ── SOLUCIÓN DEFINTIVA DE RECORTE VERTICAL EN NOMBRES LARGOS ──
                    if es_nombre_largo:
                        lbl_n.setMinimumHeight(92 if self.current_mode != 1 else 120)
                    else:
                        lbl_n.setMinimumHeight(48 if self.current_mode != 1 else 60)
                    from PyQt6.QtWidgets import QSizePolicy
                    lbl_n.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    
                    top_lay.addWidget(lbl_n, stretch=1)
                    
                    # Bloque de Precios (Derecha en perfecta alineación y sin excesos de anchura)
                    if precio_oferta > 0:
                        fs_old = 28 if self.current_mode == 1 else 22
                        lbl_old = QLabel(f"<s>${precio:,.0f}</s>")
                        lbl_old.setStyleSheet(f"QLabel {{ font-family: -apple-system, 'Segoe UI', sans-serif; font-size: {fs_old}px; font-weight: 700; color: #94A3B8; background: transparent; border: none; }}")
                        lbl_old.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        
                        lbl_p = QLabel(f"${precio_oferta:,.0f}")
                        if is_temu:
                            fs_p = 46 if self.current_mode == 1 else 32
                            pad_h = "4px 14px" if self.current_mode == 1 else "2px 8px"
                            lbl_p.setStyleSheet(f"QLabel {{ font-family: 'Impact', 'Arial Black', sans-serif; font-size: {fs_p}px; font-weight: 900; color: #FFFF00; background-color: #DC2626; padding: {pad_h}; border-radius: 8px; border: none; }}")
                        else:
                            fs_p = 44 if self.current_mode == 1 else 32
                            pad_h = "4px 14px" if self.current_mode == 1 else "2px 8px"
                            lbl_p.setStyleSheet(f"QLabel {{ font-family: -apple-system, 'Segoe UI', sans-serif; font-size: {fs_p}px; font-weight: 900; color: #FFFFFF; background-color: {C_THEME['accent']}; padding: {pad_h}; border-radius: 8px; border: none; }}")
                        lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        
                        precios_lay = QVBoxLayout()
                        precios_lay.setContentsMargins(0, 0, 0, 0)
                        precios_lay.setSpacing(2)
                        precios_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
                        precios_lay.addWidget(lbl_old, 0, Qt.AlignmentFlag.AlignRight)
                        precios_lay.addWidget(lbl_p, 0, Qt.AlignmentFlag.AlignRight)
                        top_lay.addLayout(precios_lay)
                    else:
                        lbl_p = QLabel(f"${precio:,.0f}")
                        if is_temu:
                            fs_p = 50 if self.current_mode == 1 else 36
                            lbl_p.setStyleSheet(f"QLabel {{ font-family: 'Impact', 'Arial Black', sans-serif; font-size: {fs_p}px; font-weight: 900; color: #DC2626; background: transparent; border: none; }}")
                        else:
                            fs_p = 46 if self.current_mode == 1 else 34
                            lbl_p.setStyleSheet(f"QLabel {{ font-family: -apple-system, 'Segoe UI', sans-serif; font-size: {fs_p}px; font-weight: 800; color: {C_THEME['accent']}; background: transparent; border: none; }}")
                        lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        top_lay.addWidget(lbl_p, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        
                    card_lay.addLayout(top_lay, stretch=1)
                    
                    # ── PIE DE TARJETA CON LÍNEA DIVISORIA (EXCLUSIVO PARA REGLAS Y PROMOS) ──
                    if regla:
                        linea = QFrame()
                        linea.setFrameShape(QFrame.Shape.HLine)
                        linea.setFixedHeight(1)
                        if is_temu:
                            linea.setStyleSheet("background: rgba(220, 38, 38, 0.2); border: none; max-height: 1px;")
                        else:
                            linea.setStyleSheet("background: rgba(0, 0, 0, 0.1); border: none; max-height: 1px;")
                        card_lay.addWidget(linea)
                        
                        fs_r = 23 if self.current_mode == 1 else 17
                        lbl_r = QLabel(f"🔥 {regla.strip()}")
                        lbl_r.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                        lbl_r.setStyleSheet(f"QLabel {{ font-family: 'Arial', sans-serif; font-size: {fs_r}px; font-weight: 800; color: #008C4A; background: transparent; border: none; padding-top: 2px; }}")
                        lbl_r.setWordWrap(True)
                        card_lay.addWidget(lbl_r)
                        
                    self.inner_layout.addWidget(row)
                
        self.timer.start(50) 

    def _do_scroll(self):
        bar = self.verticalScrollBar()
        max_val = bar.maximum()
        if max_val == 0: return
        self._scroll_pos += 2
        if self._scroll_pos > (max_val * 0.6):
            self._scroll_pos = 0
        bar.setValue(self._scroll_pos)
