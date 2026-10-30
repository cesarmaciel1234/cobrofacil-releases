"""
motor_huevo.py - Motor matemático para cálculo de promedios de huevo
TPV Pro 2026 · Cobro Fácil POS

Estructura:
- Cajón = 12 maples
- 1 maple = 30 huevos
- Total cajón = 360 huevos
- Cada fila de la tabla es una fórmula. Vender un cajón por esa fórmula es una cuenta aparte.
"""

class MotorHuevo:
    """Motor de cálculos para huevo"""

    @staticmethod
    def calcular_costo_cajon(precio_cajon: float, maples_por_cajon: int = 12, huevos_por_maple: int = 30):
        """Costo de un maple de 30 y de un huevo."""
        total_huevos = maples_por_cajon * huevos_por_maple
        costo_maple = precio_cajon / maples_por_cajon
        costo_huevo = precio_cajon / total_huevos
        return costo_maple, costo_huevo, total_huevos

    @staticmethod
    def ganancia_de_cajon(precio_cajon: float, huevos: int, precio_venta: float, precio_mayoreo: float = 0.0) -> dict:
        """Cuánto deja vender un cajón por esta fórmula, y por mayor si tiene precio."""
        try:
            huevos = int(huevos or 0)
            precio_cajon = float(precio_cajon or 0)
            precio_venta = float(precio_venta or 0)
            precio_mayoreo = float(precio_mayoreo or 0)
        except (TypeError, ValueError):
            huevos, precio_cajon, precio_venta, precio_mayoreo = 0, 0.0, 0.0, 0.0
        vacio = {
            "salen": 0.0, "costo": 0.0, "pct": 0.0, "pct_mayoreo": 0.0,
            "venta": 0.0, "ganancia": 0.0, "venta_mayoreo": 0.0, "ganancia_mayoreo": 0.0,
        }
        if huevos <= 0 or precio_cajon <= 0:
            return vacio
        salen = 360.0 / huevos
        costo = precio_cajon / salen
        pct = ((precio_venta / costo) - 1) * 100 if costo > 0 and precio_venta > 0 else 0.0
        pct_mayoreo = ((precio_mayoreo / costo) - 1) * 100 if costo > 0 and precio_mayoreo > 0 else 0.0
        venta = salen * precio_venta if precio_venta > 0 else 0.0
        mayoreo = salen * precio_mayoreo if precio_mayoreo > 0 else 0.0
        return {
            "salen": salen,
            "costo": costo,
            "pct": pct,
            "pct_mayoreo": pct_mayoreo,
            "venta": venta,
            "ganancia": venta - precio_cajon if venta else 0.0,
            "venta_mayoreo": mayoreo,
            "ganancia_mayoreo": mayoreo - precio_cajon if mayoreo else 0.0,
        }

    @staticmethod
    def calcular_precio_venta_por_maple(costo_maple: float, huevos_venta: int, pct_ganancia: float = 0.0):
        costo_total = costo_maple * (huevos_venta / 30)
        return costo_total * (1 + pct_ganancia / 100.0)

    @staticmethod
    def recalcular_fila(columna_editada: int, nuevo_valor: float, costo_maple: float, huevos_venta: int):
        pct = 0.0
        precio_venta = 0.0
        costo_proporcion = costo_maple * (huevos_venta / 30)
        if columna_editada == 3:
            pct = nuevo_valor
            if costo_proporcion > 0:
                precio_venta = costo_proporcion * (1 + pct / 100.0)
        elif columna_editada == 4:
            precio_venta = nuevo_valor
            if costo_proporcion > 0:
                pct = ((precio_venta / costo_proporcion) - 1) * 100.0
        return pct, precio_venta

    @staticmethod
    def obtener_precios_inventario(db, tipos_huevo: list):
        precios = {}
        try:
            from src.motor_descuentos.mayoreo.motor import MotorMayoreo
            motor = MotorMayoreo(db=db)
            for tipo in tipos_huevo:
                cfg = motor.obtener_por_nombre(tipo)
                precios[tipo] = cfg["precio"] if cfg and cfg.get("precio", 0) > 0 else 0.0
        except Exception as e:
            print(f"Error obteniendo precios de inventario: {e}")
        return precios
