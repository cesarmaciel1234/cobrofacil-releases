import os
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor


def resolver_icono_png(categoria_nombre):
    """
    Busca la ruta del ícono PNG para un departamento/categoría.
    Primero busca asignación específica en BD, luego mapeo automático local.
    """
    cat_upper = str(categoria_nombre).upper().strip()
    from src.carteleria.assets_paths import iconos_rubros_dir
    base_dir = iconos_rubros_dir()
    
    # 1. BD departamental
    try:
        from src.motor_inventario.motor_departamentos import MotorDepartamentos
        deps = MotorDepartamentos().obtener_departamentos()
        for d in deps:
            if d.get('nombre', '').upper().strip() == cat_upper and d.get('icono'):
                fpath = os.path.join(base_dir, d['icono'])
                if os.path.exists(fpath):
                    return fpath
    except Exception:
        pass

    # 2. Mapeo por palabras clave
    kw_map = [
        (["CARNE", "VACUNO", "ASADO", "LOMO", "BIFE", "TERNERA", "ACHURA", "MONDONGO"], "carne.png"),
        (["POLLO", "AVE", "PATA", "SUPREMA", "PECHUGA", "ALITA"], "pollo.png"),
        (["CERDO", "BONDIOLA", "PECHITO", "CHUCHETO", "LECHON"], "cerdo.png"),
        (["QUESO", "FIAMBRE", "LACTEO", "JAMON", "PROVOLETA", "EMBUTIDO", "CHORIZO", "MORCILLA", "SALCHICHA"], "fiambreria.png"),
        (["PAN", "PANADERIA", "FACTURA", "BIZCOCHO", "TORTA"], "panaderia.png"),
        (["VERDURA", "VERDULERIA", "FRUTA", "FRUTAL"], "verduleria.png"),
        (["BEBIDA", "GASEOSA", "CERVEZA", "VINO", "AGUA", "JUGO"], "bebidas.png"),
        (["LIMPIEZA", "JABON", "DETERGENTE", "LAVANDINA"], "limpieza.png"),
        (["PESCADO", "MARISCO", "FILET"], "pescado.png"),
        (["OFERTA", "PROMO", "COMBO", "DESTACADO", "RELAMPAGO"], "oferta.png"),
        (["ALMACEN", "MERCADERIA", "ABARROTES"], "almacen.png")
    ]
    for kws, fname in kw_map:
        if any(w in cat_upper for w in kws):
            fpath = os.path.join(base_dir, fname)
            if os.path.exists(fpath):
                return fpath

    return None


class BannerCategoria(QFrame):
    """
    Componente Modular Independiente: Banner Encabezado de Categoria / Departamento.
    Incluye la cápula/cápsula contenedora del ícono en el lado izquierdo y
    auto-escalado de texto responsive para nombres largos.
    """
    def __init__(self, categoria_nombre, modo_tv=4, is_temu=False, parent=None):
        super().__init__(parent)
        self.categoria_nombre = categoria_nombre
        self.modo_tv = modo_tv
        self.is_temu = is_temu
        self._setup_ui()

    def _setup_ui(self):
        cat_upper = self.categoria_nombre.upper()
        ico_path = resolver_icono_png(cat_upper)

        # ── Estilo Contenedor Principal (Banner) ──
        if self.is_temu:
            bg_gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #002663, stop:0.5 #0045B5, stop:1 #002663)"
            border_color = "#3B82F6"
        else:
            bg_gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:0.5 #2563EB, stop:1 #1E3A8A)"
            border_color = "#60A5FA"

        self.setObjectName("BannerCategoria")
        self.setMinimumHeight(64)
        self.setStyleSheet(f"""
            BannerCategoria#BannerCategoria {{
                background: {bg_gradient};
                border: 2px solid {border_color};
                border-radius: 16px;
                margin-top: 10px;
                margin-bottom: 6px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 16, 4)
        layout.setSpacing(8)

        # ── Contenedor Ícono (20% Proporción de Ancho) ──
        contenedor_icono = QWidget()
        contenedor_icono.setStyleSheet("background: transparent; border: none;")
        ico_lay = QHBoxLayout(contenedor_icono)
        ico_lay.setContentsMargins(4, 2, 4, 2)
        ico_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_ico = QLabel()
        lbl_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ico.setStyleSheet("border: none; background: transparent;")

        if ico_path and os.path.exists(ico_path):
            from src.carteleria.escala_tv import load_pixmap_scaled, scaled_px
            pm = load_pixmap_scaled(ico_path, 54, 54, widget=self)
            if not pm.isNull():
                side = scaled_px(54, self)
                lbl_ico.setFixedSize(side, side)
                lbl_ico.setPixmap(pm)
            else:
                fs = max(27, int(27 * (scaled_px(54, self) / 54)))
                lbl_ico.setText(self._obtener_emoji_fallback(cat_upper))
                lbl_ico.setStyleSheet(f"border: none; background: transparent; font-size: {fs}pt;")
        else:
            from src.carteleria.escala_tv import scaled_px
            fs = max(27, int(27 * (scaled_px(54, self) / 54)))
            lbl_ico.setText(self._obtener_emoji_fallback(cat_upper))
            lbl_ico.setStyleSheet(f"border: none; background: transparent; font-size: {fs}pt;")

        ico_lay.addWidget(lbl_ico)
        layout.addWidget(contenedor_icono, 2) # 20% del ancho

        # ── Texto del Título con Auto-Escalado Responsive (80% Proporción de Ancho) ──
        fs_cat = 34 if (self.is_temu and self.modo_tv == 1) else (27 if self.is_temu else (31 if self.modo_tv == 1 else 24))
        
        # Ajuste dinámico de fuente para nombres muy largos
        if len(cat_upper) > 28:
            fs_cat = int(fs_cat * 0.58)
        elif len(cat_upper) > 20:
            fs_cat = int(fs_cat * 0.72)
        elif len(cat_upper) > 14:
            fs_cat = int(fs_cat * 0.85)

        lbl_txt = QLabel(cat_upper)
        lbl_txt.setWordWrap(True)
        lbl_txt.setStyleSheet(f"""
            QLabel {{
                font-family: 'Arial Black', 'Segoe UI Black', sans-serif;
                font-size: {fs_cat}pt;
                font-weight: 900;
                color: #FFFFFF;
                border: none;
                background: transparent;
                letter-spacing: 1px;
            }}
        """)
        layout.addWidget(lbl_txt, 8) # 80% del ancho

    def _obtener_emoji_fallback(self, cat_upper):
        if any(w in cat_upper for w in ["CARNE", "VACUNO", "ASADO", "LOMO", "BIFE", "NOVILLO", "TERNERA", "ACHURAS", "ACHURA", "MENUDENCIAS", "MONDONGO"]):
            return "🥩"
        elif any(w in cat_upper for w in ["POLLO", "AVE", "PATA", "SUPREMA", "PECHUGA", "ALITA"]):
            return "🍗"
        elif any(w in cat_upper for w in ["CERDO", "BONDIOLA", "PECHITO", "CHUCHETO", "LECHON"]):
            return "🥓"
        elif any(w in cat_upper for w in ["CHORIZO", "MORCILLA", "EMBUTIDO", "SALCHICHA", "SALAME"]):
            return "🌭"
        elif any(w in cat_upper for w in ["OFERTA", "PROMO", "COMBO", "DESTACADO", "RELAMPAGO"]):
            return "🔥"
        elif any(w in cat_upper for w in ["QUESO", "FIAMBRE", "LACTEO", "JAMON", "PROVOLETA"]):
            return "🧀"
        return "⭐"
