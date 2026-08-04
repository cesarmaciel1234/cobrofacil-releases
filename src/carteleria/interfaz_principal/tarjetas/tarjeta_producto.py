from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainterPath, QRegion
from src.carteleria.theme import C_THEME

class TarjetaProducto(QFrame):
    """
    Contenedor modular independiente para cada producto en la grilla de precios.
    Fuentes en `px` (no `pt`): en ejecutables Windows el DPI infla los pt y
    el precio/badge se sale del borde redondeado.
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
        # Preferred (no Ignored): evita que la fila se aplaste y se pinte encima de la siguiente
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        
        # Calcular alturas mínimas equilibradas para asegurar visibilidad en TV
        len_n = len(self.nombre)
        es_nombre_largo = (len_n > 14)
        tiene_oferta = self.precio_oferta and float(self.precio_oferta) > 0
        
        if self.modo_tv == 1:
            base_h = 118
            extra_h_largo = 28 if es_nombre_largo else 0
            extra_h_regla = 34 if self.regla else 0
            extra_h_oferta = 22 if tiene_oferta else 0
        else:
            base_h = 98
            extra_h_largo = 22 if es_nombre_largo else 0
            extra_h_regla = 28 if self.regla else 0
            extra_h_oferta = 16 if tiene_oferta else 0
            
        self.setMinimumHeight(base_h + extra_h_largo + extra_h_regla + extra_h_oferta)
        
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
        # Más padding inferior: el badge rojo no “rompe” el borde en .exe
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
            fs_n = 28 if self.modo_tv == 1 else 20
        elif len_n <= 14 and max_word_len <= 10:
            fs_n = 24 if self.modo_tv == 1 else 17
        elif max_word_len > 10:
            fs_n = 16 if self.modo_tv == 1 else 13
        else:
            fs_n = 19 if self.modo_tv == 1 else 14
            
        self.lbl_producto = QLabel(self.nombre)
        self.lbl_producto.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # px (no pt): evita inflación DPI en CobroFacil_POS.exe
        if self.is_temu:
            self.lbl_producto.setStyleSheet(
                f"QLabel {{ font-family: 'Segoe UI Black', 'Arial Black', sans-serif; "
                f"font-size: {fs_n}px; font-weight: 800; color: #1E293B; "
                f"letter-spacing: 0.3px; padding: 2px 0px; }}"
            )
        else:
            self.lbl_producto.setStyleSheet(
                f"QLabel {{ font-family: 'Segoe UI', sans-serif; font-size: {fs_n}px; "
                f"font-weight: 800; color: {C_THEME['text']}; padding: 2px 0px; }}"
            )

        self.lbl_producto.setWordWrap(True)
        self.lbl_producto.setMinimumWidth(0)
        self.lbl_producto.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def _build_contenedor_precios(self):
        p_val = self.precio_oferta if self.precio_oferta > 0 else self.precio
        p_str = f"${p_val:,.0f}"
        es_precio_largo = len(p_str) >= 7

        if self.precio_oferta > 0:
            fs_old = 16 if self.modo_tv == 1 else 12
            lbl_old = QLabel(f"<s>${self.precio:,.0f}</s>")
            lbl_old.setMinimumWidth(0)
            lbl_old.setStyleSheet(
                f"QLabel {{ font-family: 'Segoe UI', sans-serif; font-size: {fs_old}px; "
                f"font-weight: 700; color: #94A3B8; }}"
            )
            lbl_old.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.precios_lay.addWidget(lbl_old, 0, Qt.AlignmentFlag.AlignRight)

            lbl_p = QLabel(f"${self.precio_oferta:,.0f}")
            lbl_p.setMinimumWidth(0)
            lbl_p.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            if self.is_temu:
                fs_p = (22 if self.modo_tv == 1 else 16) if es_precio_largo else (24 if self.modo_tv == 1 else 18)
                pad_h = "3px 10px" if self.modo_tv == 1 else "2px 8px"
                lbl_p.setStyleSheet(
                    f"QLabel {{ font-family: 'Arial Black', 'Segoe UI Black', sans-serif; "
                    f"font-size: {fs_p}px; font-weight: 900; color: #FFFF00; "
                    f"background-color: #DC2626; padding: {pad_h}; border-radius: 10px; }}"
                )
            else:
                fs_p = (20 if self.modo_tv == 1 else 15) if es_precio_largo else (23 if self.modo_tv == 1 else 17)
                pad_h = "3px 10px" if self.modo_tv == 1 else "2px 8px"
                lbl_p.setStyleSheet(
                    f"QLabel {{ font-family: 'Segoe UI', sans-serif; font-size: {fs_p}px; "
                    f"font-weight: 900; color: #FFFFFF; background-color: {C_THEME['accent']}; "
                    f"padding: {pad_h}; border-radius: 10px; }}"
                )
            lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.precios_lay.addWidget(lbl_p, 0, Qt.AlignmentFlag.AlignRight)
        else:
            lbl_p = QLabel(f"${self.precio:,.0f}")
            lbl_p.setMinimumWidth(0)
            lbl_p.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            if self.is_temu:
                fs_p = (24 if self.modo_tv == 1 else 17) if es_precio_largo else (28 if self.modo_tv == 1 else 20)
                lbl_p.setStyleSheet(
                    f"QLabel {{ font-family: 'Arial Black', 'Segoe UI Black', sans-serif; "
                    f"font-size: {fs_p}px; font-weight: 900; color: #DC2626; }}"
                )
            else:
                fs_p = (22 if self.modo_tv == 1 else 16) if es_precio_largo else (26 if self.modo_tv == 1 else 19)
                lbl_p.setStyleSheet(
                    f"QLabel {{ font-family: 'Segoe UI', sans-serif; font-size: {fs_p}px; "
                    f"font-weight: 800; color: {C_THEME['accent']}; }}"
                )
            lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.precios_lay.addWidget(lbl_p, 0, Qt.AlignmentFlag.AlignRight)

    def _build_contenedor_cinta(self):
        from src.carteleria.utils_condiciones import formatear_condicion_oferta
        regla_txt = formatear_condicion_oferta(self.regla)

        if not regla_txt:
            return

        fs_r = 14 if self.modo_tv == 1 else 12
        lbl_r = QLabel(f"🔥 {regla_txt.strip()} 🔥")
        lbl_r.setMinimumWidth(0)
        lbl_r.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lbl_r.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.is_temu:
            lbl_r.setStyleSheet(
                f"QLabel {{ font-family: 'Segoe UI Black', 'Arial Black', sans-serif; "
                f"font-size: {fs_r}px; font-weight: 800; color: #FFFFFF; "
                f"background-color: #E1251B; padding: 2px 4px; border-radius: 6px; }}"
            )
        else:
            lbl_r.setStyleSheet(
                f"QLabel {{ font-family: 'Segoe UI', sans-serif; font-size: {fs_r}px; "
                f"font-weight: 800; color: #FFFFFF; background-color: #E11D48; "
                f"padding: 2px 4px; border-radius: 6px; }}"
            )

        lbl_r.setWordWrap(True)
        self.main_lay.addWidget(lbl_r)
