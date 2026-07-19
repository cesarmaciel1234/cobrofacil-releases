import time
import datetime
import threading
import traceback
from src.logger import logger
from src.base_de_datos.database import db_manager

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
                SELECT categoria, nombre, precio, precio_oferta, cant_oferta, tipo_unidad_oferta
                FROM productos 
                WHERE precio > 0
            """
            filas = db_manager.execute_query(query_productos)
            if not filas:
                return
                
            nuevos_datos = []
            
            # 2. Formatear y preparar los datos
            for fila in filas:
                departamento = str(fila[0])
                nombre_producto = str(fila[1])
                precio_normal = float(fila[2] or 0)
                precio_oferta = float(fila[3] or 0)
                cant_oferta = float(fila[4] or 0)
                tipo_unidad = str(fila[5] or "").strip().lower()
                
                regla_texto = ""
                if cant_oferta > 0:
                    if 'unidad' in tipo_unidad or tipo_unidad == 'u':
                        t_un = "Unidades"
                    else:
                        t_un = "Kilos"
                    regla_texto = f"<span style='color: #00A859;'>Llevando</span> <span style='color: #DC2626;'>{cant_oferta:g} {t_un}</span>"
                
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
