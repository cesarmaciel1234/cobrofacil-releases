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
        Si no hay suficientes datos empíricos, hace un fallback inteligente.
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Buscamos IDs de ventas donde se vendió el producto_base
            cursor.execute("""
                SELECT id_venta FROM detalles_ventas 
                WHERE LOWER(nombre_producto) = LOWER(?)
            """, (producto_base,))
            
            ventas = cursor.fetchall()
            ids_ventas = [v[0] if not isinstance(v, dict) else v['id_venta'] for v in ventas]
            
            if len(ids_ventas) >= 2:
                # Si hay al menos 2 tickets con este producto, buscamos co-ocurrencias
                placeholders = ','.join(['?'] * len(ids_ventas))
                
                # Buscamos otros productos en esos mismos tickets, agrupados por frecuencia
                query = f"""
                    SELECT dv.nombre_producto, COUNT(*) as frecuencia
                    FROM detalles_ventas dv
                    JOIN productos p ON LOWER(dv.nombre_producto) = LOWER(p.nombre)
                    WHERE dv.id_venta IN ({placeholders})
                      AND LOWER(dv.nombre_producto) != LOWER(?)
                      AND LOWER(dv.nombre_producto) NOT LIKE '%articulo comun%'
                    GROUP BY dv.nombre_producto
                    ORDER BY frecuencia DESC
                    LIMIT ?
                """
                
                params = ids_ventas + [producto_base, limit]
                cursor.execute(query, params)
                relacionados = cursor.fetchall()
                
                nombres = [r[0] if not isinstance(r, dict) else r['nombre_producto'] for r in relacionados]
                
                # Rellenar si faltan
                if len(nombres) < limit:
                    nombres.extend(MotorIALocal._obtener_top_general(limit - len(nombres), excluir=nombres + [producto_base]))
                    
                return nombres
            else:
                # Fallback: No hay datos suficientes para este producto, usar TOP Ventas global
                return MotorIALocal._obtener_top_general(limit, excluir=[producto_base])
                
        except Exception as e:
            print(f"Error en obtener_relacionados: {e}")
            return ["Falda", "Chorizo", "Carbón"] # Fallback rústico
                
    @staticmethod
    def _obtener_top_general(limit=3, excluir=None):
        if excluir is None:
            excluir = []
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT dv.nombre_producto, SUM(dv.cantidad) as total
                FROM detalles_ventas dv
                JOIN productos p ON LOWER(dv.nombre_producto) = LOWER(p.nombre)
                WHERE LOWER(dv.nombre_producto) NOT LIKE '%articulo comun%'
                GROUP BY dv.nombre_producto
                ORDER BY total DESC
            """)
            
            top_general = cursor.fetchall()
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
            
            top = MotorIALocal._obtener_top_general(limit=1)
            if top:
                estrella = top[0]
            
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
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT precio, precio_oferta FROM productos WHERE LOWER(nombre) = LOWER(?)", (estrella,))
            res = cursor.fetchone()
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
