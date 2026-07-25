from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
from src.carteleria.motor_carteleria.modulos_ventas_hoy.buscador_precios_y_stock import BuscadorDePreciosYStock

class ModuloMasElegidosHoy:
    """
    Módulo 1 de Cartelería (Fácil para que lo entienda un niño de 10 años):
    ¿Qué hace? Mira los tickets de cobro que se hicieron HOY y cuenta qué productos 
    eligió la mayor cantidad de clientes (frecuencia por ticket).
    Si recién abriste el local hoy temprano y aún se vendió poquito, completa 
    inteligentemente con los más elegidos de la semana para que la pantalla nunca quede vacía.
    """
    
    def obtener_productos_para_cartel(self, limit=10):
        titulo_cartel = "🔥 LOS MÁS ELEGIDOS HOY"
        
        # 1. Consultamos al motor central las ventas más frecuentes de HOY
        ventas_hoy = motor_ventas.get_top_ventas(limit=limit, periodo="hoy", modo="frecuencia")
        lista_pantalla = BuscadorDePreciosYStock.armar_lista_para_pantalla(ventas_hoy)
        
        # 2. Si recién abre el comercio hoy y tenemos menos de 5 productos vendidos, completamos con la semana
        if len(lista_pantalla) < 5:
            ventas_recientes = motor_ventas.get_top_ventas(limit=limit, periodo="semana", modo="frecuencia")
            lista_complementar = BuscadorDePreciosYStock.armar_lista_para_pantalla(ventas_recientes)
            
            nombres_ya_puestos = {item[0].lower() for item in lista_pantalla}
            for prod in lista_complementar:
                if prod[0].lower() not in nombres_ya_puestos:
                    lista_pantalla.append(prod)
                    nombres_ya_puestos.add(prod[0].lower())
                if len(lista_pantalla) >= limit:
                    break
                    
        return lista_pantalla[:limit], titulo_cartel
