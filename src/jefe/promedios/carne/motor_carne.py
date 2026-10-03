# -*- coding: utf-8 -*-
from enum import IntEnum

class ColumnasCarne(IntEnum):
    CORTE = 0
    KILOS = 1
    COSTO = 2
    PV_KG = 3
    MARGEN_V = 4
    PM_KG = 5
    VACIO_6 = 6
    MARGEN_M = 7
    VALOR_COSTO = 8
    VENTA_NORMAL = 9
    VENTA_MAYOREO = 10
    GANANCIA_N = 11
    GANANCIA_M = 12

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

    @staticmethod
    def calcular_fila(costo_real_kg, kilos, pv, pg, pm, pmg, c_ed, from_calc):
        """
        Calcula las matemáticas financieras para una fila de la tabla de carnes.
        Retorna un dict con todos los valores computados.
        """
        # Calcular márgenes si hay costo real
        if costo_real_kg > 0:
            # Venta Normal
            if c_ed == ColumnasCarne.MARGEN_V:
                pv = costo_real_kg * (1 + pg / 100)
            else:
                pg = ((pv / costo_real_kg) - 1) * 100 if pv > 0 else 0.0
            
            # Venta Mayoreo
            if c_ed == ColumnasCarne.MARGEN_M:
                pm = costo_real_kg * (1 + pmg / 100)
            else:
                pmg = ((pm / costo_real_kg) - 1) * 100 if pm > 0 else 0.0
        else:
            if from_calc:
                pg = 0.0
                pmg = 0.0

        # Totales
        v_costo = kilos * costo_real_kg
        
        vn = (kilos * pv) if pv > 0 else 0.0
        gn = vn - v_costo if pv > 0 else 0.0
        
        vo = (kilos * pm) if pm > 0 else 0.0
        go = vo - v_costo if pm > 0 else 0.0

        return {
            "pv": pv,
            "pg": pg,
            "pm": pm,
            "pmg": pmg,
            "v_costo": v_costo,
            "vn": vn,
            "gn": gn,
            "vo": vo,
            "go": go
        }
