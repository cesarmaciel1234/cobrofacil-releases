"""
motor_huevo.py - Motor matemático para cálculo de promedios de huevo
TPV Pro 2026 · Cobro Fácil POS

Estructura:
- Cajón = 12 maples
- 1 maple = 30 huevos
- Total cajón = 360 huevos = 30 docenas
- Venta por maple: 30, 15, 10, 6 huevos
"""

class MotorHuevo:
    """Motor de cálculos para huevo"""
    
    @staticmethod
    def calcular_costo_cajon(precio_cajon: float, maples_por_cajon: int = 12, huevos_por_maple: int = 30):
        """
        Calcula el costo por maple y por huevo
        
        Args:
            precio_cajon: Precio total del cajón
            maples_por_cajon: Cantidad de maples por cajón (default 12)
            huevos_por_maple: Huevos por maple (default 30)
        
        Returns:
            (costo_por_maple, costo_por_huevo, total_huevos)
        """
        total_huevos = maples_por_cajon * huevos_por_maple
        costo_maple = precio_cajon / maples_por_cajon
        costo_huevo = precio_cajon / total_huevos
        
        return costo_maple, costo_huevo, total_huevos
    
    @staticmethod
    def calcular_precio_venta_por_maple(costo_maple: float, huevos_venta: int, pct_ganancia: float = 0.0):
        """
        Calcula el precio de venta por maple según cantidad de huevos
        
        Args:
            costo_maple: Costo del maple
            huevos_venta: Cantidad de huevos en el maple de venta (30, 15, 10, 6)
            pct_ganancia: Porcentaje de ganancia
        
        Returns:
            precio_venta_maple
        """
        costo_total = costo_maple * (huevos_venta / 30)  # Proporción del maple
        precio_venta = costo_total * (1 + pct_ganancia / 100.0)
        
        return precio_venta
    
    @staticmethod
    def recalcular_fila(columna_editada: int, nuevo_valor: float, costo_maple: float, huevos_venta: int):
        """
        Recalcula % ganancia o precio venta según columna editada
        
        Args:
            columna_editada: 3 = % Ganancia, 4 = Precio Venta
            nuevo_valor: Nuevo valor ingresado
            costo_maple: Costo por maple
            huevos_venta: Cantidad de huevos en este maple de venta
        
        Returns:
            (pct_ganancia, precio_venta)
        """
        pct = 0.0
        precio_venta = 0.0
        
        costo_proporcion = costo_maple * (huevos_venta / 30)
        
        if columna_editada == 3:  # % Ganancia
            pct = nuevo_valor
            if costo_proporcion > 0:
                precio_venta = costo_proporcion * (1 + pct / 100.0)
        
        elif columna_editada == 4:  # Precio Venta
            precio_venta = nuevo_valor
            if costo_proporcion > 0:
                pct = ((precio_venta / costo_proporcion) - 1) * 100.0
        
        return pct, precio_venta
    
    @staticmethod
    def obtener_precios_inventario(db, tipos_huevo: list):
        """
        Obtiene los precios actuales de inventario para los tipos de huevo
        
        Args:
            db: DatabaseManager
            tipos_huevo: Lista de nombres de productos de huevo
        
        Returns:
            Dict con precios actuales
        """
        precios = {}
        try:
            from src.motor_descuentos.mayoreo.motor import MotorMayoreo
            motor = MotorMayoreo(db=db)
            
            for tipo in tipos_huevo:
                cfg = motor.obtener_por_nombre(tipo)
                if cfg and cfg.get("precio", 0) > 0:
                    precios[tipo] = cfg["precio"]
                else:
                    precios[tipo] = 0.0
        except Exception as e:
            print(f"Error obteniendo precios de inventario: {e}")
        
        return precios
