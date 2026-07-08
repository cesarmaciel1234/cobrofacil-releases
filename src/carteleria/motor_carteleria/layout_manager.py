class LayoutManager:
    def __init__(self, main_window):
        self.main = main_window

    def ciclar_layout(self):
        self.main.layout_mode += 1
        if self.main.layout_mode > 4:
            self.main.layout_mode = 1
        self.aplicar_layout()

    def aplicar_layout(self):
        for i in reversed(range(self.main.grid.count())): 
            w = self.main.grid.itemAt(i).widget()
            if w:
                self.main.grid.removeWidget(w)
            
        for i in range(4): self.main.grid.setColumnStretch(i, 0)
        self.main.grid.setRowStretch(0, 0)
        self.main.grid.setRowStretch(1, 0)
            
        if self.main.layout_mode == 1:
            self.main.grid.addWidget(self.main.zona2_precios, 0, 0)
            self.main.grid.setColumnStretch(0, 1)
        elif self.main.layout_mode == 2:
            self.main.grid.addWidget(self.main.zona1_carrusel, 0, 0)
            self.main.grid.addWidget(self.main.zona2_precios, 0, 1)
            self.main.grid.setColumnStretch(0, 1)
            self.main.grid.setColumnStretch(1, 1)
        elif self.main.layout_mode == 3:
            self.main.grid.addWidget(self.main.zona1_carrusel, 0, 0)
            self.main.grid.addWidget(self.main.zona2_precios, 0, 1)
            self.main.grid.addWidget(self.main.zona3_extra1, 0, 2)
            self.main.grid.setColumnStretch(0, 1)
            self.main.grid.setColumnStretch(1, 1)
            self.main.grid.setColumnStretch(2, 1)
        elif self.main.layout_mode == 4:
            self.main.grid.addWidget(self.main.zona1_carrusel, 0, 0)
            self.main.grid.addWidget(self.main.zona2_precios, 0, 1) 
            self.main.grid.addWidget(self.main.zona3_extra1, 0, 2)
            self.main.grid.addWidget(self.main.zona4_extra2, 0, 3)
            self.main.grid.setColumnStretch(0, 1)
            self.main.grid.setColumnStretch(1, 1)
            self.main.grid.setColumnStretch(2, 1)
            self.main.grid.setColumnStretch(3, 1)
            
        self.main.grid.setRowStretch(0, 1)
        if hasattr(self.main, 'promo_manager'):
            self.main.promo_manager.actualizar_pantallas_promocionales()

    def fade_to_index(self, index):
        if self.main.stack.currentIndex() == index:
            return
            
        print(f'[DEBUG] Cambiando a indice {index}')
        self.main.stack.setCurrentIndex(index)
