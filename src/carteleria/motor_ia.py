import datetime
import random
import os
import json
from src.utils.paths import get_base_path

class MotorIA:
    """
    Cerebro de ventas que cruza datos meteorológicos, calendario y base de datos
    para generar impulsos de compra altamente persuasivos y contextualizados.
    """
    @staticmethod
    def generar_recomendacion(db, clima_tupla, datos_destacados):
        if not datos_destacados:
            return "¡Llevá la mejor calidad para tu familia!", "Oferta", 0, 0
            
        # 0. INTERCALADO HÍBRIDO CON lobo.db (Cerebro Persistente)
        import sqlite3
        try:
            db_path = os.path.join(get_base_path(), "lobo.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                clima_actual = clima_tupla[0] if clima_tupla else "sol"
                dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                dia_semana = dias[datetime.datetime.now().weekday()]
                
                dia_mes = datetime.datetime.now().day
                momento_mes = "fin_mes" if 20 <= dia_mes <= 30 else "inicio_mes"
                
                c.execute('''SELECT id, mensaje, producto 
                             FROM respuestas_ia 
                             WHERE clima = ? AND momento_mes = ?
                             ORDER BY veces_usado ASC, RANDOM() LIMIT 1''', (clima_actual, momento_mes))
                row = c.fetchone()
                if row and random.random() < 0.8: # 80% de probabilidad si hay datos
                    _id, mensaje_ia, producto_ia = row
                    mensaje_ia = f"¡Especial para este {dia_semana}! {mensaje_ia}"
                    c.execute('UPDATE respuestas_ia SET veces_usado = veces_usado + 1 WHERE id = ?', (_id,))
                    conn.commit()
                    conn.close()
                    
                    # Recuperar el precio actual y real del producto directamente del inventario (db principal)
                    precio, poferta = 0, 0
                    if db:
                        res = db.execute_query("SELECT precio, precio_oferta FROM productos WHERE nombre = ?", (producto_ia,))
                        if res:
                            if isinstance(res[0], dict):
                                precio = float(res[0].get('precio', 0))
                                poferta = float(res[0].get('precio_oferta', 0))
                            else:
                                precio = float(res[0][0] if res[0][0] else 0)
                                poferta = float(res[0][1] if len(res[0])>1 and res[0][1] else 0)
                                
                    if precio > 0:
                        return mensaje_ia, producto_ia, precio, poferta
                    else:
                        # Si el producto ya no existe o no tiene precio, buscar uno al azar
                        if db:
                            is_mariadb = getattr(db, "db_engine_type", "sqlite") == "mariadb"
                            rand_func = "RAND()" if is_mariadb else "RANDOM()"
                            res_random = db.execute_query(f"SELECT nombre, precio, precio_oferta FROM productos WHERE precio > 0 ORDER BY {rand_func} LIMIT 1")
                            if res_random:
                                r = res_random[0]
                                if isinstance(r, dict):
                                    n = r.get('nombre', '')
                                    p = float(r.get('precio', 0))
                                    po = float(r.get('precio_oferta', 0))
                                else:
                                    n = r[0]
                                    p = float(r[1] if r[1] else 0)
                                    po = float(r[2] if len(r)>2 and r[2] else 0)
                                return f"¡Aprovechá llevar {n} al mejor precio hoy!", n, p, po
                        
                        return "¡Llevá la mejor calidad!", "Oferta", 0, 0
                conn.close()
        except Exception as e:
            pass # Si falla, cae a la lógica local sin trabarse

        icon_name, clima_txt = clima_tupla
        hoy = datetime.datetime.now()
        dia_semana = hoy.weekday() # 0 = Lunes, 6 = Domingo
        dia_mes = hoy.day
        
        es_fin_de_semana = dia_semana in [4, 5, 6] # Vie, Sab, Dom
        es_fecha_cobro = 1 <= dia_mes <= 10
        es_fin_de_mes = 22 <= dia_mes <= 31
        
        # Categorizar el inventario por precio para recomendaciones inteligentes
        cortes_premium = [p for p in datos_destacados if p[1] > 8000]
        cortes_economicos = [p for p in datos_destacados if p[1] < 6500]
        
        if not cortes_premium: cortes_premium = datos_destacados
        if not cortes_economicos: cortes_economicos = datos_destacados

        # 1. ANALIZAR VENTAS REALES DEL DÍA (Si hay base de datos conectada)
        if db:
            try:
                # Buscamos el producto más vendido de HOY
                query = """
                    SELECT nombre_producto, SUM(cantidad) as total 
                    FROM detalles_ventas dv 
                    JOIN ventas v ON dv.id_venta = v.id 
                    WHERE date(v.fecha) = date('now') 
                    GROUP BY nombre_producto 
                    ORDER BY total DESC LIMIT 1
                """
                mas_vendido = db.execute_query(query)
                # 30% de probabilidad de usar el argumento de "Psicología de Masas"
                if mas_vendido and random.random() < 0.3:
                    nombre_top = mas_vendido[0][0]
                    # Buscar el precio de este producto
                    for p in datos_destacados:
                        if p[0] == nombre_top:
                            msg = f"🔥 ¡Récord de ventas! Hoy todos los vecinos de Pilar se están llevando {nombre_top}. ¡Llevate el tuyo antes que se agote el stock!"
                            poferta = p[2] if len(p) > 2 else 0
                            return msg, p[0], p[1], poferta
            except Exception as e:
                pass # Fallback silencioso si falla la query

        # 2. LÓGICA HEURÍSTICA Y CONTEXTUAL
        producto_elegido = random.choice(datos_destacados)
        mensaje = ""

        # Evaluamos el clima primero (tiene mucho peso emocional en la comida)
        if icon_name == "lluvia":
            producto_elegido = random.choice(cortes_economicos)
            mensaje = f"🌧️ Con esta lluvia en Pilar no da para salir. Ideal para quedarse cocinando en familia un buen tuco o guiso. Te recomiendo {producto_elegido[0]}."
        
        elif icon_name == "nube" and random.random() < 0.5:
            mensaje = f"☁️ El día está nublado pero tu parrilla puede brillar. Sorprendé a todos y llevate {producto_elegido[0]}."
            
        elif es_fin_de_semana and icon_name == "sol":
            producto_elegido = random.choice(cortes_premium)
            mensaje = f"☀️ ¡Tremendo finde de sol! No hay excusas, hoy hay que prender el fuego sí o sí. Date un lujo con nuestro {producto_elegido[0]}."
            
        # Si el clima no determinó nada fuerte, evaluamos el bolsillo (Calendario)
        elif es_fecha_cobro:
            producto_elegido = random.choice(cortes_premium)
            mensaje = f"💸 ¡Llegó el momento de darse el gusto del mes! Recién cobraste, así que te merecés la calidad premium de nuestro {producto_elegido[0]}."
            
        elif es_fin_de_mes:
            producto_elegido = random.choice(cortes_economicos)
            mensaje = f"📉 Cuidamos tu bolsillo en este fin de mes. Comer rico y de calidad no tiene que ser caro. Aprovechá este ofertón de {producto_elegido[0]}."
            
        # Argumentos de venta aleatorios generales
        else:
            mensajes_genericos = [
                f"👀 ¡Mirá este corte! El {producto_elegido[0]} tiene una terneza increíble hoy. Te aseguro que se corta con cuchara.",
                f"🥩 Si no sabés qué cocinar hoy, te resuelvo el problema: Llevate {producto_elegido[0]} que está espectacular.",
                f"🚨 ¡Oferta relámpago detectada! Aprovechá el precio que tenemos en {producto_elegido[0]}, no lo vas a conseguir más barato en la zona."
            ]
            mensaje = random.choice(mensajes_genericos)

        return mensaje, producto_elegido[0], producto_elegido[1], (producto_elegido[2] if len(producto_elegido)>2 else 0)

    @staticmethod
    def buscar_complementos(db, nombre_escaneado):
        if not db: return []
        is_mariadb = getattr(db, "db_engine_type", "sqlite") == "mariadb"
        rand_func = "RAND()" if is_mariadb else "RANDOM()"
        # Buscar 5 productos distintos para "sugerir"
        query = f"""
            SELECT nombre, precio 
            FROM productos 
            WHERE nombre != ? AND precio > 0 
            ORDER BY {rand_func} LIMIT 5
        """
        try:
            rows = db.execute_query(query, (nombre_escaneado,))
            return rows if rows else []
        except:
            return []

    @staticmethod
    def analizar_contexto_ticket(db, carrito_actual):
        """
        carrito_actual: list of dicts [{'producto': nombre, 'precio': precio}]
        Retorna: mensaje, producto_recomendado, precio_recomendado
        """
        if not carrito_actual or not db:
            return None, None, None
            
        nombres = [item.get('producto', '').lower() for item in carrito_actual]
        total_monto = sum(item.get('precio', 0.0) for item in carrito_actual)
        cantidad_items = len(carrito_actual)
        
        try:
            # 3. Cierre de Ticket (Último Minuto) - Si hay mucho volumen o monto
            if cantidad_items >= 4 or total_monto > 25000:
                if "carbón" not in " ".join(nombres) and "carbon" not in " ".join(nombres):
                    carbon = db.execute_query("SELECT nombre, precio FROM productos WHERE nombre LIKE '%carbón%' OR nombre LIKE '%carbon%' LIMIT 1")
                    if carbon:
                        return "¿Tenés todo listo? Que no falte el Carbón para el fuego", carbon[0]['nombre'], carbon[0]['precio']
                
                salsa = db.execute_query("SELECT nombre, precio FROM productos WHERE nombre LIKE '%salsa%' OR nombre LIKE '%mayonesa%' LIMIT 1")
                if salsa:
                    return "¡No te olvides del aderezo para acompañar!", salsa[0]['nombre'], salsa[0]['precio']
                        
            # 1. Venta Cruzada (Cross-selling)
            tiene_carne = any(kw in n for n in nombres for kw in ['asado', 'vacio', 'bife', 'carne', 'pollo', 'matambre'])
            tiene_acompanamiento = any(kw in n for n in nombres for kw in ['carbon', 'leña', 'salsa', 'vino', 'cerveza', 'pan', 'chorizo'])
            
            if tiene_carne and not tiene_acompanamiento:
                acompanamiento = db.execute_query("SELECT nombre, precio FROM productos WHERE nombre LIKE '%chorizo%' OR nombre LIKE '%vino%' LIMIT 1")
                if acompanamiento:
                    return "¿Sale Asado? Llevate la picada, Chorizo Puro Cerdo o un buen Vino", acompanamiento[0]['nombre'], acompanamiento[0]['precio']
                    
            is_mariadb = getattr(db, "db_engine_type", "sqlite") == "mariadb"
            rand_func = "RAND()" if is_mariadb else "RANDOM()"
            
            # 2. Incremento de Valor (Up-selling)
            tiene_generico = any(kw in n for n in nombres for kw in ['picada', 'molida', 'común', 'alita', 'oferta'])
            if tiene_generico:
                premium = db.execute_query(f"SELECT nombre, precio FROM productos WHERE precio > 6000 ORDER BY {rand_func} LIMIT 1")
                if premium:
                    return "¡Date un lujo! Probá nuestra línea de Cortes Premium de primera calidad", premium[0]['nombre'], premium[0]['precio']
                    
            # Si no aplica ninguna estrategia específica, recomendar algo aleatorio pero atractivo
            recomendacion = db.execute_query(f"SELECT nombre, precio FROM productos WHERE precio > 0 ORDER BY {rand_func} LIMIT 1")
            if recomendacion:
                return "¡Aprovechá la mejor calidad y precio del barrio!", recomendacion[0]['nombre'], recomendacion[0]['precio']
                
        except Exception as e:
            pass
            
        return None, None, None

    _cache_recomendaciones = {}

    @staticmethod
    def generar_recomendacion_dual(db, ahorro_total, carrito_actual=None, clima_pilar=None):
        """
        Genera una recomendación dual (Psicología Lobo Espía).
        Si hay ahorro, se basa en la ganancia. Si no, usa el contexto del ticket.
        Retorna: (mensaje, lista_gastador, lista_ahorrador)
        """
        if not db:
            return None, [], []
            
        is_mariadb = getattr(db, "db_engine_type", "sqlite") == "mariadb"
        rand_func = "RAND()" if is_mariadb else "RANDOM()"
        
        import hashlib
        import json
        import datetime
        
        # Determine climate info
        icon_name, txt = clima_pilar if clima_pilar else ("sol", "20°C")
        hora = datetime.datetime.now().hour
        try:
            t = int(txt.replace("°C", "").split()[0])
            if t < 18: temperatura_tipo = "frio"
            elif t > 25: temperatura_tipo = "calor"
            else: temperatura_tipo = "templado"
            temp_str = f"{t}°C"
        except:
            temperatura_tipo = "templado"
            temp_str = "20°C"

        if 5 <= hora < 13: momento_dia = "mañana"
        elif 13 <= hora < 19: momento_dia = "tarde"
        else: momento_dia = "noche"
        
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_semana = dias[datetime.datetime.now().weekday()]
        
        # Generar firma única del estado del carrito, ahorro, clima y hora para el cache
        estado = {"ahorro": ahorro_total, "carrito": carrito_actual or [], "clima": icon_name, "mom": momento_dia}
        firma = hashlib.md5(json.dumps(estado, sort_keys=True).encode()).hexdigest()
        
        if firma in MotorIA._cache_recomendaciones:
            return MotorIA._cache_recomendaciones[firma]
            
        try:
            # --- 1. MENSAJE PRINCIPAL HÍBRIDO (CHEF LOBO) ---
            mensaje = "¡Excelente elección! Llevate también esto:"
            if ahorro_total > 0:
                mensaje = "¡Ahorraste a lo grande! Elegí cómo aprovecharlo:"
            elif carrito_actual:
                msg_contexto, _, _ = MotorIA.analizar_contexto_ticket(db, carrito_actual)
                if msg_contexto:
                    mensaje = msg_contexto
                    
            # Intentar obtener una frase superadora desde lobo.db
            import sqlite3
            import os
            from src.utils.paths import get_base_path
            
            try:
                db_path = os.path.join(get_base_path(), "lobo.db")
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    c = conn.cursor()
                    
                    dia_mes = datetime.datetime.now().day
                    momento_mes = "fin_mes" if 20 <= dia_mes <= 30 else "inicio_mes"
                    
                    # Buscamos primero con match perfecto de clima y hora
                    c.execute('''SELECT id, mensaje FROM respuestas_ia 
                                 WHERE momento_mes = ? AND momento_dia = ? AND temperatura_tipo = ?
                                 ORDER BY veces_usado ASC, RANDOM() LIMIT 1''', (momento_mes, momento_dia, temperatura_tipo))
                    row = c.fetchone()
                    if not row:
                        # Fallback a match parcial
                        c.execute('''SELECT id, mensaje FROM respuestas_ia 
                                     WHERE momento_mes = ? 
                                     ORDER BY veces_usado ASC, RANDOM() LIMIT 1''', (momento_mes,))
                        row = c.fetchone()
                        
                    if row:
                        _id, msg_db = row
                        mensaje = msg_db.format(
                            dia_semana=dia_semana, 
                            estado_clima=icon_name, 
                            momento_dia=momento_dia, 
                            temperatura=temp_str
                        )
                        c.execute('UPDATE respuestas_ia SET veces_usado = veces_usado + 1 WHERE id = ?', (_id,))
                        conn.commit()
                    conn.close()
            except Exception as e:
                import traceback
                print(f"[ESPIA_DEBUG] Error db lobo: {e} - {traceback.format_exc()}")
                pass # Si falla, usamos el mensaje por defecto
                    
            # --- 2. PERFIL GASTADOR (Complementos / Upselling) ---
            if ahorro_total > 0:
                limite_inferior = ahorro_total * 0.3
                limite_superior = ahorro_total * 2.5
            else:
                limite_inferior = 0
                limite_superior = 999999

            
            query_g = f"""
                SELECT nombre, precio, precio_oferta 
                FROM productos 
                WHERE precio >= ? AND precio <= ? AND precio > 0
                AND (nombre LIKE '%carbón%' OR nombre LIKE '%carbon%' OR nombre LIKE '%salsa%' OR nombre LIKE '%chorizo%')
                ORDER BY {rand_func} LIMIT 3
            """
            res_g = db.execute_query(query_g, (limite_inferior, limite_superior))
            lista_gastador = []
            
            def extraer_datos(r):
                n = r.get('nombre', '') if isinstance(r, dict) else r[0]
                p = float(r.get('precio', 0)) if isinstance(r, dict) else float(r[1] or 0)
                po = float(r.get('precio_oferta', 0)) if isinstance(r, dict) else float(r[2] if len(r)>2 and r[2] else 0)
                return {'nombre': n, 'precio': p, 'precio_oferta': po}
                
            if res_g:
                for r in res_g: lista_gastador.append(extraer_datos(r))
                
            faltan_g = 3 - len(lista_gastador)
            if faltan_g > 0:
                nombres_g = [p['nombre'] for p in lista_gastador]
                if nombres_g:
                    placeholders = ','.join(['?']*len(nombres_g))
                    query_fill_g = f"SELECT nombre, precio, precio_oferta FROM productos WHERE precio >= ? AND precio <= ? AND precio > 0 AND nombre NOT IN ({placeholders}) ORDER BY {rand_func} LIMIT ?"
                    params_g = (limite_inferior, limite_superior) + tuple(nombres_g) + (faltan_g,)
                else:
                    query_fill_g = f"SELECT nombre, precio, precio_oferta FROM productos WHERE precio >= ? AND precio <= ? AND precio > 0 ORDER BY {rand_func} LIMIT ?"
                    params_g = (limite_inferior, limite_superior, faltan_g)
                    
                res_fill_g = db.execute_query(query_fill_g, params_g)
                if res_fill_g:
                    for r in res_fill_g: lista_gastador.append(extraer_datos(r))

            # --- 2. PERFIL AHORRADOR (Acumular Descuento) ---
            # Buscar 3 cortes en oferta
            query_a = f"""
                SELECT nombre, precio, precio_oferta 
                FROM productos 
                WHERE precio_oferta > 0 AND precio_oferta < precio AND precio > 0
                ORDER BY {rand_func} LIMIT 3
            """
            res_a = db.execute_query(query_a)
            lista_ahorrador = []
            if res_a:
                for r in res_a: lista_ahorrador.append(extraer_datos(r))
                
            faltan_a = 3 - len(lista_ahorrador)
            if faltan_a > 0:
                nombres_a = [p['nombre'] for p in lista_ahorrador]
                if nombres_a:
                    placeholders = ','.join(['?']*len(nombres_a))
                    query_fill_a = f"SELECT nombre, precio, precio_oferta FROM productos WHERE precio > 0 AND nombre NOT IN ({placeholders}) ORDER BY {rand_func} LIMIT ?"
                    params_a = tuple(nombres_a) + (faltan_a,)
                else:
                    query_fill_a = f"SELECT nombre, precio, precio_oferta FROM productos WHERE precio > 0 ORDER BY {rand_func} LIMIT ?"
                    params_a = (faltan_a,)
                res_fill_a = db.execute_query(query_fill_a, params_a)
                if res_fill_a:
                    for r in res_fill_a: lista_ahorrador.append(extraer_datos(r))

            resultado = (mensaje, lista_gastador, lista_ahorrador)
            
            # Limitar la caché a los últimos 50 tickets para no consumir memoria infinita
            if len(MotorIA._cache_recomendaciones) > 50:
                # Borrar el más viejo (en Python 3.7+ los dicts mantienen el orden de inserción)
                viejo_key = next(iter(MotorIA._cache_recomendaciones))
                del MotorIA._cache_recomendaciones[viejo_key]
                
            MotorIA._cache_recomendaciones[firma] = resultado
            return resultado
                
        except Exception as e:
            import logging
            logging.getLogger("MotorIA").error(f"Error generando recomendación dual: {e}")
            pass
            
        return None, [], []

