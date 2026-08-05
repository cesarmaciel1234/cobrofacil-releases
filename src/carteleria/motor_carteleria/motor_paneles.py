import json
import random
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from src.logger import logger
from src.base_de_datos.database import db_manager
from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
from src.cerebro_global.carteleria_cerebro.motor_ia_local import MotorIALocal
from src.cerebro_global.servicios.cache_productos import cache_productos


def _indice_stock_unidad():
    """Stock/unidad por nombre sin JOIN LOWER(productos) — evita timeout 2013 en MariaDB."""
    idx = {}
    for p in cache_productos.obtener_todos():
        k = str(p.get("nombre") or "").strip().lower()
        if k:
            idx[k] = (float(p.get("stock") or 0), str(p.get("unidad") or ""))
    return idx


def _enriquecer_filas_carteleria(rows, idx_stock):
    """Convierte filas de carteleria_global a tuplas con stock/unidad desde caché."""
    enriched = []
    for r in rows:
        if isinstance(r, dict):
            nombre = str(r.get("nombre_producto", ""))
            precio = float(r.get("precio_normal") or 0)
            precio_of = float(r.get("precio_oferta") or 0)
            regla = str(r.get("regla_texto") or "")
        else:
            nombre = str(r[0])
            precio = float(r[1] or 0)
            precio_of = float(r[2] or 0)
            regla = str(r[3] or "")
        stock, unidad = idx_stock.get(nombre.strip().lower(), (0.0, ""))
        enriched.append((nombre, precio, precio_of, regla, stock, unidad))
    return enriched


def _muestra_carteleria(where_sql="", params=(), pool_limit=40, sample_limit=5):
    """Muestra aleatoria sin ORDER BY RAND() ni JOIN productos (timeout MariaDB 2013)."""
    q = (
        "SELECT nombre_producto, precio_normal, precio_oferta, regla_texto "
        "FROM carteleria_global "
    )
    if where_sql:
        q += f"WHERE {where_sql} "
    q += "ORDER BY precio_oferta DESC LIMIT ?"
    rows = db_manager.execute_query(q, params + (pool_limit,)) or []
    if not rows:
        return []
    enriched = _enriquecer_filas_carteleria(rows, _indice_stock_unidad())
    if len(enriched) <= sample_limit:
        return enriched
    return random.sample(enriched, sample_limit)


class MotorCarrusel(QThread):
    datos_listos = pyqtSignal(list, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.modo_actual = 0 # 0=Elegidos Hoy, 1=Volumen Hoy, 2=Recomendados Hoy
        
    def run(self):
        try:
            from src.carteleria.motor_carteleria.modulos_ventas_hoy import (
                ModuloMasElegidosHoy,
                ModuloMasVolumenHoy,
                ModuloRecomendadoHoy
            )
            
            # Los 3 módulos enfocados en las ventas y tickets frescos de HOY (sin sobrecargar de banners innecesarios)
            modulos_carteleria = [
                ModuloMasElegidosHoy(),
                ModuloMasVolumenHoy(),
                ModuloRecomendadoHoy()
            ]
            
            # Elegimos el módulo correspondiente al ciclo actual y extraemos sus productos reales del día
            modulo_seleccionado = modulos_carteleria[self.modo_actual % len(modulos_carteleria)]
            prod_lista, titulo_str = modulo_seleccionado.obtener_productos_para_cartel(limit=10)
            
            # Rotar en orden al siguiente módulo para el próximo refresco en la pantalla
            self.modo_actual = (self.modo_actual + 1) % len(modulos_carteleria)
            
            if not self.isInterruptionRequested():
                if prod_lista:
                    self.datos_listos.emit(prod_lista, titulo_str)
                else:
                    self.datos_listos.emit([], "")
        except RuntimeError:
            pass
        except Exception as e:
            logger.error(f"MotorCarrusel Error: {e}")
            try:
                if not self.isInterruptionRequested():
                    self.datos_listos.emit([], "")
            except RuntimeError:
                pass

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
            
            eleccion = random.choice([0, 1])
            
            # Buscar productos en oferta (sin RAND/JOIN LOWER: timeout 2013 en MariaDB)
            rows = _muestra_carteleria("precio_oferta > 0", (), 40, 5)
            
            if not rows: return
            
            if eleccion == 0:
                # Emitir Destacada (Oferta Relámpago)
                r = rows[0]
                if isinstance(r, dict):
                    nombre = str(r.get('nombre_producto', ''))
                    regla_raw = str(r.get('regla_texto') or "")
                    unidad = "Kilos" if "Kilos" in regla_raw else "Unidades"
                    precio = float(r.get('precio_normal') or 0)
                    precio_of = float(r.get('precio_oferta') or 0)
                    real_stock = float(r.get('stock') or 0)
                    if r.get('unidad'): unidad = str(r.get('unidad'))
                else:
                    nombre = str(r[0])
                    precio = float(r[1])
                    precio_of = float(r[2])
                    regla_raw = str(r[3] or "")
                    real_stock = float(r[4] or 0)
                    unidad = "Kilos" if "Kilos" in regla_raw else "Unidades"
                    if r[5]: unidad = str(r[5])
                
                import re as _re
                regla_limpia = _re.sub(r'<[^>]+>', '', regla_raw).strip()
                if not regla_limpia and precio_of > 0:
                    un_text = "kilo" if "kilo" in unidad.lower() else ("unidad" if "unidad" in unidad.lower() else unidad.lower())
                    regla_limpia = f"Llevando 1 {un_text}"
                    
                from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
                vistas = motor_ventas.get_personas_viendo("mes")
                unidades_vendidas = motor_ventas.get_unidades_vendidas(nombre, "mes")
                self.destacada_lista.emit(nombre, precio, precio_of, real_stock, unidad, regla_limpia, vistas, unidades_vendidas)
            else:
                # Emitir Combo Simulado / Venta Cruzada Inteligente
                if isinstance(rows[0], dict):
                    centro = str(rows[0].get('nombre_producto', ''))
                else:
                    centro = str(rows[0][0])
                centro = centro.replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
                    
                from src.carteleria.motor_carteleria.modulos_ventas_hoy.venta_cruzada_inteligente import VentaCruzadaInteligente
                nombres = VentaCruzadaInteligente.obtener_relacionados_para_ticket(centro, limit=3)
                if not self.isInterruptionRequested():
                    self.combo_listo.emit(centro, nombres)
        except RuntimeError:
            pass
        except Exception as e:
            logger.error(f"MotorCombos Error: {e}")

class MotorIAPanel(QThread):
    ia_lista = pyqtSignal(str, str, float, float, str, tuple) # Añadida regla de promoción (str)
    promo_lista = pyqtSignal(str, float, list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clima = ("sol", "22°C Pilar")
        self.turno_ia = 0 # 0=Chef Lobo, 1=Promo Especial / Combo
        
    def set_clima(self, clima):
        self.clima = clima
        
    def run(self):
        try:
            if self.isInterruptionRequested(): return
            import random
            import json
            
            self.turno_ia = (self.turno_ia + 1) % 2
            
            # Si el turno es 1, intentamos mostrar PROMO ESPECIAL en la 4ta pantalla con Chef Lobo
            if self.turno_ia == 1:
                try:
                    promo_rows = db_manager.execute_query(
                        "SELECT nombre, precio_combo, productos_json FROM combos"
                    )
                    if promo_rows:
                        promo_rows = [random.choice(list(promo_rows))]
                    
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
                        if p_list and not self.isInterruptionRequested():
                            self.promo_lista.emit(p_nombre, p_precio, p_list)
                            return
                except:
                    pass
            
            # Si es turno 0 o si no había combos guardados, mostramos a Chef Lobo y su recomendación con clima
            rows = _muestra_carteleria("", (), 40, 5)
            if not rows or self.isInterruptionRequested(): return
            
            prod_lista = []
            reglas_map = {}
            for r in rows:
                if isinstance(r, dict):
                    nombre = str(r.get('nombre_producto', ''))
                    regla_t = str(r.get('regla_texto') or "").strip()
                    unidad = "Kilos" if "Kilos" in regla_t else "Unidades"
                    precio = float(r.get('precio_normal') or 0)
                    precio_of = float(r.get('precio_oferta') or 0)
                    real_stock = float(r.get('stock') or 0)
                    if r.get('unidad'): unidad = str(r.get('unidad'))
                else:
                    nombre = str(r[0])
                    precio = float(r[1])
                    precio_of = float(r[2])
                    regla_t = str(r[3] or "").strip()
                    real_stock = float(r[4] or 0)
                    unidad = "Kilos" if "Kilos" in regla_t else "Unidades"
                    if r[5]: unidad = str(r[5])
                    
                reglas_map[nombre.lower()] = regla_t
                prod_lista.append((nombre, precio, precio_of, real_stock, unidad))
                
            msg, prod, precio, precio_oferta = MotorIALocal.generar_recomendacion_lobo(self.clima, prod_lista)
            regla_enviada = reglas_map.get(str(prod).lower(), "")
            if not self.isInterruptionRequested():
                self.ia_lista.emit(msg, prod, precio, precio_oferta, regla_enviada, self.clima)
        except RuntimeError:
            pass
        except Exception as e:
            logger.error(f"MotorIAPanel Error: {e}")
