import json
import random
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from src.logger import logger
from src.base_de_datos.database import db_manager
from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
from src.cerebro_global.carteleria_cerebro.motor_ia_local import MotorIALocal

class MotorCarrusel(QThread):
    datos_listos = pyqtSignal(list, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.modo_actual = 0 # 0=Hoy, 1=Semana, 2=Mes
        
    def run(self):
        try:
            modos = ["hoy", "semana", "mes"]
            titulos = ["LOS MÁS ELEGIDOS HOY", "CON MÁS VOLUMEN HOY", "RECOMENDADO HOY"]
            
            prod_lista = []
            titulo_str = ""
            
            # Intentar encontrar un modo que tenga datos (hasta 3 intentos)
            for _ in range(3):
                modo_str = modos[self.modo_actual]
                titulo_str = titulos[self.modo_actual]
                
                # Si es hoy, usamos frecuencia (tickets). Si es semana, usamos volumen (kilos).
                # Si es mes (Recomendados), usamos "clavos" (los menos vendidos para empujarlos).
                if modo_str == "hoy":
                    modo_metrica = "frecuencia"
                elif modo_str == "mes":
                    modo_metrica = "clavos"
                else:
                    modo_metrica = "volumen"
                
                top_real = motor_ventas.get_top_ventas(limit=10, periodo=modo_str, modo=modo_metrica)
                
                for p in top_real:
                    nombre = p['nombre']
                    q = "SELECT precio_normal, precio_oferta, regla_texto FROM carteleria_global WHERE LOWER(nombre_producto) = LOWER(?)"
                    rows = db_manager.execute_query(q, (nombre,))
                    if rows:
                        row0 = rows[0]
                        if isinstance(row0, dict):
                            precio = float(row0.get('precio_normal') or 0)
                            precio_of = float(row0.get('precio_oferta') or 0)
                            regla = str(row0.get('regla_texto') or "")
                        else:
                            precio = float(row0[0] or 0)
                            precio_of = float(row0[1] or 0)
                            regla = str(row0[2] or "")
                        
                        if regla: unidad = "Kilos" if "Kilos" in regla else "Unidades"
                        else: unidad = "Unidades"
                        
                        stock_rows = db_manager.execute_query("SELECT stock, unidad FROM productos WHERE LOWER(nombre) = LOWER(?)", (nombre,))
                        real_stock = 0.0
                        if stock_rows:
                            if isinstance(stock_rows[0], dict):
                                real_stock = float(stock_rows[0].get('stock') or 0)
                                if stock_rows[0].get('unidad'): unidad = str(stock_rows[0].get('unidad'))
                            else:
                                real_stock = float(stock_rows[0][0] or 0)
                                if stock_rows[0][1]: unidad = str(stock_rows[0][1])
                        
                        cantidad_vendida = float(p.get('cantidad', 0))
                        prod_lista.append((nombre, precio, precio_of, real_stock, unidad, cantidad_vendida))
                
                self.modo_actual = (self.modo_actual + 1) % 3
                if prod_lista:
                    break # Encontramos datos, salimos del bucle
            
            # Fallback si no hay ventas en ningun periodo (ej. base de datos nueva)
            if not prod_lista:
                q_fall = "SELECT nombre_producto, precio_normal, precio_oferta, regla_texto FROM carteleria_global ORDER BY precio_oferta DESC LIMIT 5"
                rows_fall = db_manager.execute_query(q_fall)
                for row in rows_fall:
                    if isinstance(row, dict):
                        nombre = row.get('nombre_producto')
                        precio = float(row.get('precio_normal') or 0)
                        precio_of = float(row.get('precio_oferta') or 0)
                        regla = str(row.get('regla_texto') or "")
                    else:
                        nombre = row[0]
                        precio = float(row[1] or 0)
                        precio_of = float(row[2] or 0)
                        regla = str(row[3] or "")
                        
                    unidad = "Kilos" if "Kilos" in regla else "Unidades"
                    prod_lista.append((nombre, precio, precio_of, 99, unidad, 0))
                titulo_str = "PRODUCTOS DESTACADOS"

            if prod_lista:
                self.datos_listos.emit(prod_lista, titulo_str)
        except Exception as e:
            logger.error(f"MotorCarrusel Error: {e}")
            self.datos_listos.emit([], "")

class MotorCombos(QThread):
    combo_listo = pyqtSignal(str, list)
    destacada_lista = pyqtSignal(str, float, float, float, str, str, float, float)  # nombre, precio, precio_of, stock, unidad, regla_texto, vistas, unidades_vendidas
    promo_lista = pyqtSignal(str, float, list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def run(self):
        try:
            import random
            import json
            
            eleccion = random.choice([0, 1, 2])
            
            # Buscar productos en oferta aleatorios desde carteleria_global
            q = "SELECT nombre_producto, precio_normal, precio_oferta, regla_texto FROM carteleria_global WHERE precio_oferta > 0 ORDER BY RANDOM() LIMIT 5"
            if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb":
                q = q.replace("RANDOM()", "RAND()")
            rows = db_manager.execute_query(q)
            
            if eleccion == 2:
                # Intentar cargar una Promo Manual (Combo real)
                try:
                    q_promo = "SELECT nombre, precio_combo, productos_json FROM combos ORDER BY RANDOM() LIMIT 1"
                    if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb":
                        q_promo = q_promo.replace("RANDOM()", "RAND()")
                    promo_rows = db_manager.execute_query(q_promo)
                    
                    if promo_rows:
                        pr = promo_rows[0]
                        if isinstance(pr, dict):
                            p_nombre = str(pr.get('nombre', ''))
                            p_precio = float(pr.get('precio_combo') or 0)
                            p_json = str(pr.get('productos_json', '[]'))
                        else:
                            p_nombre = str(pr[0])
                            p_precio = float(pr[1] or 0)
                            p_json = str(pr[2] or '[]')
                            
                        p_list = json.loads(p_json)
                        if p_list:
                            self.promo_lista.emit(p_nombre, p_precio, p_list)
                            return
                except:
                    pass
                # Si falla, no existe la tabla o no hay promos válidas, cae a opcion 0 o 1
                eleccion = random.choice([0, 1])

            if not rows: return
            
            if eleccion == 0:
                # Emitir Destacada
                r = rows[0]
                if isinstance(r, dict):
                    nombre = str(r.get('nombre_producto', ''))
                    regla_raw = str(r.get('regla_texto') or "")
                    unidad = "Kilos" if "Kilos" in regla_raw else "Unidades"
                    precio = float(r.get('precio_normal') or 0)
                    precio_of = float(r.get('precio_oferta') or 0)
                else:
                    nombre = str(r[0])
                    regla_raw = str(r[3] or "")
                    unidad = "Kilos" if "Kilos" in regla_raw else "Unidades"
                    precio = float(r[1])
                    precio_of = float(r[2])
                    
                stock_rows = db_manager.execute_query("SELECT stock, unidad FROM productos WHERE LOWER(nombre) = LOWER(?)", (nombre,))
                real_stock = 0.0
                if stock_rows:
                    if isinstance(stock_rows[0], dict):
                        real_stock = float(stock_rows[0].get('stock') or 0)
                        if stock_rows[0].get('unidad'): unidad = str(stock_rows[0].get('unidad'))
                    else:
                        real_stock = float(stock_rows[0][0] or 0)
                        if stock_rows[0][1]: unidad = str(stock_rows[0][1])
                
                import re as _re
                regla_limpia = _re.sub(r'<[^>]+>', '', regla_raw).strip()
                if not regla_limpia and precio_of > 0:
                    regla_limpia = f"Comprando {unidad.lower()}"
                    
                from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
                vistas = motor_ventas.get_personas_viendo("mes")
                unidades_vendidas = motor_ventas.get_unidades_vendidas(nombre, "mes")
                self.destacada_lista.emit(nombre, precio, precio_of, real_stock, unidad, regla_limpia, vistas, unidades_vendidas)
            else:
                # Emitir Combo Simulado
                if isinstance(rows[0], dict):
                    centro = str(rows[0].get('nombre_producto', ''))
                else:
                    centro = str(rows[0][0])
                    
                nombres = MotorIALocal.obtener_relacionados(centro, limit=1)
                self.combo_listo.emit(centro, nombres)
        except Exception as e:
            logger.error(f"MotorCombos Error: {e}")

class MotorIAPanel(QThread):
    ia_lista = pyqtSignal(str, str, float, float, tuple)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clima = ("sol", "22°C Pilar")
        
    def set_clima(self, clima):
        self.clima = clima
        
    def run(self):
        try:
            q = "SELECT nombre_producto, precio_normal, precio_oferta, regla_texto FROM carteleria_global ORDER BY RANDOM() LIMIT 5"
            if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb":
                q = q.replace("RANDOM()", "RAND()")
                
            rows = db_manager.execute_query(q)
            if not rows: return
            
            prod_lista = []
            for r in rows:
                if isinstance(r, dict):
                    nombre = str(r.get('nombre_producto', ''))
                    unidad = "Kilos" if "Kilos" in str(r.get('regla_texto') or "") else "Unidades"
                    precio = float(r.get('precio_normal') or 0)
                    precio_of = float(r.get('precio_oferta') or 0)
                else:
                    nombre = str(r[0])
                    unidad = "Kilos" if "Kilos" in str(r[3] or "") else "Unidades"
                    precio = float(r[1])
                    precio_of = float(r[2])
                    
                stock_rows = db_manager.execute_query("SELECT stock, unidad FROM productos WHERE LOWER(nombre) = LOWER(?)", (nombre,))
                real_stock = 0.0
                if stock_rows:
                    if isinstance(stock_rows[0], dict):
                        real_stock = float(stock_rows[0].get('stock') or 0)
                        if stock_rows[0].get('unidad'): unidad = str(stock_rows[0].get('unidad'))
                    else:
                        real_stock = float(stock_rows[0][0] or 0)
                        if stock_rows[0][1]: unidad = str(stock_rows[0][1])
                
                prod_lista.append((nombre, precio, precio_of, real_stock, unidad))
                
            msg, prod, precio, precio_oferta = MotorIALocal.generar_recomendacion_lobo(self.clima, prod_lista)
            self.ia_lista.emit(msg, prod, precio, precio_oferta, self.clima)
        except Exception as e:
            logger.error(f"MotorIAPanel Error: {e}")
