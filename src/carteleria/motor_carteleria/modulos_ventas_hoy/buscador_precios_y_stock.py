from src.base_de_datos.database import db_manager
from src.cerebro_global.servicios.cache_productos import cache_productos
from src.utils.text_db import safe_mariadb_text

class BuscadorDePreciosYStock:
    """
    Módulo Ayudante (Tan simple como para que lo entienda un niño de 10 años):
    Su único trabajo es: cuando le damos el nombre de un producto (ej: 'Asado'),
    busca cuánto cuesta hoy, cuánto stock hay en la heladera/depósito y su unidad (Kilos o Unidades).
    ¡Busca tanto en las promociones (carteleria_global) como en la tabla general (productos) 
    para que NINGÚN producto vendido hoy se quede afuera del cartel!
    """
    
    _NOMBRES_IGNORADOS = frozenset({
        "ARTICULO COMUN", "ARTÍCULO COMÚN", "ARTICULO LIBRE", "ARTÍCULO LIBRE",
        "VENTA LIBRE", "VARIOS", "COBRO RAPIDO", "COBRO RÁPIDO",
        "DIFERENCIA", "AJUSTE", "ENVASADO", "TICKET", "SUBTOTAL",
    })

    @staticmethod
    def _limpiar_nombre(nombre):
        return safe_mariadb_text(str(nombre or "").strip())

    @staticmethod
    def _build_lookup_indices():
        """Carga catálogo en memoria (evita TRIM/LOWER por producto → timeout 2013 en MariaDB)."""
        prod_by_name = {}
        for row in cache_productos.obtener_todos():
            if isinstance(row, dict):
                nom = BuscadorDePreciosYStock._limpiar_nombre(row.get("nombre"))
            else:
                nom = BuscadorDePreciosYStock._limpiar_nombre(row[1] if len(row) > 1 else "")
            if nom:
                prod_by_name.setdefault(nom.lower(), row)

        cartel_by_name = {}
        try:
            rows_cartel = db_manager.execute_query(
                "SELECT nombre_producto, precio_normal, precio_oferta, regla_texto FROM carteleria_global"
            ) or []
            for row in rows_cartel:
                if isinstance(row, dict):
                    nom = BuscadorDePreciosYStock._limpiar_nombre(row.get("nombre_producto"))
                else:
                    nom = BuscadorDePreciosYStock._limpiar_nombre(row[0] if row else "")
                if nom:
                    cartel_by_name.setdefault(nom.lower(), row)
        except Exception:
            pass

        return prod_by_name, cartel_by_name

    @staticmethod
    def _buscar_en_carteleria(nombre, cartel_by_name):
        key = nombre.lower()
        row = cartel_by_name.get(key)
        if row is None:
            for k, v in cartel_by_name.items():
                if key in k or k in key:
                    row = v
                    break
        if not row:
            return None
        if isinstance(row, dict):
            return {
                "precio_normal": float(row.get("precio_normal") or 0),
                "precio_oferta": float(row.get("precio_oferta") or 0),
                "regla": str(row.get("regla_texto") or ""),
            }
        return {
            "precio_normal": float(row[0] or 0),
            "precio_oferta": float(row[1] or 0),
            "regla": str(row[2] or ""),
        }

    @staticmethod
    def _buscar_en_productos(nombre, prod_by_name):
        key = nombre.lower()
        row = prod_by_name.get(key)
        if row is None:
            for k, v in prod_by_name.items():
                if key in k or k in key:
                    row = v
                    break
        if not row:
            return None
        if isinstance(row, dict):
            return {
                "precio": float(row.get("precio") or 0),
                "precio_oferta": float(row.get("precio_oferta") or 0),
                "stock": float(row.get("stock") or 0),
                "unidad": str(row.get("unidad") or ""),
            }
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
        prod_by_name, cartel_by_name = BuscadorDePreciosYStock._build_lookup_indices()
        
        for prod in productos_vendidos_hoy:
            if isinstance(prod, dict):
                nombre = BuscadorDePreciosYStock._limpiar_nombre(prod.get("nombre"))
                cantidad = float(prod.get("cantidad", 0) or 0)
            else:
                nombre = BuscadorDePreciosYStock._limpiar_nombre(prod[0] if len(prod) > 0 else "")
                cantidad = float(prod[1] or 0) if len(prod) > 1 else 0.0
                
            if not nombre or nombre.lower() in nombres_procesados or nombre.upper() in BuscadorDePreciosYStock._NOMBRES_IGNORADOS:
                continue
            nombres_procesados.add(nombre.lower())
            
            precio_normal = 0.0
            precio_oferta = 0.0
            unidad = "Unidades"
            stock_real = 99.0
            encontro_datos = False
            
            cartel = BuscadorDePreciosYStock._buscar_en_carteleria(nombre, cartel_by_name)
            if cartel:
                precio_normal = cartel["precio_normal"]
                precio_oferta = cartel["precio_oferta"]
                regla = cartel["regla"]
                if "Kilo" in regla or "KG" in regla.upper():
                    unidad = "Kilos"
                encontro_datos = True

            prod_row = BuscadorDePreciosYStock._buscar_en_productos(nombre, prod_by_name)
            if prod_row:
                if not encontro_datos:
                    precio_normal = prod_row["precio"]
                    precio_oferta = prod_row["precio_oferta"]
                stock_real = prod_row["stock"]
                u_db = prod_row["unidad"].upper()
                if u_db in ("KG", "KILO", "KILOS"):
                    unidad = "Kilos"
                elif u_db in ("UNIDAD", "UNIDADES", "U", "UN"):
                    unidad = "Unidades"
                encontro_datos = True
                
            if encontro_datos:
                resultado_lista.append((nombre, precio_normal, precio_oferta, stock_real, unidad, cantidad))
                
        return resultado_lista
