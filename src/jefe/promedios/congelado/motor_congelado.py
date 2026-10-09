"""
motor_congelado.py - Motor matemático para cálculo de promedios de congelados
TPV Pro 2026 · Cobro Fácil POS
"""

class MotorCongelado:
    """Motor de cálculos para productos congelados"""
    
    @staticmethod
    def calcular_costo_kilo(kilos_totales: float, precio_kg: float, merma: float = 0.0):
        """
        Calcula el costo real por kg considerando merma
        
        Args:
            kilos_totales: Peso total en kg
            precio_kg: Precio por kg
            merma: Porcentaje de merma (0-100)
        
        Returns:
            (costo_real_kg, kilos_utiles)
        """
        kilos_merma = kilos_totales * (merma / 100.0)
        kilos_utiles = kilos_totales - kilos_merma
        total_compra = kilos_totales * precio_kg
        costo_real_kg = total_compra / kilos_utiles if kilos_utiles > 0 else 0.0
        
        return costo_real_kg, kilos_utiles
    
    @staticmethod
    def recalcular_fila(kilos: float, costo_real_kg: float, pv: float, pg: float, pm: float, pmg: float, col_editada: int = -1, valor_editado: float = 0.0, from_calc: bool = False):
        """
        Recalcula una fila individual de la tabla de congelados.
        Retorna diccionario con todos los valores calculados.
        """
        if costo_real_kg > 0:
            # Venta Normal
            if col_editada == 4:  # % Ganancia
                pg = valor_editado
                pv = costo_real_kg * (1 + pg / 100)
            else:
                pg = ((pv / costo_real_kg) - 1) * 100 if pv > 0 else 0.0

            # Venta Mayoreo
            if col_editada == 7:  # % Mayoreo
                pmg = valor_editado
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
            "costo_real_kg": costo_real_kg,
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
        Recalcula todas las filas de la tabla de congelados.
        Retorna lista de diccionarios con valores calculados y totales.
        """
        resultados = []
        t_vn = 0.0
        t_gn = 0.0
        t_vo = 0.0
        t_go = 0.0

        for r_idx, fila in enumerate(filas):
            if len(fila) < 12:
                continue

            try:
                kilos = float(fila[1] or 0)
                pv = float(fila[3] or 0)
                pg = float(fila[4] or 0)
                pm = float(fila[5] or 0)
                pmg = float(fila[7] or 0)

                val = valor_editado if r_idx == fila_editada else 0.0
                calc = MotorCongelado.recalcular_fila(
                    kilos, costo_real_kg, pv, pg, pm, pmg,
                    col_editada, val, from_calc
                )

                t_vn += calc["vn"]
                t_gn += calc["gn"]
                t_vo += calc["vo"]
                t_go += calc["go"]

                resultados.append(calc)
            except:
                resultados.append({
                    "costo_real_kg": costo_real_kg,
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
