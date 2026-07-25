from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
from src.carteleria.motor_carteleria.modulos_ventas_hoy.buscador_precios_y_stock import BuscadorDePreciosYStock

class ModuloMasVolumenHoy:
    """
    Módulo 2 de Cartelería (Fácil para que lo entienda un niño de 10 años):
    ¿Qué hace? Revisa todos los tickets de cobro de HOY y suma la cantidad total en Kilos o Unidades.
    Muestra los cortes de carne o artículos en la pantalla por mayor peso o cantidad vendida ("Con Más Volumen").
    Si el local recién abre y hay poquitas ventas, completa con las ventas de mayor volumen de la semana.
    """
    
    def obtener_productos_para_cartel(self, limit=10):
        titulo_cartel = "🔥 CORTES TOP: MEGA VENTAS"
        
        # 1. Consultamos las ventas con más kilos/unidades despachadas HOY
        ventas_hoy = motor_ventas.get_top_ventas(limit=limit, periodo="hoy", modo="volumen")
        lista_pantalla = BuscadorDePreciosYStock.armar_lista_para_pantalla(ventas_hoy)
        
        # 2. Respaldo inteligente si la jornada es joven y hay menos de 5 productos en el ranking de hoy
        if len(lista_pantalla) < 5:
            ventas_recientes = motor_ventas.get_top_ventas(limit=limit, periodo="semana", modo="volumen")
            lista_complementar = BuscadorDePreciosYStock.armar_lista_para_pantalla(ventas_recientes)
            
            nombres_ya_puestos = {item[0].lower() for item in lista_pantalla}
            for prod in lista_complementar:
                if prod[0].lower() not in nombres_ya_puestos:
                    lista_pantalla.append(prod)
                    nombres_ya_puestos.add(prod[0].lower())
                if len(lista_pantalla) >= limit:
                    break
                    
        return lista_pantalla[:limit], titulo_cartel
