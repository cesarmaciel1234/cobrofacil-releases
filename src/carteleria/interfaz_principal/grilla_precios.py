from PyQt6.QtWidgets import QScrollArea, QFrame, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from src.carteleria.theme import C_THEME, apply_apple_shadow

class GrillaPrecios(QFrame):
    """
    Zona 2: Lista AutoScroll (Envuelto en un Frame estilo Apple)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        from src.carteleria.theme import get_active_theme_name
        if get_active_theme_name() == "temu":
            # Estilo asiático: Bordes punteados de cupón / Naranja-Rojo brillante
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; border: 6px dashed #FF5722;")
        else:
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
        apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        from PyQt6.QtWidgets import QSizePolicy
        self.scroll_area = _AutoScrollList()
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.scroll_area)
        
    def set_items(self, items_by_category):
        self.scroll_area.set_items(items_by_category)


class _AutoScrollList(QScrollArea):
    """Componente interno que maneja el scroll y renderizado de ítems"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background: transparent; border: none;")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(10, 10, 10, 10) 
        self.inner_layout.setSpacing(12)
        self.setWidget(self.container)
        
        self._scroll_pos = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._do_scroll)

    def set_items(self, items_by_category):
        for i in reversed(range(self.inner_layout.count())):
            w = self.inner_layout.itemAt(i).widget()
            if w: w.deleteLater()
                
        for _ in range(3): 
            for categoria, productos in items_by_category.items():
                lbl_cat = QLabel(categoria.upper())
                from src.carteleria.theme import get_active_theme_name
                if get_active_theme_name() == "temu":
                    lbl_cat.setStyleSheet(f"font-family: Impact; font-size: 42px; color: #DC2626; background: transparent; padding-top: 25px; padding-bottom: 5px; border-bottom: 4px solid #DC2626;")
                else:
                    lbl_cat.setStyleSheet(f"font-family: -apple-system, 'Segoe UI'; font-size: 36px; font-weight: 800; color: {C_THEME['blue']}; background: transparent; padding-top: 25px; padding-bottom: 5px; border-bottom: 2px solid rgba(0, 122, 255, 0.2);")
                lbl_cat.setAlignment(Qt.AlignLeft)
                self.inner_layout.addWidget(lbl_cat)
                
                for nombre, precio, precio_oferta, regla in productos:
                    row = QFrame()
                    from src.carteleria.theme import get_active_theme_name
                    if get_active_theme_name() == "temu":
                        row.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 8px; border: 2px solid #F87171;")
                    else:
                        row.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 16px; border: 1px solid rgba(0,0,0,0.1);")
                    
                    row_lay = QHBoxLayout(row) 
                    row_lay.setContentsMargins(20, 15, 20, 15)
                    
                    # Layout vertical para Nombre y Regla
                    name_lay = QVBoxLayout()
                    name_lay.setSpacing(2)
                    
                    lbl_n = QLabel(nombre)
                    lbl_n.setStyleSheet(f"font-family: -apple-system, 'Segoe UI'; font-size: 28px; font-weight: 600; color: {C_THEME['text']}; background: transparent;")
                    lbl_n.setWordWrap(True)
                    name_lay.addWidget(lbl_n)
                    
                    if regla:
                        lbl_r = QLabel(regla)
                        lbl_r.setStyleSheet(f"font-family: -apple-system, 'Segoe UI'; font-size: 20px; font-weight: 600; color: {C_THEME['accent']}; background: transparent;")
                        lbl_r.setWordWrap(True)
                        name_lay.addWidget(lbl_r)
                        
                    name_lay.addStretch()
                    row_lay.addLayout(name_lay, stretch=1)
                    
                    if precio_oferta > 0:
                        lbl_old = QLabel(f"<s>${precio:,.2f}</s>")
                        lbl_old.setStyleSheet(f"font-family: -apple-system, 'Segoe UI'; font-size: 22px; font-weight: 600; color: rgba(0,0,0,0.4); background: transparent;")
                        lbl_old.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        
                        lbl_p = QLabel(f"${precio_oferta:,.2f}")
                        if get_active_theme_name() == "temu":
                            lbl_p.setStyleSheet(f"font-family: 'Impact', 'Segoe UI Black', sans-serif; font-size: 36px; font-weight: 900; color: #FFFF00; background: #DC2626; padding: 2px 8px; border-radius: 6px;")
                        else:
                            lbl_p.setStyleSheet(f"font-family: -apple-system, 'Segoe UI'; font-size: 32px; font-weight: 800; color: {C_THEME['accent']}; background: transparent;")
                        lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        
                        precios_lay = QVBoxLayout()
                        precios_lay.setContentsMargins(0,0,0,0)
                        precios_lay.setSpacing(2)
                        precios_lay.addWidget(lbl_old)
                        precios_lay.addWidget(lbl_p)
                        row_lay.addLayout(precios_lay)
                    else:
                        lbl_p = QLabel(f"${precio:,.2f}")
                        lbl_p.setStyleSheet(f"font-family: -apple-system, 'Segoe UI'; font-size: 32px; font-weight: 800; color: {C_THEME['accent']}; background: transparent;")
                        lbl_p.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        row_lay.addWidget(lbl_p)
                    self.inner_layout.addWidget(row)
                
        self.timer.start(40) 

    def _do_scroll(self):
        bar = self.verticalScrollBar()
        max_val = bar.maximum()
        if max_val == 0: return
        self._scroll_pos += 1
        if self._scroll_pos > (max_val * 0.6):
            self._scroll_pos = 0
        bar.setValue(self._scroll_pos)
