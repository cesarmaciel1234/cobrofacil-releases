import random

from src.base_de_datos.database import db_manager
from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas

class VentaCruzadaInteligente:
    """
    Módulo de Venta Cruzada Inteligente (Tan simple para que lo entienda un niño de 10 años):
    ¿Qué hace? Cuando vemos que un cliente está comprando algo (ejemplo: 'Picada Comun'),
    este módulo revisa el historial de tickets de la caja y se fija qué otras cosas suelen 
    comprar los vecinos en el MISMO ticket (por ejemplo, si llevan carne picada, también se llevan asado y pollo).
    
    ¡Garantía de Verificación en 2 Pasos y 3 Productos Relacionados!: 
    Rechaza cobros en negro o ítems genéricos no inventariados (ej: 'Artículo Común'), y si hay poquitos tickets,
    completa inteligentemente con clásicos infaltables de parrilla para que SIEMPRE muestre exactamente 3 recomendaciones.
    """
    
    @staticmethod
    def es_producto_valido(nombre):
        """
        Verificación en dos pasos para Venta Cruzada:
        1. Excluir cobros genéricos / libres (Artículo Común, Venta Libre, etc.) y quitar etiquetas promocionales.
        2. Comprobar que existe genuinamente en el catálogo o promociones.
        """
        if not nombre:
            return False, ""
        nom_limpio = str(nombre).replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
        
        nombres_ignorados = {
            "ARTICULO COMUN", "ARTÍCULO COMÚN", "ARTICULO LIBRE", "ARTÍCULO LIBRE", 
            "VENTA LIBRE", "VARIOS", "COBRO RAPIDO", "COBRO RÁPIDO", 
            "DIFERENCIA", "AJUSTE", "ENVASADO", "TICKET", "SUBTOTAL"
        }
        if not nom_limpio or nom_limpio.upper() in nombres_ignorados:
            return False, nom_limpio
            
        # Validar existencia en base de datos (sin LOWER/TRIM: collation case-insensitive + índice)
        try:
            q_p = "SELECT 1 FROM productos WHERE nombre = ? OR nombre LIKE ? LIMIT 1"
            rows_p = db_manager.execute_query(q_p, (nom_limpio, f"%{nom_limpio}%"))
            if rows_p:
                return True, nom_limpio
            q_c = "SELECT 1 FROM carteleria_global WHERE nombre_producto = ? OR nombre_producto LIKE ? LIMIT 1"
            rows_c = db_manager.execute_query(q_c, (nom_limpio, f"%{nom_limpio}%"))
            if rows_c:
                return True, nom_limpio
        except Exception:
            pass
            
        # Si es un clásico garantizado de parrilla, permitirlo
        clasicos_set = {"carbón premium", "chorizo puro cerdo", "morcilla vasca", "provoleta especial", "pan del día", "falda para parrilla"}
        if nom_limpio.lower() in clasicos_set:
            return True, nom_limpio
            
        return False, nom_limpio
    
    @staticmethod
    def obtener_relacionados_para_ticket(producto_base, limit=3):
        nombres_resultado = []
        _, producto_base_limpio = VentaCruzadaInteligente.es_producto_valido(producto_base)
        if not producto_base_limpio:
            producto_base_limpio = str(producto_base).strip()
            
        nombres_procesados = {producto_base_limpio.lower(), str(producto_base).strip().lower()}
        
        def es_muy_similar(nuevo, procesados):
            nuevo_min = nuevo.lower()
            for p in procesados:
                # Si son idénticos o uno es el plural del otro (agregando 's' o 'es')
                if nuevo_min == p or nuevo_min == p + "s" or nuevo_min == p + "es" or p == nuevo_min + "s" or p == nuevo_min + "es":
                    return True
                # Si una palabra clave principal está contenida (ej: "alita" y "alitas")
                # Exigir un mínimo de 4 letras para no filtrar "pan" y "pancho" accidentalmente
                if len(nuevo_min) > 4 and len(p) > 4:
                    if nuevo_min in p or p in nuevo_min:
                        return True
            return False
        
        try:
            # 1. Buscamos en qué tickets de venta apareció nuestro producto base
            q_ids = "SELECT id_venta FROM detalles_ventas WHERE LOWER(nombre_producto) = LOWER(?) OR LOWER(nombre_producto) LIKE LOWER(?)"
            rows_ventas = db_manager.execute_query(q_ids, (producto_base, f"%{producto_base_limpio}%"))
            ids_ventas = [v[0] if not isinstance(v, dict) else v['id_venta'] for v in rows_ventas] if rows_ventas else []
            
            if ids_ventas:
                placeholders = ','.join(['?'] * len(ids_ventas))
                # 2. Buscamos qué otros productos aparecieron en esos EXACTOS mismos tickets, ordenados por popularidad
                q_coocurrencia = f"""
                    SELECT dv.nombre_producto, COUNT(*) as frecuencia
                    FROM detalles_ventas dv
                    WHERE dv.id_venta IN ({placeholders})
                    GROUP BY dv.nombre_producto
                    ORDER BY frecuencia DESC
                    LIMIT ?
                """
                params = ids_ventas + [limit * 4]
                rows_cooc = db_manager.execute_query(q_coocurrencia, params)
                if rows_cooc:
                    for r in rows_cooc:
                        nom_raw = str(r[0] if not isinstance(r, dict) else r.get('nombre_producto', '')).strip()
                        valido, nom_limpio = VentaCruzadaInteligente.es_producto_valido(nom_raw)
                        if valido and not es_muy_similar(nom_limpio, nombres_procesados):
                            nombres_resultado.append(nom_limpio)
                            nombres_procesados.add(nom_limpio.lower())
                            if len(nombres_resultado) >= limit:
                                break

            # 3. Si aún no tenemos los 3 productos (ej. solo encontró 1 o 2 en el historial), completamos con los Top de HOY y de la Semana
            if len(nombres_resultado) < limit:
                top_ventas = motor_ventas.get_top_ventas(limit=limit * 4, periodo="hoy", modo="frecuencia")
                if len(top_ventas) < limit * 2:
                    top_ventas += motor_ventas.get_top_ventas(limit=limit * 4, periodo="semana", modo="volumen")
                for t in top_ventas:
                    nom_raw = str(t['nombre'] if isinstance(t, dict) else t[0]).strip()
                    valido, nom_limpio = VentaCruzadaInteligente.es_producto_valido(nom_raw)
                    if valido and not es_muy_similar(nom_limpio, nombres_procesados):
                        nombres_resultado.append(nom_limpio)
                        nombres_procesados.add(nom_limpio.lower())
                        if len(nombres_resultado) >= limit:
                            break
                            
            # 4. Si la base de datos es súper nueva o aún faltan para completar el número exacto, completamos con el catálogo en stock
            if len(nombres_resultado) < limit:
                # Sin ORDER BY RAND: timeout en MariaDB con inventario grande
                q_stock = "SELECT nombre FROM productos WHERE stock > 0 ORDER BY nombre LIMIT ?"
                rows_stock = db_manager.execute_query(q_stock, (limit * 8,))
                if rows_stock:
                    rows_stock = random.sample(list(rows_stock), min(limit * 4, len(rows_stock)))
                if rows_stock:
                    for s in rows_stock:
                        nom_raw = str(s[0] if not isinstance(s, dict) else s.get('nombre', '')).strip()
                        valido, nom_limpio = VentaCruzadaInteligente.es_producto_valido(nom_raw)
                        if valido and not es_muy_similar(nom_limpio, nombres_procesados):
                            nombres_resultado.append(nom_limpio)
                            nombres_procesados.add(nom_limpio.lower())
                            if len(nombres_resultado) >= limit:
                                break

        except Exception as e:
            print(f"Error leve en VentaCruzadaInteligente: {e}")
            
        # 5. GARANTÍA ABSOLUTA: Si todo falla o hay poquitos artículos cargados, aseguramos los 3 productos con clásicos invencibles
        clasicos = ["Carbón Premium", "Chorizo Puro Cerdo", "Morcilla Vasca", "Provoleta Especial", "Pan del Día", "Falda para Parrilla"]
        for clasico in clasicos:
            if len(nombres_resultado) >= limit:
                break
            if clasico.lower() not in nombres_procesados:
                nombres_resultado.append(clasico)
                nombres_procesados.add(clasico.lower())
                
        return nombres_resultado[:limit]

