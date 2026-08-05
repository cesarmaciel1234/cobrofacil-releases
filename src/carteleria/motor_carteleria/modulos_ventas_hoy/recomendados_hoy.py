import random

from src.base_de_datos.database import db_manager
from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
from src.carteleria.motor_carteleria.modulos_ventas_hoy.buscador_precios_y_stock import BuscadorDePreciosYStock

class ModuloRecomendadoHoy:
    """
    Módulo 3 de Cartelería (Fácil para que lo entienda un niño de 10 años):
    ¿Qué hace? Elige productos estratégicos para RECOMENDAR en el cartel el día de HOY.
    Busca aquellos productos que tienen buen stock en heladera pero que necesitan "un empujoncito" 
    para venderse hoy (menos vendidos del momento), o productos recomendados especiales del catálogo 
    para tentar e inspirar a los clientes en la cola.
    """
    
    def obtener_productos_para_cartel(self, limit=10):
        titulo_cartel = "RECOMENDADO HOY"
        
        # 1. Buscamos en el motor de ventas aquellos productos con rotación lenta en la semana ("clavos") para empujarlos
        ventas_empujar = motor_ventas.get_top_ventas(limit=limit, periodo="semana", modo="clavos")
        lista_pantalla = BuscadorDePreciosYStock.armar_lista_para_pantalla(ventas_empujar)
        
        # 2. Si hay menos de 5 recomendaciones, sumamos productos que tengan buen stock desde la base de datos
        if len(lista_pantalla) < 5:
            nombres_ya_puestos = {item[0].lower() for item in lista_pantalla}
            
            # Consultar productos en stock (sin ORDER BY RAND: timeout en MariaDB con inventario grande)
            fetch_limit = limit * 2
            q_sugerencias = "SELECT nombre FROM productos WHERE stock > 0 ORDER BY nombre LIMIT ?"
            rows_sug = db_manager.execute_query(q_sugerencias, (fetch_limit,))
            if rows_sug:
                rows_sug = random.sample(list(rows_sug), min(fetch_limit, len(rows_sug)))
            lista_nombres_sug = [{'nombre': r['nombre'] if isinstance(r, dict) else r[0], 'cantidad': 5.0} for r in rows_sug] if rows_sug else []
            
            sugerencias_armadas = BuscadorDePreciosYStock.armar_lista_para_pantalla(lista_nombres_sug)
            for prod in sugerencias_armadas:
                if prod[0].lower() not in nombres_ya_puestos:
                    lista_pantalla.append(prod)
                    nombres_ya_puestos.add(prod[0].lower())
                if len(lista_pantalla) >= limit:
                    break
                    
        return lista_pantalla[:limit], titulo_cartel
