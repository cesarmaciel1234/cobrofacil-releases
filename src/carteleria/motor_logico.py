import datetime
import random
import os
import json
import sqlite3
import traceback
from src.utils.paths import get_base_path

class MotorLogico:
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
                            partes = address.split()
                            if len(partes) > 1:
                                barrio = partes[0]
                                localidad = partes[1]
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
            
            plantilla = "¡Tenemos las mejores ofertas en carnes para vos!"
            if row:
                plantilla = row[0]
                
            # 5. Reemplazar etiquetas
            mensaje = plantilla.format(
                barrio=barrio,
                localidad=localidad,
                momento_dia=momento_dia,
                dia_semana=dia_semana
            )
            
            # 6. Seleccionar producto relacionado de inventario/destacados
            producto_sugerido = "Oferta"
            precio = 0
            poferta = 0
            
            if datos_destacados:
                # Seleccionamos un producto al azar de los destacados para acompañar el mensaje
                p = random.choice(datos_destacados)
                if len(p) >= 3:
                    producto_sugerido = p[0]
                    precio = p[1]
                    poferta = p[2]
            elif db:
                is_mariadb = getattr(db, "db_engine_type", "sqlite") == "mariadb"
                rand_func = "RAND()" if is_mariadb else "RANDOM()"
                res_random = db.execute_query(f"SELECT nombre, precio, precio_oferta FROM productos WHERE precio > 0 ORDER BY {rand_func} LIMIT 1")
                if res_random:
                    r = res_random[0]
                    if isinstance(r, dict):
                        producto_sugerido = r.get('nombre', '')
                        precio = float(r.get('precio', 0))
                        poferta = float(r.get('precio_oferta', 0))
                    else:
                        producto_sugerido = r[0]
                        precio = float(r[1] if r[1] else 0)
                        poferta = float(r[2] if len(r)>2 and r[2] else 0)

            return mensaje, producto_sugerido, precio, poferta
            
        except Exception as e:
            traceback.print_exc()
            return "¡Llevá la mejor calidad!", "Oferta", 0, 0
