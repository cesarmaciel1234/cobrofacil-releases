from PyQt6.QtWidgets import QSizePolicy

class LayoutManager:
    def __init__(self, main_window):
        self.main = main_window

    def ciclar_layout(self):
        if hasattr(self.main, 'estado_sos_activo') and self.main.estado_sos_activo:
            return
            
        self.main.layout_mode += 1
        if self.main.layout_mode > 4:
            self.main.layout_mode = 1
        self.aplicar_layout()

    def aplicar_layout(self):
        self.main.zona1_carrusel.hide()
        self.main.zona2_precios.hide()
        self.main.zona3_extra1.hide()
        self.main.zona4_extra2.hide()
        
        # Forzar políticas de tamaño para que siempre se dividan el ancho exactamente igual
        policy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.main.zona1_carrusel.setSizePolicy(policy)
        self.main.zona2_precios.setSizePolicy(policy)
        self.main.zona3_extra1.setSizePolicy(policy)
        self.main.zona4_extra2.setSizePolicy(policy)
        
        for i in reversed(range(self.main.grid.count())): 
            w = self.main.grid.itemAt(i).widget()
            if w:
                self.main.grid.removeWidget(w)
            
        for i in range(4): self.main.grid.setColumnStretch(i, 0)
        self.main.grid.setRowStretch(0, 0)
        self.main.grid.setRowStretch(1, 0)
            
        total_width = self.main.width()
        is_multimonitor = total_width > 2500
        
        if hasattr(self.main.zona2_precios, 'set_layout_mode'):
            self.main.zona2_precios.set_layout_mode(self.main.layout_mode)
            
        if self.main.layout_mode == 1:
            self.main.grid.addWidget(self.main.zona2_precios, 0, 0)
            self.main.zona2_precios.show()
            self.main.grid.setColumnStretch(0, 1)
        elif self.main.layout_mode == 2:
            self.main.grid.addWidget(self.main.zona1_carrusel, 0, 0)
            self.main.grid.addWidget(self.main.zona2_precios, 0, 1)
            self.main.zona1_carrusel.show()
            self.main.zona2_precios.show()
            self.main.grid.setColumnStretch(0, 1)
            self.main.grid.setColumnStretch(1, 1)
        elif self.main.layout_mode == 3:
            self.main.grid.addWidget(self.main.zona1_carrusel, 0, 0)
            self.main.grid.addWidget(self.main.zona2_precios, 0, 1)
            self.main.zona1_carrusel.show()
            self.main.zona2_precios.show()
            
            # En modo 3, promo_manager se encarga de rotar zona3 y zona4 en la columna 2.
            # Por defecto mostramos zona3 al inicio.
            self.main.grid.addWidget(self.main.zona3_extra1, 0, 2)
            self.main.zona3_extra1.show()
            
            self.main.grid.setColumnStretch(0, 1)
            self.main.grid.setColumnStretch(1, 1)
            self.main.grid.setColumnStretch(2, 1)
        elif self.main.layout_mode == 4:
            self.main.grid.addWidget(self.main.zona1_carrusel, 0, 0)
            self.main.grid.addWidget(self.main.zona2_precios, 0, 1) 
            self.main.grid.addWidget(self.main.zona3_extra1, 0, 2)
            self.main.grid.addWidget(self.main.zona4_extra2, 0, 3)
            self.main.zona1_carrusel.show()
            self.main.zona2_precios.show()
            self.main.zona3_extra1.show()
            self.main.zona4_extra2.show()
            
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
