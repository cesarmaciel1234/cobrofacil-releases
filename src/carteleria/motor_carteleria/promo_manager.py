import random
import time
from src.carteleria.ia_chef_lobo.motor_ia import MotorIA

class PromoManager:
    def __init__(self, main_window):
        self.main = main_window

    def agrupar(self, rows):
        agrupados = {}
        for r in rows:
            if isinstance(r, dict):
                cat = r.get('categoria', 'OTROS')
                nombre = r.get('nombre', '')
                precio = float(r.get('precio', 0.0))
                ofertas = [float(r.get(k) or 0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
                validas = [x for x in ofertas if x > 0]
                precio_oferta = min(validas) if validas else 0.0
                
                cant_of = float(r.get('cant_oferta') or 0)
                if cant_of > 0:
                    nombre = f"{nombre} [Llevando {int(cant_of)} {r.get('tipo_unidad_oferta', 'un')}]"
            else:
                cat = str(r[0])
                nombre = str(r[1])
                precio = float(r[2]) if len(r) > 2 else 0.0
                ofertas = [float(r[i] if len(r)>i and r[i] else 0) for i in (3, 4, 5)]
                validas = [x for x in ofertas if x > 0]
                precio_oferta = min(validas) if validas else 0.0
                
                cant_of = float(r[6]) if len(r) > 6 else 0.0
                if cant_of > 0:
                    tipo_un = str(r[7]) if len(r) > 7 else 'un'
                    nombre = f"{nombre} [Llevando {int(cant_of)} {tipo_un}]"

            if cat not in agrupados: agrupados[cat] = []
            agrupados[cat].append((nombre, precio, precio_oferta))
        return agrupados

    def actualizar_pantallas_promocionales(self):
        inactividad = time.time() - getattr(self.main, 'ultimo_cambio_ia', 0)
        
        # --- Lógica de Protector de Pantalla ---
        if getattr(self.main, 'hay_oferta_sos', False) and inactividad > 600:
            if self.main.stack.currentIndex() != 1:
                try:
                    import os, datetime
                    from src.utils.paths import get_base_path
                    log_p = os.path.join(get_base_path(), "logs", "espia_debug.log")
                    with open(log_p, "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [ESPIA_DEBUG] 10 minutos inactividad. Protector.\n")
                except: pass
                self.main.layout_manager.fade_to_index(1)
                self.main.timer.setInterval(10000) 
            return 
            
        if self.main.stack.currentIndex() == 1 and inactividad <= 600:
            self.main.layout_manager.fade_to_index(0)
            self.main.timer.setInterval(getattr(self.main, 'rotacion_ms', 16000))

        if self.main.stack.currentIndex() not in (0, 1):
            self.main.layout_manager.fade_to_index(0)
            
        if not self.main.datos_destacados: return
        
        def parse_top(top_list):
            parsed = []
            for r in top_list:
                if isinstance(r, dict):
                    ofertas = [float(r.get(k) or 0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
                    validas = [x for x in ofertas if x > 0]
                    p_of = min(validas) if validas else 0.0
                    
                    nombre = r.get('nombre', '')
                    cant_of = float(r.get('cant_oferta') or 0)
                    if cant_of > 0:
                        nombre = f"{nombre} [Llevando {int(cant_of)} {r.get('tipo_unidad_oferta', 'un')}]"
                        
                    parsed.append((nombre, float(r.get('precio', 0)), p_of))
                else:
                    ofertas = [float(r[i] if len(r)>i and r[i] else 0) for i in (2, 3, 4)]
                    validas = [x for x in ofertas if x > 0]
                    p_of = min(validas) if validas else 0.0
                    
                    nombre = str(r[0])
                    cant_of = float(r[5]) if len(r) > 5 else 0.0
                    if cant_of > 0:
                        tipo_un = str(r[6]) if len(r) > 6 else 'un'
                        nombre = f"{nombre} [Llevando {int(cant_of)} {tipo_un}]"
                        
                    parsed.append((nombre, float(r[1] if r[1] else 0), p_of))
            return parsed

        datos_parsed = parse_top(self.main.datos_destacados)
        self.main.img_index = (self.main.img_index + 1) % len(datos_parsed)
        prod_actual = datos_parsed[self.main.img_index]
        
        choice = random.randint(1, 4)
        if choice == 1:
            poferta = prod_actual[2] if len(prod_actual) > 2 else 0
            self.main.zona1_carrusel.actualizar_especial(prod_actual[0], prod_actual[1], poferta)
        elif choice == 2 and hasattr(self.main, 'top10_hoy') and self.main.top10_hoy:
            self.main.zona1_carrusel.actualizar_top10(parse_top(self.main.top10_hoy), "🔥 Top Ventas Hoy 🔥")
        elif choice == 3 and hasattr(self.main, 'top10_semanal') and self.main.top10_semanal:
            self.main.zona1_carrusel.actualizar_top10(parse_top(self.main.top10_semanal), "🔥 Top Ventas Semana 🔥")
        elif hasattr(self.main, 'top10_mensual') and self.main.top10_mensual:
            self.main.zona1_carrusel.actualizar_top10(parse_top(self.main.top10_mensual), "🔥 Top Ventas del Mes 🔥")
        else:
            poferta = prod_actual[2] if len(prod_actual) > 2 else 0
            self.main.zona1_carrusel.actualizar_especial(prod_actual[0], prod_actual[1], poferta)
            
        if len(datos_parsed) > 1:
            prod_siguiente = datos_parsed[(self.main.img_index + 1) % len(datos_parsed)]
            
            if random.choice([True, False]):
                poferta_dest = prod_siguiente[2] if len(prod_siguiente) > 2 else 0
                self.main.zona3_extra1.actualizar_destacada(prod_siguiente[0], prod_siguiente[1], poferta_dest)
            else:
                nombres = []
                if len(datos_parsed) >= 2:
                    nombres = [p[0] for p in random.sample(datos_parsed, min(3, len(datos_parsed)))]
                        
                if nombres:
                    centro_compra_simulado = random.choice([prod_siguiente[0], prod_actual[0]])
                    self.main.zona3_extra1.actualizar_combo(centro_compra_simulado, nombres)
                else:
                    poferta_dest = prod_siguiente[2] if len(prod_siguiente) > 2 else 0
                    self.main.zona3_extra1.actualizar_destacada(prod_siguiente[0], prod_siguiente[1], poferta_dest)
            
            prod_tercero = datos_parsed[(self.main.img_index + 2) % len(datos_parsed)]
            
            if random.choice([True, False]):
                self.main.timer.setInterval(self.main.rotacion_ms if hasattr(self.main, 'rotacion_ms') else 16000)
                poferta = prod_tercero[2] if len(prod_tercero) > 2 else 0
                self.main.zona4_extra2.actualizar_recomendacion(prod_tercero[0], prod_tercero[1], poferta)
            else:
                self.main.timer.setInterval((self.main.rotacion_ms if hasattr(self.main, 'rotacion_ms') else 16000) + 12000)
                msg, prod, precio, precio_oferta = MotorIA.generar_recomendacion(
                    None, 
                    self.main.clima_pilar, 
                    datos_parsed
                )
                self.main.zona4_extra2.actualizar_ia(msg, prod, precio, precio_oferta, self.main.clima_pilar)
