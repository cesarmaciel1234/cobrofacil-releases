import logging
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class MotorImportacion:
    def __init__(self):
        self.logger = logging.getLogger("MotorImportacion")

    def exportar_excel(self, ruta_destino):
        """Exporta el inventario a un archivo Excel. Retorna (exito, mensaje)."""
        from src.admin.admin_importexport import exportar_excel
        return exportar_excel(ruta_destino)

    def importar_excel(self, ruta_origen, progres_callback=None):
        """Importa un archivo Excel. Retorna (exito, mensaje)."""
        from src.admin.admin_importexport import importar_excel
        # Note: the current importar_excel might need slightly different parameters
        return importar_excel(ruta_origen)

    def descargar_precarga(self):
        """Descarga e inserta datos desde el JSON de la nube."""
        import urllib.request
        import json
        
        url = "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/inventario_precargado.json?alt=media"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if not data:
                return False, "El archivo JSON está vacío."
            
            existing_res = db_manager.execute_query("SELECT codigo FROM productos WHERE codigo IS NOT NULL AND codigo != ''")
            existing_codes = set(str(row['codigo']).strip() for row in (existing_res or []))
            
            values = []
            for item in data:
                codigo = str(dict(item).get("codigo", "") or "").strip()
                nombre = str(dict(item).get("descripcion", "") or "").strip()
                if not codigo or not nombre: continue
                if codigo in existing_codes: continue
                    
                values.append((
                    codigo,
                    nombre,
                    float(dict(item).get("precio_venta") or 0.0),
                    float(dict(item).get("precio_costo") or 0.0),
                    float(dict(item).get("precio_mayoreo") or 0.0),
                    str(dict(item).get("departamento", "GENERAL") or "GENERAL"),
                    float(dict(item).get("stock") or 0.0),
                    float(dict(item).get("stock_minimo") or 0.0),
                    float(dict(item).get("stock_maximo") or 0.0),
                    1 if str(dict(item).get("tipo_venta", "")).strip().lower() in ("granel", "a granel") else 0
                ))
                existing_codes.add(codigo)
            
            if not values:
                return True, "Tu inventario ya está actualizado. No se encontraron productos nuevos en la nube."

            insert_keyword = "INSERT IGNORE INTO" if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb" else "INSERT OR IGNORE INTO"
            query = f"""
                {insert_keyword} productos (
                    codigo, nombre, precio, costo, precio_mayoreo,
                    departamento, stock, stock_minimo, stock_maximo, es_pesable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            db_manager.execute_many(query, values)
            return True, f"Se insertaron {len(values)} productos nuevos exitosamente."
        except Exception as e:
            return False, str(e)
