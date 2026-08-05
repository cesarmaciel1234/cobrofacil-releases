from src.base_de_datos.database import db_manager
from src.cerebro_global.servicios.cache_productos import cache_productos


class BuscadorDePreciosYStock:
    """
    Módulo Ayudante (Tan simple como para que lo entienda un niño de 10 años):
    Su único trabajo es: cuando le damos el nombre de un producto (ej: 'Asado'),
    busca cuánto cuesta hoy, cuánto stock hay en la heladera/depósito y su unidad (Kilos o Unidades).
    ¡Busca tanto en las promociones (carteleria_global) como en la tabla general (productos) 
    para que NINGÚN producto vendido hoy se quede afuera del cartel!
    """

    @staticmethod
    def _buscar_producto_en_cache(nombre: str):
        """Evita N+1 queries LIKE a MariaDB (timeout 2013 con inventario grande)."""
        nombre_norm = nombre.strip().lower()
        if not nombre_norm:
            return None
        productos = cache_productos.obtener_todos()
        for row in productos:
            pn = str(row.get("nombre") or "").strip().lower()
            if pn == nombre_norm:
                return row
        for row in productos:
            pn = str(row.get("nombre") or "").strip().lower()
            if nombre_norm in pn or pn in nombre_norm:
                return row
        return None

    @staticmethod
    def armar_lista_para_pantalla(productos_vendidos_hoy):
        """
        Recibe una lista de diccionarios con el volumen o frecuencia de ventas del día: 
        [{'nombre': 'Asado', 'cantidad': 25.5}, ...]
        Y devuelve las tuplas exactas listas para mostrar en la pantalla del carrusel:
        [(nombre, precio_normal, precio_oferta, stock_real, unidad, cantidad_vendida)]
        """
        resultado_lista = []
        nombres_procesados = set()
        
        for prod in productos_vendidos_hoy:
            if isinstance(prod, dict):
                nombre = str(prod.get('nombre') or '').strip()
                cantidad = float(prod.get('cantidad', 0) or 0)
            else:
                nombre = str(prod[0]).strip() if len(prod) > 0 else ""
                cantidad = float(prod[1] or 0) if len(prod) > 1 else 0.0
                
            nombre = nombre.replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
                
            # PASO 1 DE VERIFICACIÓN: Excluir cobros genéricos (en negro/cobro libre/no inventariados) o duplicados
            nombres_ignorados = {
                "ARTICULO COMUN", "ARTÍCULO COMÚN", "ARTICULO LIBRE", "ARTÍCULO LIBRE",
                "VENTA LIBRE", "VARIOS", "COBRO RAPIDO", "COBRO RÁPIDO",
                "DIFERENCIA", "AJUSTE", "ENVASADO", "TICKET", "SUBTOTAL"
            }
            if not nombre or nombre.lower() in nombres_procesados or nombre.upper() in nombres_ignorados:
                continue
            nombres_procesados.add(nombre.lower())
            
            precio_normal = 0.0
            precio_oferta = 0.0
            unidad = "Unidades"
            stock_real = 99.0
            encontro_datos = False
            
            # PASO 2 DE VERIFICACIÓN: Comprobar que el producto EXISTE genuinamente en el Inventario o Promociones.
            # a) Intentamos leer de 'carteleria_global'
            q_cartel = "SELECT precio_normal, precio_oferta, regla_texto FROM carteleria_global WHERE TRIM(LOWER(nombre_producto)) = TRIM(LOWER(?))"
            rows_cartel = db_manager.execute_query(q_cartel, (nombre.strip(),))
            if not rows_cartel:
                q_cartel = "SELECT precio_normal, precio_oferta, regla_texto FROM carteleria_global WHERE LOWER(nombre_producto) LIKE LOWER(?)"
                rows_cartel = db_manager.execute_query(q_cartel, (f"%{nombre.strip()}%",))
                
            if rows_cartel:
                row = rows_cartel[0]
                if isinstance(row, dict):
                    precio_normal = float(row.get('precio_normal') or 0)
                    precio_oferta = float(row.get('precio_oferta') or 0)
                    regla = str(row.get('regla_texto') or "")
                else:
                    precio_normal = float(row[0] or 0)
                    precio_oferta = float(row[1] or 0)
                    regla = str(row[2] or "")
                if "Kilo" in regla or "KG" in regla.upper():
                    unidad = "Kilos"
                encontro_datos = True

            # b) Buscamos en inventario vía caché en memoria (sin LIKE por producto a MariaDB)
            row_p = BuscadorDePreciosYStock._buscar_producto_en_cache(nombre)
            if row_p:
                if isinstance(row_p, dict):
                    if not encontro_datos:
                        precio_normal = float(row_p.get('precio') or 0)
                        precio_oferta = float(row_p.get('precio_oferta') or 0)
                    stock_real = float(row_p.get('stock') or 0)
                    u_db = str(row_p.get('unidad') or '').upper()
                    if u_db in ['KG', 'KILO', 'KILOS']:
                        unidad = "Kilos"
                    elif u_db in ['UNIDAD', 'UNIDADES', 'U', 'UN']:
                        unidad = "Unidades"
                else:
                    if not encontro_datos:
                        precio_normal = float(row_p[0] or 0)
                        precio_oferta = float(row_p[1] or 0)
                    stock_real = float(row_p[2] or 0)
                    u_db = str(row_p[3] or '').upper()
                    if u_db in ['KG', 'KILO', 'KILOS']:
                        unidad = "Kilos"
                    elif u_db in ['UNIDAD', 'UNIDADES', 'U', 'UN']:
                        unidad = "Unidades"
                encontro_datos = True
                
            # CUMPLE LAS EXPECTATIVAS: Solo si existe auténticamente en el inventario lo exponemos al público en la cartelería
            if encontro_datos:
                resultado_lista.append((nombre, precio_normal, precio_oferta, stock_real, unidad, cantidad))
                
        return resultado_lista
