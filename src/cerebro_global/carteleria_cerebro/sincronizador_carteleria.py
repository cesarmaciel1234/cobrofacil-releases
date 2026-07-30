import time
import datetime
import threading
import traceback
import re
from src.logger import logger
from src.base_de_datos.database import db_manager

def _limpiar_nombre(nombre):
    nombre = str(nombre or "")
    for tag in ["🔥 [OFERTA] ", "🔥 [OFERTA]", "[OFERTA] ", "[OFERTA]", "📦 [MAYOREO] ", "📦 [MAYOREO]", "🌟 "]:
        nombre = nombre.replace(tag, "")
    nombre = re.sub(r'^(?:oferta\s+de|oferta)\s+', '', nombre, flags=re.IGNORECASE).strip()
    return nombre

class SincronizadorCarteleria:
    """
    Cerebro independiente que carga los datos de 'productos' (Inventario),
    los formatea limpiamente (Kilos/Unidades/Colores), y los guarda en 'carteleria_global'
    para que la Grilla de Precios los consuma sin saturar el sistema.
    """
    def __init__(self, intervalo_segundos=30):
        self.intervalo = intervalo_segundos
        self.running = False
        self._thread = None
        
    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info("Sincronizador de Cartelería INICIADO.")
            
    def stop(self):
        self.running = False
        
    def _run_loop(self):
        # Sincronización inicial rápida
        self.sincronizar_ahora()
        
        while self.running:
            time.sleep(self.intervalo)
            self.sincronizar_ahora()
            
    def sincronizar_ahora(self):
        try:
            # 1. Leer inventario de productos
            query_productos = """
                SELECT categoria, nombre, precio, precio_oferta, cant_oferta, tipo_unidad_oferta, unidad
                FROM productos 
                WHERE precio > 0
            """
            filas = db_manager.execute_query(query_productos)
            if not filas:
                return
                
            nuevos_datos = []
            
            # 2. Formatear y preparar los datos
            for fila in filas:
                if isinstance(fila, dict):
                    departamento = str(fila.get('categoria', ''))
                    nombre_producto = _limpiar_nombre(fila.get('nombre', ''))
                    precio_normal = float(fila.get('precio') or 0)
                    precio_oferta = float(fila.get('precio_oferta') or 0)
                    cant_oferta = float(fila.get('cant_oferta') or 0)
                    tipo_unidad = str(fila.get('tipo_unidad_oferta') or "").strip().lower()
                    prod_unidad = str(fila.get('unidad') or "").strip().lower()
                else:
                    departamento = str(fila[0])
                    nombre_producto = _limpiar_nombre(fila[1])
                    precio_normal = float(fila[2] or 0)
                    precio_oferta = float(fila[3] or 0)
                    cant_oferta = float(fila[4] or 0)
                    tipo_unidad = str(fila[5] or "").strip().lower()
                    prod_unidad = str(fila[6] or "").strip().lower()
                
                regla_texto = ""
                if cant_oferta > 0:
                    import math
                    cant_display = cant_oferta
                    if cant_display >= 1:
                        frac = cant_display - math.floor(cant_display)
                        if frac >= 0.8:
                            cant_display = float(math.ceil(cant_display))

                    is_kilo = ('kilo' in prod_unidad or prod_unidad == 'kg' or 'kilo' in tipo_unidad or tipo_unidad == 'kg' or cant_oferta != int(cant_oferta))
                    if is_kilo:
                        if cant_display < 1:
                            t_un_str = f"{int(round(cant_display * 1000))} gs"
                        elif cant_display == 1:
                            t_un_str = "1 Kilo"
                        else:
                            t_un_str = f"{cant_display:g} Kilos"
                    else:
                        if cant_display == 1:
                            t_un_str = "1 Unidad"
                        else:
                            t_un_str = f"{int(cant_display)} Unidades"
                    
                    regla_texto = f"<span style='color: #00A859;'>Llevando</span> <span style='color: #DC2626;'>{t_un_str}</span>"
                
                nuevos_datos.append((
                    departamento,
                    nombre_producto,
                    precio_normal,
                    precio_oferta,
                    regla_texto
                ))
            
            # 3. Guardar en la tabla global limpiamente
            is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
            
            conn = db_manager.get_connection()
            try:
                cursor = conn.cursor()
                # Limpiar tabla vieja
                cursor.execute("DELETE FROM carteleria_global")
                
                # Insertar tabla nueva
                if is_mariadb:
                    query_insert = """
                        INSERT INTO carteleria_global 
                        (departamento, nombre_producto, precio_normal, precio_oferta, regla_texto) 
                        VALUES (%s, %s, %s, %s, %s)
                    """
                else:
                    query_insert = """
                        INSERT INTO carteleria_global 
                        (departamento, nombre_producto, precio_normal, precio_oferta, regla_texto) 
                        VALUES (?, ?, ?, ?, ?)
                    """
                    
                cursor.executemany(query_insert, nuevos_datos)
                conn.commit()
            except Exception as e_db:
                logger.error(f"SincronizadorCarteleria DB Error: {e_db}")
            finally:
                if hasattr(conn, 'close'):
                    conn.close()
                    
        except Exception as e:
            logger.error(f"SincronizadorCarteleria Loop Error: {e}\n{traceback.format_exc()}")

# Instancia global (Singleton)
sincronizador_carteleria = SincronizadorCarteleria(intervalo_segundos=30)
