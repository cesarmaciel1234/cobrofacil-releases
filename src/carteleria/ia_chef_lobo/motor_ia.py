import datetime
import random
import os
import json
import sqlite3
import traceback
from src.utils.paths import get_base_path

class MotorIA:
    """
    Motor Lógico 100% Offline para la Cartelería Digital.
    Genera recomendaciones determinísticas basadas en la hora, día, clima y ubicación.
    """
    @staticmethod
    def generar_recomendacion(db, clima_tupla, datos_destacados):
        try:
            # 1. Analizar contexto de tiempo
            hoy = datetime.datetime.now()
            hora = hoy.hour
            dia_idx = hoy.weekday() # 0 = Lunes, 6 = Domingo
            
            dias_str = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            dia_semana = dias_str[dia_idx]
            
            if 6 <= hora < 12:
                momento_dia = "mañana"
            elif 12 <= hora < 20:
                momento_dia = "tarde"
            else:
                momento_dia = "noche"
                
            filtro_tipo_dia = "finde" if dia_idx >= 4 else "semana" # Viernes a Domingo = finde
            
            # Reglas de fechas especiales
            dia_mes = hoy.day
            mes_actual = hoy.month
            
            es_dia_noquis = dia_mes in [28, 29]
            es_dia_locro = mes_actual == 5 and dia_mes in [1, 24, 25]
            
            # 2. Analizar contexto de clima (recibe tuple como ("sol", "22°C Pilar") o ("nube", ...) o ("lluvia", ...))
            icono_clima = clima_tupla[0].lower() if clima_tupla else "sol"
            if "lluvia" in icono_clima:
                filtro_clima = "lluvioso"
            elif "sol" in icono_clima:
                # Determinar si hace calor o frío según la temp si es posible
                temp_str = clima_tupla[1] if len(clima_tupla) > 1 else "22"
                import re
                nums = re.findall(r'\d+', temp_str)
                temp = int(nums[0]) if nums else 22
                if temp > 25:
                    filtro_clima = "calor"
                elif temp < 15:
                    filtro_clima = "frio"
                else:
                    filtro_clima = "indiferente"
            else:
                filtro_clima = "indiferente"

            # 3. Leer variables geográficas de config.json
            barrio = "Centro"
            localidad = "tu ciudad"
            try:
                config_path = os.path.join(get_base_path(), "config.json")
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        address = cfg.get("address", "")
                        if address:
                            # Heurística simple si no hay barrio explícito
                            import re
                            partes = [p for p in re.split(r'[, ]+', address) if not p.isdigit() and len(p)>2]
                            if len(partes) >= 1:
                                barrio = partes[0].capitalize()
                                localidad = partes[1].capitalize() if len(partes) > 1 else barrio
                            else:
                                barrio = address
            except Exception:
                pass

            # 4. Consultar SQLite lobo.db
            db_path = os.path.join(get_base_path(), "lobo.db")
            if not os.path.exists(db_path):
                return "¡Tenemos las mejores ofertas en carnes para vos!", "Oferta", 0, 0

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # Consulta flexible: busca el clima exacto o indiferente, momento exacto o indiferente, etc.
            query = """
            SELECT texto_plantilla FROM plantillas_carteleria 
            WHERE (filtro_clima = ? OR filtro_clima = 'indiferente')
              AND (filtro_momento = ? OR filtro_momento = 'indiferente')
              AND (filtro_tipo_dia = ? OR filtro_tipo_dia = 'indiferente')
            ORDER BY RANDOM() LIMIT 1
            """
            
            c.execute(query, (filtro_clima, momento_dia, filtro_tipo_dia))
            row = c.fetchone()
            conn.close()
            
            # Fallback determinístico con venta cruzada
            plantilla = "¡Tenemos las mejores ofertas en carnes para vos!"
            if es_dia_noquis:
                plantilla = "¡Se acercan los 29! Llevate la mejor carne picada o falda para el estofado de {momento_dia} en {barrio}."
            elif es_dia_locro:
                plantilla = "¡Celebremos en {localidad}! Tenemos pechito de cerdo, patitas y chorizo colorado para el mejor Locro patrio."
            elif dia_idx >= 4:
                plantilla = "¡Salió Asado este {dia_semana}! Llevate nuestros cortes premium y no te olvides del carbón y los chinchulines."
            elif row:
                plantilla = row[0]
                
            # 5. Reemplazar etiquetas con safe mapping
            class SafeDict(dict):
                def __missing__(self, key):
                    return '{' + key + '}'
                    
            mensaje = plantilla.format_map(SafeDict(
                barrio=barrio,
                localidad=localidad,
                momento_dia=momento_dia,
                dia_semana=dia_semana
            ))
            
            # 6. Seleccionar producto relacionado de inventario/destacados
            producto_sugerido = "Oferta"
            precio = 0
            poferta = 0
            
            if datos_destacados:
                # Seleccionamos un producto al azar de los destacados para acompañar el mensaje
                p = None
                if isinstance(datos_destacados, dict):
                    productos = []
                    for cat, items in datos_destacados.items():
                        if isinstance(items, list):
                            productos.extend(items)
                    if productos: p = random.choice(productos)
                else:
                    p = random.choice(datos_destacados)
                    
                if p and len(p) >= 3:
                    producto_sugerido = p[0]
                    precio = p[1]
                    poferta = p[2]
            elif db:
                res_random = db.execute_query(
                    "SELECT nombre, precio, precio_oferta FROM productos WHERE precio > 0 ORDER BY nombre LIMIT 50"
                )
                if res_random:
                    r = random.choice(list(res_random))
                    if isinstance(r, dict):
                        producto_sugerido = r.get('nombre', '')
                        precio = float(r.get('precio', 0))
                        poferta = float(r.get('precio_oferta', 0))
                    else:
                        producto_sugerido = r[0]
                        precio = float(r[1] if r[1] else 0)
                        poferta = float(r[2] if len(r)>2 and r[2] else 0)

            producto_sugerido = str(producto_sugerido).replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
            if not producto_sugerido or producto_sugerido.upper() in {"ARTICULO COMUN", "ARTÍCULO COMÚN", "ARTICULO LIBRE", "VENTA LIBRE", "COBRO RAPIDO", "VARIOS", "AJUSTE", "DIFERENCIA"}:
                producto_sugerido = "Asado Especial"

            return mensaje, producto_sugerido, precio, poferta
            
        except Exception as e:
            traceback.print_exc()
            return "¡Llevá la mejor calidad!", "Oferta", 0, 0
