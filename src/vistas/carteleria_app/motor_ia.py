import datetime
import random

class MotorIA:
    """
    Cerebro de ventas que cruza datos meteorológicos, calendario y base de datos
    para generar impulsos de compra altamente persuasivos y contextualizados.
    """
    @staticmethod
    def generar_recomendacion(db, clima_tupla, datos_destacados):
        if not datos_destacados:
            return "¡Llevá la mejor calidad para tu familia!", "Oferta", 0
            
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
                mas_vendido = db.execute(query)
                # 30% de probabilidad de usar el argumento de "Psicología de Masas"
                if mas_vendido and random.random() < 0.3:
                    nombre_top = mas_vendido[0][0]
                    # Buscar el precio de este producto
                    for p in datos_destacados:
                        if p[0] == nombre_top:
                            msg = f"🔥 ¡Récord de ventas! Hoy todos los vecinos de Pilar se están llevando {nombre_top}. ¡Llevate el tuyo antes que se agote el stock!"
                            return msg, p[0], p[1]
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

        return mensaje, producto_elegido[0], producto_elegido[1]
