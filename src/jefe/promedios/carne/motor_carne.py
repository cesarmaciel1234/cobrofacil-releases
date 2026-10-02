# -*- coding: utf-8 -*-
class MotorCarne:
    @staticmethod
    def get_cortes(tipo="Media Res"):
        if tipo == "Mocho":
            return [("Bola de Lomo", 6), ("Nalga", 8), ("Cuadril", 4), ("Peceto", 3), ("Cuadrada", 5), ("Tortuguita", 2)]
        elif tipo == "Pecho":
            return [("Asado", 10), ("Vacío", 5), ("Matambre", 2), ("Tapa de asado", 3), ("Falda", 4), ("Entraña", 1)]
        else: # Media Res
            return [
                ("Matambre", 1), ("Paleta", 6), ("Palomita", 1), ("Osobuco", 6), 
                ("Tapa de asado", 2), ("Vacío", 5), ("Asado", 10), ("Nalga", 8), 
                ("Bola de Lomo", 6), ("Cuadril", 4), ("Peceto", 3), ("Cuadrada", 5),
                ("Falda", 4), ("Entraña", 1), ("Roast Beef", 5), ("Bife Ancho", 4), ("Bife Angosto", 4)
            ]
