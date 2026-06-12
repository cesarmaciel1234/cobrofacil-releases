from PyQt5.QtWidgets import QScrollArea, QFrame, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from src.vistas.carteleria_app.theme import C_THEME, apply_apple_shadow

class Pantalla2(QFrame):
    """
    Zona 2: Lista AutoScroll (Envuelto en un Frame estilo Apple)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
        apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area = _AutoScrollList()
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
                lbl_cat.setStyleSheet(f"font-family: -apple-system, 'Segoe UI'; font-size: 24px; font-weight: 800; color: {C_THEME['blue']}; background: transparent; padding-top: 25px; padding-bottom: 5px; border-bottom: 2px solid rgba(0, 122, 255, 0.2);")
                lbl_cat.setAlignment(Qt.AlignLeft)
                self.inner_layout.addWidget(lbl_cat)
                
                for nombre, precio in productos:
                    row = QFrame()
                    row.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 16px;")
                    apply_apple_shadow(row, blur=15, alpha=15, y_offset=4)
                    
                    row_lay = QHBoxLayout(row) 
                    row_lay.setContentsMargins(20, 15, 20, 15)
                    
                    lbl_n = QLabel(nombre)
                    lbl_n.setStyleSheet(f"font-family: -apple-system, 'Segoe UI'; font-size: 20px; font-weight: 600; color: {C_THEME['text']}; background: transparent;")
                    lbl_n.setWordWrap(True)
                    
                    lbl_p = QLabel(f"${precio:,.2f}")
                    lbl_p.setStyleSheet(f"font-family: -apple-system, 'Segoe UI'; font-size: 22px; font-weight: 800; color: {C_THEME['accent']}; background: transparent;")
                    lbl_p.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    row_lay.addWidget(lbl_n, stretch=1)
                    row_lay.addWidget(lbl_p)
                    self.inner_layout.addWidget(row)
                
        self.timer.start(25) 

    def _do_scroll(self):
        bar = self.verticalScrollBar()
        max_val = bar.maximum()
        if max_val == 0: return
        self._scroll_pos += 1
        if self._scroll_pos > (max_val * 0.6):
            self._scroll_pos = 0
        bar.setValue(self._scroll_pos)
