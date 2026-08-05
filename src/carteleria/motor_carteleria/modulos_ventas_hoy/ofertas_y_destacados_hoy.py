import random

from src.base_de_datos.database import db_manager
from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
from src.carteleria.motor_carteleria.modulos_ventas_hoy.buscador_precios_y_stock import BuscadorDePreciosYStock

class ModuloOfertasYDestacadosHoy:
    """
    Módulo 4 de Cartelería (Fácil para que lo entienda un niño de 10 años):
    ¿Qué hace? Busca las mejores OFERTAS, DESCUENTOS y PRODUCTOS DESTACADOS para mostrar HOY.
    Revisa tanto las ofertas programadas en el cartel global como los productos con precio promocional.
    Además, le suma la cantidad real vendida en los tickets del día para mostrar qué tan popular es la oferta.
    """
    
    def obtener_productos_para_cartel(self, limit=10):
        titulo_cartel = "OFERTAS Y DESTACADOS HOY"
        
        # 1. Buscamos productos que tengan un precio de oferta mayor a 0, tanto en carteleria_global como en productos
        q_ofertas = "SELECT nombre_producto FROM carteleria_global WHERE precio_oferta > 0 ORDER BY precio_oferta DESC LIMIT ?"
        rows = db_manager.execute_query(q_ofertas, (limit * 2,))
        
        nombres_encontrados = []
        if rows:
            for r in rows:
                nom = r['nombre_producto'] if isinstance(r, dict) else r[0]
                if nom: nombres_encontrados.append(nom)
                
        # 2. Si hay pocas ofertas en carteleria_global, buscamos en la tabla principal 'productos'
        if len(nombres_encontrados) < limit:
            q_prod = "SELECT nombre FROM productos WHERE precio_oferta > 0 LIMIT ?"
            rows_p = db_manager.execute_query(q_prod, (min(limit * 20, 200),))
            if rows_p:
                rows_p = random.sample(list(rows_p), min(limit * 2, len(rows_p)))
            if rows_p:
                for r in rows_p:
                    nom = r['nombre'] if isinstance(r, dict) else r[0]
                    if nom and nom not in nombres_encontrados:
                        nombres_encontrados.append(nom)
                        
        # 3. Si aún faltaran productos (ej: ninguna oferta configurada en la base), traemos los más elegidos de hoy/semana
        if len(nombres_encontrados) < 5:
            top_extra = motor_ventas.get_top_ventas(limit=limit, periodo="semana", modo="volumen")
            for t in top_extra:
                nom = t['nombre'] if isinstance(t, dict) else t[0]
                if nom and nom not in nombres_encontrados:
                    nombres_encontrados.append(nom)
                    
        # 4. Ahora para cada nombre encontrado, consultamos sus ventas FRESCAS DE HOY en los tickets
        lista_con_ventas = []
        for nom in nombres_encontrados:
            ventas_hoy_cajas = motor_ventas.get_unidades_vendidas(nom, periodo="hoy")
            if ventas_hoy_cajas <= 0:
                # Si recién abre, tomamos volumen de la semana o asignamos 10 para rotación visual activa
                ventas_hoy_cajas = max(10.0, motor_ventas.get_unidades_vendidas(nom, periodo="semana"))
            lista_con_ventas.append({'nombre': nom, 'cantidad': ventas_hoy_cajas})
            
        lista_pantalla = BuscadorDePreciosYStock.armar_lista_para_pantalla(lista_con_ventas)
        
        return lista_pantalla[:limit], titulo_cartel
