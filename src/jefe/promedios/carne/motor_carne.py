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

    @staticmethod
    def recalcular_tabla(filas: list, costo_real_kg: float, col_editada: int = -1, fila_editada: int = -1, valor_editado: float = 0.0, from_calc: bool = False):
        """
        Recalcula todas las filas de la tabla de carnes.
        Retorna lista de diccionarios con valores calculados y totales.
        """
        resultados = []
        t_vn = 0.0
        t_gn = 0.0
        t_vo = 0.0
        t_go = 0.0

        for r_idx, fila in enumerate(filas):
            if len(fila) < 13:
                continue

            try:
                kilos = float(fila[ColumnasCarne.KILOS] or 0)
                pv = float(fila[ColumnasCarne.PV_KG] or 0)
                pg = float(fila[ColumnasCarne.MARGEN_V] or 0)
                pm = float(fila[ColumnasCarne.PM_KG] or 0)
                pmg = float(fila[ColumnasCarne.MARGEN_M] or 0)

                # Si se editó una columna específica, actualizar el valor correspondiente
                if r_idx == fila_editada:
                    if col_editada == ColumnasCarne.MARGEN_V:
                        pg = valor_editado
                    elif col_editada == ColumnasCarne.PV_KG:
                        pv = valor_editado
                    elif col_editada == ColumnasCarne.MARGEN_M:
                        pmg = valor_editado
                    elif col_editada == ColumnasCarne.PM_KG:
                        pm = valor_editado

                c_ed = col_editada if r_idx == fila_editada else -1
                calc = MotorCarne.calcular_fila(
                    costo_real_kg, kilos, pv, pg, pm, pmg, c_ed, from_calc
                )

                t_vn += calc["vn"]
                t_gn += calc["gn"]
                t_vo += calc["vo"]
                t_go += calc["go"]

                resultados.append(calc)
            except:
                resultados.append({
                    "pv": 0.0, "pg": 0.0, "pm": 0.0, "pmg": 0.0,
                    "v_costo": 0.0, "vn": 0.0, "gn": 0.0, "vo": 0.0, "go": 0.0
                })

        return {
            "filas": resultados,
            "totales": {
                "vn": t_vn,
                "gn": t_gn,
                "vo": t_vo,
                "go": t_go
            }
        }
