class PromoManager:
    """
    Gestor e Intercalador Inteligente de Promociones y Chef Lobo (Tan simple para que lo entienda un niño de 10 años):
    ¿Qué hace? En las pantallas del local, en el Modo 3 (3 columnas), no hay espacio suficiente para poner al 
    Chef Lobo Y a las Promos Especiales al mismo tiempo sin que todo quede amontonado y chiquito.
    
    Este módulo independiente se encarga de 'intercalar' (turnar de forma organizada) ambos carteles:
    - Primer turno: Muestra el cartel de PROMO ESPECIAL / COMBO / VENTA CRUZADA (zona3_extra1).
    - Siguiente turno: Lo oculta suavemente y pone en su lugar al CHEF LOBO con las recomendaciones del día y el clima (zona4_extra2).
    
    ¡Cero conflictos! Así los clientes disfrutan tanto las promociones como los consejos del Chef Lobo y todo el sistema 
    se mantiene modular sin que las pantallas se choquen.
    """
    def __init__(self, main_window):
        self.main = main_window
        self.turno_actual = 0  # 0 = Combos/Promos Especiales (zona3), 1 = Chef Lobo (zona4)

    def actualizar_pantallas_promocionales(self):
        """
        Se ejecuta al aplicar o ciclar los modos de diseño (Layout Mode).
        Asegura que el cartel correcto se muestre según las columnas disponibles.
        """
        modo = getattr(self.main, 'layout_mode', 1)
        if modo == 3:
            # En modo 3 de 3 columnas, intercalamos zona3 (Promos) y zona4 (Chef Lobo) en la Columna 2
            self.aplicar_turno_actual()
        elif modo == 4:
            # En modo de 4 columnas (pantallas muy anchas), hay espacio para ambos al mismo tiempo
            if hasattr(self.main, 'zona3_extra1') and hasattr(self.main, 'zona4_extra2'):
                self.main.zona3_extra1.show()
                self.main.zona4_extra2.show()

    def aplicar_turno_actual(self):
        """
        Coloca en la columna promocional (Columna 2) el cartel que corresponde a este turno.
        """
        if getattr(self.main, 'layout_mode', 1) != 3:
            return
            
        try:
            grid = self.main.grid
            zona3 = self.main.zona3_extra1
            zona4 = self.main.zona4_extra2
            
            # Remover suavemente ambos del grid si estaban colocados
            if zona3:
                grid.removeWidget(zona3)
                zona3.hide()
            if zona4:
                grid.removeWidget(zona4)
                zona4.hide()
                
            # Turno 0 -> Promos Especiales y Venta Cruzada
            # Turno 1 -> Chef Lobo con recomendaciones IA y el clima
            if self.turno_actual == 0:
                if zona3:
                    grid.addWidget(zona3, 0, 2)
                    zona3.show()
                    if hasattr(zona3, 'motor') and hasattr(zona3.motor, 'start') and not zona3.motor.isRunning():
                        zona3.motor.start()
            else:
                if zona4:
                    grid.addWidget(zona4, 0, 2)
                    zona4.show()
                    if hasattr(zona4, 'motor') and hasattr(zona4.motor, 'start') and not zona4.motor.isRunning():
                        zona4.motor.start()
                        
        except Exception as e:
            print(f"Error en PromoManager al intercalar pantallas: {e}")

    def rotar(self):
        """
        Alterna el turno: de Promos y Combos cambia al Chef Lobo, y del Chef Lobo regresa a Promos y Combos.
        """
        if getattr(self.main, 'layout_mode', 1) == 3:
            self.turno_actual = (self.turno_actual + 1) % 2
            self.aplicar_turno_actual()
