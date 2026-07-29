from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt
from src.carteleria.theme import C_THEME

class TarjetaProducto(QFrame):
    """
    Contenedor modular independiente para cada producto en la grilla de precios.
    Divide la tarjeta en contenedores estrictos para garantizar 0% solapamiento, 
    alineación vertical perfecta y evitar recortes de símbolos como '$'.
    """
    def __init__(self, nombre, precio, precio_oferta=0, regla="", modo_tv=1, parent=None):
        super().__init__(parent)
        self.nombre = nombre.strip()
        self.precio = precio
        self.precio_oferta = precio_oferta
        self.regla = regla
        self.modo_tv = modo_tv
        
        from src.carteleria.theme import get_active_theme_name
        self.is_temu = (get_active_theme_name() == "temu")
        
        self._init_contenedor_principal()
        self._construir_subcontenedores()
        
    def _init_contenedor_principal(self):
        self.setObjectName("PriceRow")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        
        # Calcular alturas mínimas equilibradas para asegurar visibilidad en TV
        len_n = len(self.nombre)
        es_nombre_largo = (len_n > 14)
        
        if self.modo_tv == 1:
            base_h = 115
            extra_h_largo = 25 if es_nombre_largo else 0
            extra_h_regla = 32 if self.regla else 0
        else:
            base_h = 95
            extra_h_largo = 20 if es_nombre_largo else 0
            extra_h_regla = 25 if self.regla else 0
            
        self.setMinimumHeight(base_h + extra_h_largo + extra_h_regla)
        
        if self.is_temu:
            self.setStyleSheet("""
                #PriceRow { 
                    background: #FFFFFF; 
                    border-radius: 16px; 
                    border: 3px solid #E1251B; 
                }
            """)
        else:
            self.setStyleSheet("""
                #PriceRow { 
                    background: #FFFFFF; 
                    border-radius: 16px; 
                    border: 2px solid #94A3B8; 
                }
            """)
            
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(14, 10, 14, 10)
        self.main_lay.setSpacing(6)
        self.main_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
    def _construir_subcontenedores(self):
        # ── CONTENEDOR SUPERIOR (PRODUCTO + PRECIOS) ──
        self.top_container = QWidget()
        self.top_container.setStyleSheet("background: transparent; border: none;")
        self.top_lay = QHBoxLayout(self.top_container)
        self.top_lay.setContentsMargins(0, 0, 0, 0)
        self.top_lay.setSpacing(14) # Espacio de respiración entre producto y precio
        self.top_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # 1. Sub-contenedor Izquierdo: PRODUCTO
        self._build_contenedor_producto()
        self.top_lay.addWidget(self.lbl_producto, stretch=1)
        
        # 2. Sub-contenedor Derecho: PRECIOS
        self.precios_container = QWidget()
        self.precios_container.setStyleSheet("background: transparent; border: none;")
        # Evitar recorte del símbolo '$' en precios con etiqueta roja
        self.precios_container.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        
        self.precios_lay = QVBoxLayout(self.precios_container)
        self.precios_lay.setContentsMargins(0, 0, 0, 0)
        self.precios_lay.setSpacing(2)
        
        # Los stretch superior e inferior garantizan alineación vertical al centro absoluto
        self.precios_lay.addStretch(1)
        self._build_contenedor_precios()
        self.precios_lay.addStretch(1)
        
        self.top_lay.addWidget(self.precios_container, stretch=0)
        self.main_lay.addWidget(self.top_container, stretch=1)
        
        # 3. Sub-contenedor Inferior: CINTA PROMOCIONAL (Si aplica)
        self._build_contenedor_cinta()

    def _build_contenedor_producto(self):
        len_n = len(self.nombre)
        p_val = self.precio_oferta if self.precio_oferta > 0 else self.precio
        p_str = f"${p_val:,.0f}"
        es_precio_largo = len(p_str) >= 7
        max_word_len = max([len(w) for w in self.nombre.split()]) if self.nombre else 0
        
        if len_n <= 9 and max_word_len <= 9 and not es_precio_largo:
            fs_n = 38 if self.modo_tv == 1 else 27
        elif len_n <= 14 and max_word_len <= 10:
            fs_n = 32 if self.modo_tv == 1 else 23
        elif max_word_len > 10:
            fs_n = 22 if self.modo_tv == 1 else 17
        else:
            fs_n = 26 if self.modo_tv == 1 else 19
            
        self.lbl_producto = QLabel(self.nombre)
        self.lbl_producto.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        if self.is_temu:
            self.lbl_producto.setStyleSheet(f"QLabel {{ font-family: 'Segoe UI Black', 'Arial Black', sans-serif; font-size: {fs_n}px; font-weight: 800; color: #1E293B; letter-spacing: 0.3px; padding: 2px 0px; }}")
        else:
            self.lbl_producto.setStyleSheet(f"QLabel {{ font-family: -apple-system, 'Segoe UI'; font-size: {fs_n}px; font-weight: 800; color: {C_THEME['text']}; padding: 2px 0px; }}")
            
        self.lbl_producto.setWordWrap(True)
        self.lbl_producto.setMinimumWidth(0)
        self.lbl_producto.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def _build_contenedor_precios(self):
        p_val = self.precio_oferta if self.precio_oferta > 0 else self.precio
        p_str = f"${p_val:,.0f}"
        es_precio_largo = len(p_str) >= 7
        
        if self.precio_oferta > 0:
            fs_old = 22 if self.modo_tv == 1 else 16
            lbl_old = QLabel(f"<s>${self.precio:,.0f}</s>")
            lbl_old.setMinimumWidth(0)
            lbl_old.setStyleSheet(f"QLabel {{ font-family: -apple-system, 'Segoe UI', sans-serif; font-size: {fs_old}px; font-weight: 700; color: #94A3B8; }}")
            lbl_old.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.precios_lay.addWidget(lbl_old, 0, Qt.AlignmentFlag.AlignRight)
            
            lbl_p = QLabel(f"${self.precio_oferta:,.0f}")
            lbl_p.setMinimumWidth(0)
            if self.is_temu:
                fs_p = (34 if self.modo_tv == 1 else 24) if es_precio_largo else (38 if self.modo_tv == 1 else 27)
                pad_h = "4px 12px" if self.modo_tv == 1 else "3px 10px"
                lbl_p.setStyleSheet(f"QLabel {{ font-family: 'Arial Black', 'Segoe UI Black', sans-serif; font-size: {fs_p}px; font-weight: 900; color: #FFFF00; background-color: #DC2626; padding: {pad_h}; border-radius: 10px; }}")
            else:
                fs_p = (32 if self.modo_tv == 1 else 23) if es_precio_largo else (36 if self.modo_tv == 1 else 26)
                pad_h = "4px 12px" if self.modo_tv == 1 else "3px 10px"
                lbl_p.setStyleSheet(f"QLabel {{ font-family: -apple-system, 'Segoe UI', sans-serif; font-size: {fs_p}px; font-weight: 900; color: #FFFFFF; background-color: {C_THEME['accent']}; padding: {pad_h}; border-radius: 10px; }}")
            lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.precios_lay.addWidget(lbl_p, 0, Qt.AlignmentFlag.AlignRight)
        else:
            lbl_p = QLabel(f"${self.precio:,.0f}")
            lbl_p.setMinimumWidth(0)
            if self.is_temu:
                fs_p = (36 if self.modo_tv == 1 else 26) if es_precio_largo else (42 if self.modo_tv == 1 else 30)
                lbl_p.setStyleSheet(f"QLabel {{ font-family: 'Arial Black', 'Segoe UI Black', sans-serif; font-size: {fs_p}px; font-weight: 900; color: #DC2626; }}")
            else:
                fs_p = (34 if self.modo_tv == 1 else 24) if es_precio_largo else (40 if self.modo_tv == 1 else 28)
                lbl_p.setStyleSheet(f"QLabel {{ font-family: -apple-system, 'Segoe UI', sans-serif; font-size: {fs_p}px; font-weight: 800; color: {C_THEME['accent']}; }}")
            lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.precios_lay.addWidget(lbl_p, 0, Qt.AlignmentFlag.AlignRight)

    def _build_contenedor_cinta(self):
        from src.carteleria.utils_condiciones import formatear_condicion_oferta
        regla_txt = formatear_condicion_oferta(self.regla)
        
        if not regla_txt:
            return # Omitir cinta si no hay regla o es absurda
            
        fs_r = 22 if self.modo_tv == 1 else 17
        lbl_r = QLabel(f"🔥 {regla_txt.strip()} 🔥")
        lbl_r.setMinimumWidth(0)
        lbl_r.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lbl_r.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Borde SÓLIDO premium, nunca punteado ni rayas
        if self.is_temu:
            lbl_r.setStyleSheet(f"QLabel {{ font-family: 'Segoe UI Black', 'Arial Black', sans-serif; font-size: {fs_r}px; font-weight: 900; color: #15803D; background: #DCFCE7; border-radius: 8px; padding: 5px 10px; border: 1px solid #22C55E; }}")
        else:
            lbl_r.setStyleSheet(f"QLabel {{ font-family: -apple-system, 'Segoe UI', sans-serif; font-size: {fs_r}px; font-weight: 800; color: #008C4A; background: #F1F8F5; border-radius: 8px; padding: 5px 10px; border: 1px solid #86EFAC; }}")
            
        lbl_r.setWordWrap(True)
        self.main_lay.addWidget(lbl_r)
