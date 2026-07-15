import json

class MotorRendimiento:
    """
    Motor global que analiza el historial de promedios (despostes previos)
    y permite inyectar el rendimiento en forma proporcional ('receta') 
    directamente al stock del inventario.
    """

    @staticmethod
    def calcular_promedio_rendimiento(tipo_carne, db_lectura):
        """
        Lee los últimos 10 historiales de un tipo de carne, y devuelve 
        un diccionario con la proporción de cada corte respecto al peso de la res.
        Ejemplo: {"Tapa de asado": 0.05, "Roast beef": 0.12, ...}
        """
        if not db_lectura: return {}
        
        try:
            historial = db_lectura.execute_query(
                "SELECT kilos_base, datos_json FROM historial_promedios WHERE tipo_carne = ? ORDER BY id DESC LIMIT 10",
                (tipo_carne,)
            )
            
            if not historial: return {}
            
            total_kilos_base = 0.0
            sumas_cortes = {}
            
            for row in historial:
                kilos_base = float(row['kilos_base'] if isinstance(row, dict) else row[0])
                if kilos_base <= 0: continue
                
                try:
                    datos = json.loads(row['datos_json'] if isinstance(row, dict) else row[1])
                    total_kilos_base += kilos_base
                    
                    for fila in datos:
                        if len(fila) >= 2:
                            nombre_corte = str(fila[0]).strip()
                            try:
                                kilos_corte = float(fila[1])
                                sumas_cortes[nombre_corte] = sumas_cortes.get(nombre_corte, 0.0) + kilos_corte
                            except ValueError:
                                pass
                except Exception:
                    pass
            
            if total_kilos_base <= 0: return {}
            
            # Calcular la receta (proporción)
            receta = {}
            for corte, kilos_acum in sumas_cortes.items():
                receta[corte] = kilos_acum / total_kilos_base
                
            return receta
            
        except Exception as e:
            print(f"Error al calcular promedio de rendimiento: {e}")
            return {}

    @staticmethod
    def aplicar_desposte_a_stock(tipo_carne, kilos_totales, db_admin, db_jefe=None):
        """
        Calcula cuántos kilos de cada corte rinde la res comprada y los suma al inventario.
        """
        if not db_admin: return False
        
        try:
            db_lectura = db_admin if db_admin else db_jefe
            receta = MotorRendimiento.calcular_promedio_rendimiento(tipo_carne, db_lectura)
            if not receta:
                print(f"No hay receta histórica para {tipo_carne}")
                return False
                
            for nombre_corte, proporcion in receta.items():
                kilos_calculados = kilos_totales * proporcion
                if kilos_calculados <= 0: continue
                
                # Actualizar el stock en MariaDB / SQLite global
                # Intentamos primero buscar el producto por nombre exacto
                res = db_admin.execute_query("SELECT id, stock FROM productos WHERE nombre = ?", (nombre_corte,))
                if res and len(res) > 0:
                    prod_id = res[0]['id'] if isinstance(res[0], dict) else res[0][0]
                    stock_actual = float(res[0]['stock'] if isinstance(res[0], dict) else res[0][1] or 0)
                    nuevo_stock = stock_actual + kilos_calculados
                    
                    db_admin.execute_non_query("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, prod_id))
            
            return True
        except Exception as e:
            print(f"Error aplicando desposte al stock: {e}")
            return False
