import json
import random
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from src.logger import logger
from src.base_de_datos.database import db_manager
from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
from src.carteleria.ia_chef_lobo.motor_ia import MotorIA as IAMotorCore

class MotorCarrusel(QThread):
    datos_listos = pyqtSignal(list, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.modo_actual = 0 # 0=Hoy, 1=Semana, 2=Mes
        
    def run(self):
        try:
            modos = ["hoy", "semana", "mes"]
            titulos = ["LO MÁS VENDIDO - HOY", "TOP DE LA SEMANA", "TOP DEL MES"]
            
            modo_str = modos[self.modo_actual]
            titulo_str = titulos[self.modo_actual]
            
            top_real = motor_ventas.get_top_ventas(limit=10, periodo=modo_str)
            
            # Buscar en carteleria_global los precios limpios
            prod_lista = []
            for p in top_real:
                nombre = p['nombre']
                q = "SELECT precio_normal, precio_oferta, regla_texto FROM carteleria_global WHERE LOWER(nombre_producto) = LOWER(?)"
                if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb":
                    q = "SELECT precio_normal, precio_oferta, regla_texto FROM carteleria_global WHERE LOWER(nombre_producto) = LOWER(%s)"
                
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
                    
                    prod_lista.append((nombre, precio, precio_of, p['cantidad'], unidad))
            
            self.modo_actual = (self.modo_actual + 1) % 3
            if prod_lista:
                self.datos_listos.emit(prod_lista, titulo_str)
            else:
                self.datos_listos.emit([], "")
        except Exception as e:
            logger.error(f"MotorCarrusel Error: {e}")
            self.datos_listos.emit([], "")

class MotorCombos(QThread):
    combo_listo = pyqtSignal(str, list)
    destacada_lista = pyqtSignal(str, float, float, float, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def run(self):
        try:
            # Buscar productos en oferta aleatorios desde carteleria_global
            q = "SELECT nombre_producto, precio_normal, precio_oferta, regla_texto FROM carteleria_global WHERE precio_oferta > 0 ORDER BY RANDOM() LIMIT 5"
            if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb":
                q = q.replace("RANDOM()", "RAND()")
                
            rows = db_manager.execute_query(q)
            if not rows: return
            
            if random.choice([True, False]):
                # Emitir Destacada
                r = rows[0]
                if isinstance(r, dict):
                    unidad = "Kilos" if "Kilos" in str(r.get('regla_texto') or "") else "Unidades"
                    self.destacada_lista.emit(str(r.get('nombre_producto', '')), float(r.get('precio_normal') or 0), float(r.get('precio_oferta') or 0), 1.0, unidad)
                else:
                    unidad = "Kilos" if "Kilos" in str(r[3] or "") else "Unidades"
                    self.destacada_lista.emit(str(r[0]), float(r[1]), float(r[2]), 1.0, unidad)
            else:
                # Emitir Combo Simulado
                if isinstance(rows[0], dict):
                    nombres = [str(r.get('nombre_producto', '')) for r in rows[:3]]
                    centro = str(rows[0].get('nombre_producto', ''))
                else:
                    nombres = [str(r[0]) for r in rows[:3]]
                    centro = str(rows[0][0])
                self.combo_listo.emit(centro, nombres)
        except Exception as e:
            logger.error(f"MotorCombos Error: {e}")

class MotorIAPanel(QThread):
    ia_lista = pyqtSignal(str, str, float, float, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clima = "despejado"
        
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
                    unidad = "Kilos" if "Kilos" in str(r.get('regla_texto') or "") else "Unidades"
                    prod_lista.append((str(r.get('nombre_producto', '')), float(r.get('precio_normal') or 0), float(r.get('precio_oferta') or 0), 0.0, unidad))
                else:
                    unidad = "Kilos" if "Kilos" in str(r[3] or "") else "Unidades"
                    prod_lista.append((str(r[0]), float(r[1]), float(r[2]), 0.0, unidad))
                
            msg, prod, precio, precio_oferta = IAMotorCore.generar_recomendacion(None, self.clima, prod_lista)
            self.ia_lista.emit(msg, prod, precio, precio_oferta, self.clima)
        except Exception as e:
            logger.error(f"MotorIAPanel Error: {e}")
