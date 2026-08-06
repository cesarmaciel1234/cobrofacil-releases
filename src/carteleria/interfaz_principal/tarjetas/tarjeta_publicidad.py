from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainterPath, QRegion
from src.carteleria.theme import C_THEME

class TarjetaPublicidad(QFrame):
    """
    Contenedor exclusivo para Productos Promocionados.
    Tiene un diseño 'tipo Google Ads' para resaltar sobre el resto.
    Preparado para alojar una imagen del producto en el futuro.
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
        self.setObjectName("PromoRow")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        
        len_n = len(self.nombre)
        tiene_oferta = self.precio_oferta and float(self.precio_oferta) > 0
        es_2_lineas = (len_n > 14 and len_n <= 28)
        es_3_lineas = (len_n > 28)
        
        # Le damos un poco más de altura base (ej +30) para que entre el cartel "PRODUCTO PROMOCIONADO"
        if self.modo_tv == 1:
            base_h = 130
            extra_h_largo = 32 if es_2_lineas else (64 if es_3_lineas else 0)
            extra_h_regla = 34 if self.regla else 0
            extra_h_oferta = 22 if tiene_oferta else 0
        else:
            base_h = 110
            extra_h_largo = 24 if es_2_lineas else (48 if es_3_lineas else 0)
            extra_h_regla = 28 if self.regla else 0
            extra_h_oferta = 16 if tiene_oferta else 0
            
        self.setMinimumHeight(base_h + extra_h_largo + extra_h_regla + extra_h_oferta)
        
        self.setStyleSheet("""
            #PromoRow { 
                background: #FFFF00; /* Amarillo Google Ads */
                border-radius: 16px; 
                border: 3px solid #E1251B; 
            }
        """)
            
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(14, 10, 14, 14)
        self.main_lay.setSpacing(6)
        self.main_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._clip_card()

    def showEvent(self, event):
        super().showEvent(event)
        self._clip_card()

    def _clip_card(self):
        if self.width() <= 0 or self.height() <= 0:
            return
        path = QPainterPath()
        path.addRoundedRect(QRectF(1.0, 1.0, self.width() - 2.0, self.height() - 2.0), 15.0, 15.0)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
        
    def _construir_subcontenedores(self):
        # Contenedor Superior (Producto + Precios)
        self.top_container = QWidget()
        self.top_container.setStyleSheet("background: transparent; border: none;")
        self.top_lay = QHBoxLayout(self.top_container)
        self.top_lay.setContentsMargins(0, 0, 0, 0)
        self.top_lay.setSpacing(14)
        self.top_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Columna Izquierda: Imagen (Futuro) + Texto
        self._build_contenedor_producto()
        self.top_lay.addWidget(self.columna_izq_widget, stretch=6)
        
        # Columna Derecha: Precios
        self.precios_container = QWidget()
        self.precios_container.setStyleSheet("background: transparent; border: none;")
        self.precios_container.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        self.precios_lay = QVBoxLayout(self.precios_container)
        self.precios_lay.setContentsMargins(0, 0, 0, 0)
        self.precios_lay.setSpacing(2)
        self.precios_lay.addStretch(1)
        self._build_contenedor_precios()
        self.precios_lay.addStretch(1)
        
        self.top_lay.addWidget(self.precios_container, stretch=4)
        self.main_lay.addWidget(self.top_container, stretch=1)
        
        self._build_contenedor_cinta()

    def _build_contenedor_producto(self):
        self.columna_izq_widget = QWidget()
        self.col_izq_lay = QVBoxLayout(self.columna_izq_widget)
        self.col_izq_lay.setContentsMargins(0,0,0,0)
        self.col_izq_lay.setSpacing(2)
        
        fs_n = 28 if self.modo_tv == 1 else 20
        self.lbl_producto = QLabel(self.nombre)
        self.lbl_producto.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Texto rojo gigante para el nombre del producto
        self.lbl_producto.setStyleSheet(
            f"QLabel {{ font-family: 'Segoe UI Black', 'Arial Black', sans-serif; "
            f"font-size: {fs_n}px; font-weight: 900; color: #DC2626; "
            f"letter-spacing: 0.3px; padding: 2px 0px; }}"
        )
        self.lbl_producto.setWordWrap(True)
        self.lbl_producto.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        
        # Subtítulo de anuncio
        self.lbl_ad = QLabel("PRODUCTO PROMOCIONADO")
        fs_ad = 13 if self.modo_tv == 1 else 10
        self.lbl_ad.setStyleSheet(
            f"QLabel {{ font-family: 'Arial Black', sans-serif; "
            f"font-size: {fs_ad}px; font-weight: 900; color: #16A34A; }}"
        )
        self.lbl_ad.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.lbl_ad.setWordWrap(True)
        self.lbl_ad.setMinimumWidth(0)
        
        # Future image container would go here
        
        self.col_izq_lay.addWidget(self.lbl_producto)
        self.col_izq_lay.addWidget(self.lbl_ad)

    def _build_contenedor_precios(self):
        p_val = self.precio_oferta if self.precio_oferta > 0 else self.precio
        p_str = f"${p_val:,.0f}"
        es_precio_largo = len(p_str) >= 7

        if self.precio_oferta > 0:
            fs_old = 18 if self.modo_tv == 1 else 14
            lbl_old = QLabel(f"<s>${self.precio:,.0f}</s>")
            lbl_old.setMinimumWidth(0)
            lbl_old.setStyleSheet(
                f"QLabel {{ font-family: 'Segoe UI', sans-serif; font-size: {fs_old}px; "
                f"font-weight: 700; color: #DC2626; opacity: 0.5; }}"
            )
            lbl_old.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.precios_lay.addWidget(lbl_old, 0, Qt.AlignmentFlag.AlignRight)

            lbl_p = QLabel(f"${self.precio_oferta:,.0f}")
            lbl_p.setMinimumWidth(0)
            lbl_p.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            fs_p = (24 if self.modo_tv == 1 else 18) if es_precio_largo else (26 if self.modo_tv == 1 else 20)
            pad_h = "3px 10px" if self.modo_tv == 1 else "2px 8px"
            lbl_p.setStyleSheet(
                f"QLabel {{ font-family: 'Arial Black', 'Segoe UI Black', sans-serif; "
                f"font-size: {fs_p}px; font-weight: 900; color: #FFFFFF; "
                f"background-color: #DC2626; padding: {pad_h}; border-radius: 10px; }}"
            )
            lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.precios_lay.addWidget(lbl_p, 0, Qt.AlignmentFlag.AlignRight)
        else:
            lbl_p = QLabel(f"${self.precio:,.0f}")
            lbl_p.setMinimumWidth(0)
            lbl_p.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            fs_p = (26 if self.modo_tv == 1 else 19) if es_precio_largo else (30 if self.modo_tv == 1 else 22)
            lbl_p.setStyleSheet(
                f"QLabel {{ font-family: 'Arial Black', 'Segoe UI Black', sans-serif; "
                f"font-size: {fs_p}px; font-weight: 900; color: #DC2626; }}"
            )
            lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.precios_lay.addWidget(lbl_p, 0, Qt.AlignmentFlag.AlignRight)

    def _build_contenedor_cinta(self):
        from src.carteleria.utils_condiciones import formatear_condicion_oferta
        regla_txt = formatear_condicion_oferta(self.regla)
        
        if regla_txt:
            self.lbl_cinta = QLabel(f"🔥 {regla_txt.strip()} 🔥")
            self.lbl_cinta.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_cinta.setWordWrap(True)
            self.lbl_cinta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            fs_c = 18 if self.modo_tv == 1 else 13
            self.lbl_cinta.setStyleSheet(
                f"QLabel {{ font-family: 'Segoe UI Black', 'Arial Black', sans-serif; "
                f"font-size: {fs_c}px; font-weight: 900; color: #15803D; "
                f"background: #DCFCE7; border-radius: 8px; padding: 4px 8px; "
                f"border: 2px solid #22C55E; }}"
            )
            self.main_lay.addWidget(self.lbl_cinta)
