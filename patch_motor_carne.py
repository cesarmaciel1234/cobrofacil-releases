import os

motor_carne = '''class MotorCarne:
    @staticmethod
    def get_cortes(tipo="Media Res"):
        if tipo == "Mocho":
            return [("Bola de Lomo", 6), ("Nalga", 8), ("Cuadril", 4), ("Peceto", 3), ("Asado", 0)]
        elif tipo == "Pecho":
            return [("Asado", 10), ("Vacío", 5), ("Matambre", 2), ("Tapa de asado", 3), ("Falda", 4)]
        else: # Media Res
            return [("Matambre", 1), ("Paleta", 6), ("Palomita", 1), ("Osobuco", 6), ("Tapa de asado", 2), ("Vacío", 5), ("Asado", 10), ("Nalga", 8), ("Bola de Lomo", 6), ("Cuadril", 4), ("Peceto", 3)]
'''
with open('src/jefe/promedios/carne/motor_carne.py', 'w', encoding='utf-8') as f:
    f.write(motor_carne)

