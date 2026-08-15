import random
import datetime
from src.base_de_datos.database import db_manager

class MotorIALocal:
    """
    Cerebro de Cartelería 100% Offline.
    Aprende de los tickets de los clientes y genera recomendaciones y combos.
    """
    
    @staticmethod
    def obtener_relacionados(producto_base, limit=3):
        """
        Analiza el historial de ventas (tickets) para encontrar qué otros productos
        se compraron en los MISMOS TICKETS que el producto_base.
        Utiliza el módulo modularizado de VentaCruzadaInteligente que garantiza siempre 3 productos exactos.
        """
        try:
            from src.carteleria.motor_carteleria.venta_cruzada import VentaCruzadaInteligente
            return VentaCruzadaInteligente.obtener_relacionados_para_ticket(producto_base, limit)
        except Exception as e:
            print(f"Error en obtener_relacionados: {e}")
            return ["Carbón Premium", "Chorizo Puro Cerdo", "Provoleta Especial"][:limit]
                
    @staticmethod
    def _obtener_top_general(limit=3, excluir=None):
        if excluir is None:
            excluir = []
        try:
            query = """
                SELECT dv.nombre_producto, SUM(dv.cantidad) as total
                FROM detalles_ventas dv
                JOIN productos p ON LOWER(dv.nombre_producto) = LOWER(p.nombre)
                WHERE LOWER(dv.nombre_producto) NOT LIKE '%articulo comun%'
                GROUP BY dv.nombre_producto
                ORDER BY total DESC
            """
            top_general = db_manager.execute_query(query)
            if not top_general:
                top_general = []
            resultados = []
            for item in top_general:
                nombre = item[0] if not isinstance(item, dict) else item['nombre_producto']
                if nombre.lower() not in [e.lower() for e in excluir]:
                    resultados.append(nombre)
                if len(resultados) == limit:
                    break
            
            # Último fallback si la base está totalmente vacía
            if not resultados:
                fallbacks = ["Carbón", "Chorizo", "Morcilla", "Pan", "Bebida"]
                for f in fallbacks:
                    if f.lower() not in [e.lower() for e in excluir]:
                        resultados.append(f)
                    if len(resultados) == limit:
                        break
            
            return resultados
        except:
            return ["Carbón", "Chorizo", "Morcilla"][:limit]

    @staticmethod
    def generar_recomendacion_lobo(clima_tupla, datos_destacados):
        """
        Genera una recomendación basándose en los productos más vendidos
        según el momento del día y el clima.
        """
        try:
            # 1. Determinar contexto
            hoy = datetime.datetime.now()
            hora = hoy.hour
            dia_idx = hoy.weekday() # 0 = Lunes, 6 = Domingo
            
            if 6 <= hora < 12: momento = "mañana"
            elif 12 <= hora < 19: momento = "tarde"
            else: momento = "noche"
            
            # Obtener top venta global para usar como estrella
            estrella = "nuestros mejores cortes"
            estrella_precio = 0
            estrella_oferta = 0
            
            top = MotorIALocal._obtener_top_general(limit=5)
            if top:
                estrella = random.choice(top)
            
            # 2. Plantillas dinámicas (sin depender de motor_ia de NLP)
            plantillas = [
                "¡Salió {clima} en {localidad}! Los vecinos están llevando mucho {estrella}, ideal para hoy.",
                "Para este momento de la {momento}, te recomendamos llevar {estrella}.",
                "¡Aprovechá la frescura de hoy! {estrella} es el corte más elegido de la semana."
            ]
            
            # Finde (Viernes a Domingo)
            if dia_idx >= 4:
                plantillas.append("¡Fin de semana de asado! No te olvides del {estrella} y el carbón.")
                
            clima = clima_tupla[0] if clima_tupla else "el día"
            if clima == "sol": clima = "el sol"
            elif clima == "nube": clima = "un día nublado"
            elif clima == "lluvia": clima = "la lluvia"
            
            localidad = clima_tupla[1].split()[-1] if clima_tupla and len(clima_tupla) > 1 else "tu barrio"
            
            plantilla_elegida = random.choice(plantillas)
            mensaje = plantilla_elegida.format(
                clima=clima, 
                localidad=localidad, 
                estrella=estrella, 
                momento=momento
            )
            
            # 3. Datos del producto para mostrar
            query2 = "SELECT precio, precio_oferta FROM productos WHERE LOWER(nombre) = LOWER(?)"
            rows = db_manager.execute_query(query2, (estrella,))
            res = rows[0] if rows else None
            if res:
                if isinstance(res, dict):
                    estrella_precio = float(res.get('precio') or 0)
                    estrella_oferta = float(res.get('precio_oferta') or 0)
                else:
                    estrella_precio = float(res[0] or 0)
                    estrella_oferta = float(res[1] or 0)
                
            # Si encontramos datos en datos_destacados (preferimos sugerir cosas que están en la cartelería global)
            if datos_destacados and not res:
                p = random.choice(datos_destacados)
                if len(p) >= 3:
                    estrella = p[0]
                    estrella_precio = p[1]
                    estrella_oferta = p[2]
            
            return mensaje, estrella, estrella_precio, estrella_oferta
            
        except Exception as e:
            print(f"Error en generar_recomendacion_lobo: {e}")
            return "¡Llevá la mejor calidad al mejor precio!", "Oferta Especial", 0, 0
