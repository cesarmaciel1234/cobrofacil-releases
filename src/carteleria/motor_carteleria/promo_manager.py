import random
import time
from src.carteleria.ia_chef_lobo.motor_ia import MotorIA

class PromoManager:
    def __init__(self, main_window):
        self.main = main_window
        self.top_current_mode = 0 # 0=Hoy, 1=Semana, 2=Mes

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
                regla = ""
                if cant_of > 0:
                    t_un = str(r.get('tipo_unidad_oferta', '')).strip().lower()
                    if 'unidad' in t_un or t_un == 'u':
                        t_un = "Unidades"
                    else:
                        t_un = "Kilos"
                    regla = f"<span style='color: #00A859;'>Llevando</span> <span style='color: #DC2626;'>{cant_of:g} {t_un}</span>"
            else:
                cat = str(r[0])
                nombre = str(r[1])
                precio = float(r[2]) if len(r) > 2 else 0.0
                ofertas = [float(r[i] if len(r)>i and r[i] else 0) for i in (3, 4, 5)]
                validas = [x for x in ofertas if x > 0]
                precio_oferta = min(validas) if validas else 0.0
                
                cant_of = float(r[6]) if len(r) > 6 else 0.0
                regla = ""
                if cant_of > 0:
                    t_un = str(r[7]).strip().lower() if len(r) > 7 and r[7] else ''
                    if 'unidad' in t_un or t_un == 'u':
                        t_un = "Unidades"
                    else:
                        t_un = "Kilos"
                    regla = f"<span style='color: #00A859;'>Llevando</span> <span style='color: #DC2626;'>{cant_of:g} {t_un}</span>"

            if cat not in agrupados: agrupados[cat] = []
            agrupados[cat].append((nombre, precio, precio_oferta, regla))
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
            if not isinstance(top_list, list): return parsed
            for r in top_list:
                if isinstance(r, dict):
                    ofertas = [float(r.get(k) or 0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
                    validas = [x for x in ofertas if x > 0]
                    p_of = min(validas) if validas else 0.0
                    
                    nombre = r.get('nombre', '')
                    cant_of = float(r.get('cant_oferta') or 0)
                    t_un = str(r.get('tipo_unidad_oferta', '')).strip().lower()
                    if cant_of > 0:
                        if 'unidad' in t_un or t_un == 'u':
                            t_un = "Unidades"
                        else:
                            t_un = "Kilos"
                        pass  # Deleted: nombre = f"{nombre} [Llevando {cant_of:g} {t_un.capitalize()}]"
                    else:
                        if 'unidad' in t_un or t_un == 'u': t_un = "Unidades"
                        else: t_un = "Kilos"
                    
                    stock_real = float(r.get('stock') or 0.0)
                    parsed.append((nombre, float(r.get('precio', 0)), p_of, stock_real, t_un))
                else:
                    ofertas = [float(r[i] if len(r)>i and r[i] else 0) for i in (2, 3, 4)]
                    validas = [x for x in ofertas if x > 0]
                    p_of = min(validas) if validas else 0.0
                    
                    nombre = str(r[0])
                    cant_of = float(r[5]) if len(r) > 5 else 0.0
                    t_un = str(r[6]).strip().lower() if len(r) > 6 and r[6] else ''
                    if cant_of > 0:
                        if 'unidad' in t_un or t_un == 'u':
                            t_un = "Unidades"
                        else:
                            t_un = "Kilos"
                        pass  # Deleted: nombre = f"{nombre} [Llevando {cant_of:g} {t_un.capitalize()}]"
                    else:
                        if 'unidad' in t_un or t_un == 'u': t_un = "Unidades"
                        else: t_un = "Kilos"
                        
                    stock_real = float(r[7]) if len(r) > 7 and r[7] else 0.0
                    parsed.append((nombre, float(r[1]) if len(r)>1 else 0.0, p_of, stock_real, t_un))
            return parsed

        # Seleccionar lista según el modo actual (0=Hoy, 1=Semana, 2=Mes)
        modos = ["hoy", "semana", "mes"]
        titulos = ["LO MÁS VENDIDO - HOY", "TOP DE LA SEMANA", "TOP DEL MES"]
        
        modo_str = modos[self.top_current_mode]
        titulo_str = titulos[self.top_current_mode]
        
        # --- NUEVO MOTOR CENTRAL DE VENTAS ---
        from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
        top_real = motor_ventas.get_top_ventas(limit=5, periodo=modo_str)
        
        # Mapear formato del motor al esperado por cartelería
        prod_lista = []
        for p in top_real:
            nombre = p['nombre']
            precio = 0.0
            precio_of = 0.0
            
            # Buscar el precio en el estado de la cartelería (grilla)
            if hasattr(self.main, 'datos_grilla_completa'):
                for cat, prods in self.main.datos_grilla_completa.items():
                    for pp in prods:
                        if pp[0].lower() == nombre.lower():
                            precio = pp[1]
                            precio_of = pp[2]
                            break
            
            prod_lista.append((nombre, precio, precio_of, p['cantidad'], "Unidades"))
        
        if prod_lista:
            self.main.zona1_carrusel.actualizar_top10(prod_lista, titulo=titulo_str)
            
            # Rotar modo para la próxima vuelta
            self.top_current_mode = (self.top_current_mode + 1) % 3

        # Extraer para Combos y Recomendación
        if prod_lista:
            self.main.img_index = (self.main.img_index + 1) % len(prod_lista)
            prod_actual = prod_lista[self.main.img_index]
            
            poferta = prod_actual[2] if len(prod_actual) > 2 else 0
            stock = prod_actual[3] if len(prod_actual) > 3 else 0
            unidad = prod_actual[4] if len(prod_actual) > 4 else "Kilos"
            
            # (El carrusel ya se actualizó completo arriba)
            
            if len(prod_lista) > 1:
                prod_siguiente = prod_lista[(self.main.img_index + 1) % len(prod_lista)]
                poferta_s = prod_siguiente[2] if len(prod_siguiente) > 2 else 0
                stock_s = prod_siguiente[3] if len(prod_siguiente) > 3 else 0
                unidad_s = prod_siguiente[4] if len(prod_siguiente) > 4 else "Kilos"
                
                if random.choice([True, False]):
                    self.main.zona3_extra1.actualizar_destacada(prod_siguiente[0], prod_siguiente[1], poferta_s, stock=stock_s, unidad=unidad_s)
                else:
                    nombres = [p[0] for p in random.sample(prod_lista, min(3, len(prod_lista)))]
                    centro_compra_simulado = random.choice([prod_siguiente[0], prod_actual[0]])
                    self.main.zona3_extra1.actualizar_combo(centro_compra_simulado, nombres)
                
                prod_tercero = prod_lista[(self.main.img_index + 2) % len(prod_lista)]
                poferta_t = prod_tercero[2] if len(prod_tercero) > 2 else 0
                stock_t = prod_tercero[3] if len(prod_tercero) > 3 else 0
                unidad_t = prod_tercero[4] if len(prod_tercero) > 4 else "Kilos"
                
                if random.choice([True, False]):
                    self.main.timer.setInterval(self.main.rotacion_ms if hasattr(self.main, 'rotacion_ms') else 16000)
                    self.main.zona4_extra2.actualizar_recomendacion(prod_tercero[0], prod_tercero[1], poferta_t, stock=stock_t, unidad=unidad_t)
                else:
                    self.main.timer.setInterval((self.main.rotacion_ms if hasattr(self.main, 'rotacion_ms') else 16000) + 12000)
                    msg, prod, precio, precio_oferta = MotorIA.generar_recomendacion(
                        None, 
                        self.main.clima_pilar, 
                        prod_lista
                    )
                    self.main.zona4_extra2.actualizar_ia(msg, prod, precio, precio_oferta, self.main.clima_pilar)
                    
            # Rotación en Vista 3: Alternar entre Combos y Recomendación en el 3er espacio
            if hasattr(self.main, 'layout_mode') and self.main.layout_mode == 3:
                self.main.grid.removeWidget(self.main.zona3_extra1)
                self.main.grid.removeWidget(self.main.zona4_extra2)
                
                # Alternamos dependiendo si es par o impar
                if self.main.img_index % 2 == 0:
                    self.main.zona4_extra2.hide()
                    self.main.grid.addWidget(self.main.zona3_extra1, 0, 2)
                    self.main.zona3_extra1.show()
                else:
                    self.main.zona3_extra1.hide()
                    self.main.grid.addWidget(self.main.zona4_extra2, 0, 2)
                    self.main.zona4_extra2.show()
