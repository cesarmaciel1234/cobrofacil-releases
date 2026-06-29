from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

class ProductCard(QFrame):
    """ Tarjeta individual para la lista 'Carlis' """
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setObjectName("CarlisItem")
        self.data = data # {id, nombre, precio, cant, subtotal}
        self.selected = False
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(80)
        self.update_style()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        
        # Info Izquierda (Nombre y Cantidad)
        info_v = QVBoxLayout()
        self.lbl_nombre = QLabel(self.data['nombre'].upper())
        self.lbl_nombre.setObjectName("CarlisName")
        
        self.lbl_detalles = QLabel(f"Código: {self.data['id']} | Cantidad: {self.data['cant']:.3f}")
        self.lbl_detalles.setObjectName("CarlisDetails")
        
        info_v.addWidget(self.lbl_nombre)
        info_v.addWidget(self.lbl_detalles)
        layout.addLayout(info_v)
        
        layout.addStretch()
        
        # Info Derecha (Precio y Subtotal)
        precio_v = QVBoxLayout()
        self.lbl_precio = QLabel(f"${self.data['precio']:.2f}")
        self.lbl_precio.setObjectName("CarlisPrice")
        
        self.lbl_subtotal = QLabel(f"${self.data['subtotal']:.2f}")
        self.lbl_subtotal.setObjectName("CarlisSubtotal")
        
        precio_v.addWidget(self.lbl_precio)
        precio_v.addWidget(self.lbl_subtotal)
        layout.addLayout(precio_v)

    def update_data(self, cant):
        self.data['cant'] = cant
        self.data['subtotal'] = self.data['precio'] * cant
        self.lbl_detalles.setText(f"Código: {self.data['id']} | Cantidad: {self.data['cant']:.3f}")
        self.lbl_subtotal.setText(f"${self.data['subtotal']:.2f}")

    def set_selected(self, state):
        self.selected = state
        self.update_style()

    def update_style(self):
        bg = "#222" if self.selected else "#111"
        border = "2px solid #3B82F6" if self.selected else "1px solid #333"

class CarlisList(QScrollArea):
    """ Contenedor tipo lista para las tarjetas de productos """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CarlisItem")
        self.cards = []
        self.current_index = -1
        self.setup_ui()

    def setup_ui(self):
        self.setWidgetResizable(True)
        self.setObjectName("CarlisScroll")
        
        self.container = QWidget()
        self.container.setObjectName("CarlisContainer")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.addStretch()
        
        self.setWidget(self.container)

    def add_product(self, product_data):
        # Si ya existe el producto, podriamos aumentar cantidad, pero el prompt sugiere tarjetas individuales
        # Para carniceria (pesables), a veces se prefiere items separados.
        card = ProductCard(product_data)
        self.layout.insertWidget(self.layout.count() - 1, card)
        self.cards.append(card)
        return card

    def clear(self):
        for card in self.cards:
            self.layout.removeWidget(card)
            card.deleteLater()
        self.cards = []
        self.current_index = -1

    def move_selection(self, delta):
        if not self.cards: return
        
        # Desmarcar anterior
        if 0 <= self.current_index < len(self.cards):
            self.cards[self.current_index].set_selected(False)
            
        self.current_index += delta
        if self.current_index < 0: self.current_index = 0
        if self.current_index >= len(self.cards): self.current_index = len(self.cards) - 1
        
        # Marcar nuevo
        self.cards[self.current_index].set_selected(True)
        self.ensureWidgetVisible(self.cards[self.current_index])

    def get_selected_card(self):
        if 0 <= self.current_index < len(self.cards):
            return self.cards[self.current_index]
        return None

    def remove_selected(self):
        if 0 <= self.current_index < len(self.cards):
            card = self.cards.pop(self.current_index)
            self.layout.removeWidget(card)
            card.deleteLater()
            
            # Ajustar indice
            if not self.cards: self.current_index = -1
            elif self.current_index >= len(self.cards): self.current_index = len(self.cards) - 1
            
            if self.current_index != -1:
                self.cards[self.current_index].set_selected(True)
