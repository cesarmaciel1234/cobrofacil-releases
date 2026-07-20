class PromedioRes:
    @staticmethod
    def get_cortes():
        return [
            ("Matambre", 1, 40), ("Paleta", 6, 36), ("Palomita", 1, 36), ("Osobuco", 6, -22),
            ("Tapa de asado", 2, 36), ("Vacío", 5, 38), ("Entraña", 1, 36), ("Asado", 9, 27),
            ("Roast beef", 7, 22), ("Lomo", 2, 57), ("Bife Angosto", 6, 36), ("Falda", 3, 15),
            ("Cuadril", 3, 57), ("Colita", 1, 57), ("Nalga", 5, 57), ("Tapa de nalga", 2, 36),
            ("Peceto", 2, 57), ("Cuadrada", 5, 48), ("Tortuguita", 2, 36), ("Bola de lomo", 4, 48),
            ("Bife chorizo", 3, 57), ("Espinazo", 3, -30),
            ("Bife ancho", 4, 36), ("Falda puchero", 2, 15), ("Picada común", 3, 20)
        ]

class PromedioMocho:
    @staticmethod
    def get_cortes():
        return [
            ("Nalga", 5, 57), ("Cuadrada", 5, 48), ("Peceto", 2, 57),
            ("Bola de lomo", 4, 48), ("Tortuguita", 2, 36), ("Osobuco", 3, -22),
            ("Cuadril", 3, 57), ("Colita de cuadril", 1, 57)
        ]

class PromedioPecho:
    @staticmethod
    def get_cortes():
        return [
            ("Paleta", 6, 36), ("Roast beef", 7, 22), ("Espinazo", 3, -30),
            ("Osobuco", 3, -22), ("Falda puchero", 2, 15), ("Tapa de asado", 2, 36),
            ("Palomita", 1, 36), ("Recorte", 2, 10)
        ]
