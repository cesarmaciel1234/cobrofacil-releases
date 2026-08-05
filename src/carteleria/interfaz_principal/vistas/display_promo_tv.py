from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt
from src.carteleria.theme import C_THEME

class DisplayPromoTV(QFrame):
    """
    Componente modular nativo para reemplazar el rendering HTML en paneles grandes 
    (Carrusel Destacados, Combos, Recomendaciones IA).
    Protege márgenes, alinea textos sin cortes ni saltos erráticos y muestra condiciones obligatorias.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(10, 10, 10, 10)
        self.main_lay.setSpacing(15)
        self.main_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._init_subcontenedores()
        
    def _init_subcontenedores(self):
        # 1. Badge Título Superior
        self.lbl_titulo = QLabel("")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setWordWrap(True)
        self.lbl_titulo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # 2. Nombre del Producto (Escala y wrap automático)
        self.lbl_producto = QLabel("")
        self.lbl_producto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_producto.setWordWrap(True)
        self.lbl_producto.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        
        # 3. Rating y Marketing (Sub-contenedor vertical para que el texto no se corte)
        self.marketing_container = QFrame()
        self.marketing_container.setObjectName("marketing_container")
        self.marketing_lay = QVBoxLayout(self.marketing_container)
        self.marketing_lay.setContentsMargins(10, 5, 10, 5)
        self.marketing_lay.setSpacing(5)
        self.marketing_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estrellas = QLabel("⭐⭐⭐⭐⭐")
        self.lbl_estrellas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_marketing = QLabel("")
        self.lbl_marketing.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_marketing.setWordWrap(True)
        self.lbl_marketing.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.marketing_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.marketing_lay.addWidget(self.lbl_estrellas)
        self.marketing_lay.addWidget(self.lbl_marketing)
        
        # 4. Contenedor de Precios
        self.lbl_precio_old = QLabel("")
        self.lbl_precio_old.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_precio_new = QLabel("")
        self.lbl_precio_new.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 5. Contenedor Cinta Condiciones (Ribbon inferio)
        self.lbl_cinta = QLabel("")
        self.lbl_cinta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cinta.setWordWrap(True)
        self.lbl_cinta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        
        # Agregar al Layout Principal con resortes para mantener todo centrado como bloque
        self.main_lay.addStretch(1)
        self.main_lay.addWidget(self.lbl_titulo)
        self.main_lay.addSpacing(20)
        self.main_lay.addWidget(self.lbl_producto)
        self.main_lay.addSpacing(15)
        self.main_lay.addWidget(self.marketing_container)
        self.main_lay.addSpacing(15)
        self.main_lay.addWidget(self.lbl_precio_old)
        self.main_lay.addSpacing(5)
        self.main_lay.addWidget(self.lbl_precio_new)
        self.main_lay.addSpacing(20)
        self.main_lay.addWidget(self.lbl_cinta)
        self.main_lay.addStretch(1)

    def actualizar(self, titulo, nombre, marketing_str, precio, precio_oferta=0, regla="", is_temu=True, bg_color_badge="#DC2626", use_ribbon=True):
        # Limpieza de regla/condiciones
        from src.carteleria.utils_condiciones import formatear_condicion_oferta
        regla_txt = formatear_condicion_oferta(regla)
        
        if use_ribbon and regla_txt:
            self.lbl_cinta.setText(f"🔥 {regla_txt.strip()} 🔥")
            self.lbl_cinta.show()
        else:
            self.lbl_cinta.hide()

        # 1. Título
        self.lbl_titulo.setText(titulo.upper())
        len_t = len(titulo.strip())
        fs_t = 38 if len_t < 17 else 28
        
        if is_temu:
            self.lbl_titulo.setStyleSheet(f"QLabel {{ font-family: Impact, 'Arial Black', sans-serif; font-size: {fs_t}px; color: #FFFFFF; background-color: {bg_color_badge}; padding: 12px 20px; border-radius: 12px; }}")
        else:
            self.lbl_titulo.setStyleSheet(f"QLabel {{ font-family: -apple-system, sans-serif; font-size: {fs_t-4}px; font-weight: bold; color: #FFFFFF; background-color: {bg_color_badge}; padding: 10px 20px; border-radius: 12px; }}")

        # 2. Producto
        len_n = len(nombre.strip())
        max_word = max([len(w) for w in nombre.split()]) if nombre else 0
        fs_n = 65 if (len_n < 16 and max_word < 9) else 45
        self.lbl_producto.setText(nombre.upper())
        if is_temu:
            self.lbl_producto.setStyleSheet(f"QLabel {{ font-family: Impact, 'Arial Black', sans-serif; font-size: {fs_n}px; color: #000000; line-height: 1.1; }}")
        else:
            self.lbl_producto.setStyleSheet(
                f"QLabel {{ font-family: -apple-system, sans-serif; font-size: {fs_n-10}px; font-weight: 900; "
                f"color: {C_THEME.get('text', '#1D1D1F')}; }}"
            )

        # 3. Rating y Marketing
        self.lbl_marketing.setText(f"({marketing_str})")
        if is_temu:
            self.marketing_container.setStyleSheet("#marketing_container { background-color: #F0FFF4; border: 2px solid #86EFAC; border-radius: 12px; padding: 8px; }")
            self.lbl_estrellas.setStyleSheet("QLabel { font-size: 34px; color: #FF9900; background: transparent; border: none; }")
            self.lbl_marketing.setStyleSheet("QLabel { font-family: Arial, sans-serif; font-size: 22px; font-weight: bold; color: #00A859; background: transparent; border: none; }")
        else:
            bg_card = C_THEME.get("bg_card") or C_THEME.get("surface") or "#FFFFFF"
            border = C_THEME.get("border") or "#E2E8F0"
            self.marketing_container.setStyleSheet(
                f"#marketing_container {{ background-color: {bg_card}; border: 1px solid {border}; "
                f"border-radius: 12px; padding: 8px; }}"
            )
            self.lbl_estrellas.setStyleSheet("QLabel { font-size: 30px; color: #F59E0B; background: transparent; border: none; }")
            self.lbl_marketing.setStyleSheet(
                f"QLabel {{ font-family: -apple-system, sans-serif; font-size: 20px; font-weight: 700; "
                f"color: {C_THEME.get('accent', '#FF3B30')}; background: transparent; border: none; }}"
            )


        # 4. Precios
        p_val = precio_oferta if precio_oferta > 0 else precio
        p_str = f"${p_val:,.0f}"
        es_precio_largo = len(p_str) >= 7
        
        if precio_oferta > 0:
            self.lbl_precio_old.setText(f"<s>${precio:,.0f}</s>")
            self.lbl_precio_old.show()
            self.lbl_precio_new.setText(f"${precio_oferta:,.0f}")
        else:
            self.lbl_precio_old.hide()
            self.lbl_precio_new.setText(f"${precio:,.0f}")

        if is_temu:
            self.lbl_precio_old.setStyleSheet("QLabel { font-family: Arial, sans-serif; font-size: 40px; color: #DC2626; text-decoration: line-through; }")
            fs_p = 85 if es_precio_largo else 110
            self.lbl_precio_new.setStyleSheet(f"QLabel {{ font-family: Impact, 'Arial Black', sans-serif; font-size: {fs_p}px; color: #DC2626; background-color: #FFFF00; padding: 10px 25px; border-radius: 12px; margin-bottom: 10px; }}")
        else:
            self.lbl_precio_old.setStyleSheet("QLabel { font-family: -apple-system, sans-serif; font-size: 38px; color: #94A3B8; text-decoration: line-through; }")
            fs_p = 90 if es_precio_largo else 115
            self.lbl_precio_new.setStyleSheet(
                f"QLabel {{ font-family: -apple-system, sans-serif; font-size: {fs_p}px; font-weight: 900; "
                f"color: #FFFFFF; background-color: {C_THEME.get('accent', '#FF3B30')}; "
                f"padding: 10px 25px; border-radius: 12px; }}"
            )

        # 5. Cinta Condiciones
        if regla_txt:
            if use_ribbon:
                self.lbl_cinta.setText(f"🔥 {regla_txt.strip()} 🔥")
                self.lbl_cinta.show()
                if is_temu:
                    self.lbl_cinta.setStyleSheet("QLabel { font-family: 'Segoe UI Black', 'Arial Black', sans-serif; font-size: 26px; font-weight: 900; color: #15803D; background: #DCFCE7; border-radius: 8px; padding: 8px 15px; border: 2px solid #22C55E; margin-top: 10px; }")
                else:
                    self.lbl_cinta.setStyleSheet("QLabel { font-family: -apple-system, sans-serif; font-size: 24px; font-weight: 800; color: #008C4A; background: #F1F8F5; border-radius: 8px; padding: 8px 15px; border: 2px solid #86EFAC; margin-top: 10px; }")
            else:
                self.lbl_cinta.setText(f"*{regla_txt.strip()}*")
                self.lbl_cinta.show()
                if is_temu:
                    self.lbl_cinta.setStyleSheet("QLabel { font-family: Arial, sans-serif; font-size: 20px; color: #666666; font-weight: normal; font-style: italic; margin-top: 15px; }")
                else:
                    self.lbl_cinta.setStyleSheet(
                        f"QLabel {{ font-family: -apple-system, sans-serif; font-size: 18px; "
                        f"color: {C_THEME.get('text_muted', '#86868B')}; font-style: italic; margin-top: 15px; }}"
                    )
        else:
            self.lbl_cinta.hide()
