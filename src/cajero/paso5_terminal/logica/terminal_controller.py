from src.base_de_datos.database import db_manager
from src.utils.barcode_parser import BarcodeParser

class TerminalController:
    """
    Controlador (Presenter) para la Terminal Paso 5.
    Maneja la lógica de negocio pura: búsqueda de productos, parseo de códigos de barra, 
    y validación de stock, separándola de la vista principal.
    """
    def __init__(self, view):
        self.view = view

    def buscar_productos(self, txt):
        """Busca productos por ID o aproximación de nombre. Retorna lista de diccionarios."""
        res = db_manager.execute_query(
            "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta FROM productos WHERE id = ? OR nombre LIKE ? LIMIT 5", 
            (txt, f"%{txt}%")
        )
        return res if res else []

    def buscar_producto_exacto(self, txt):
        """Busca un producto exactamente por su ID."""
        res = db_manager.execute_query(
            "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta FROM productos WHERE id = ?", 
            (txt,)
        )
        return res[0] if res else None

    def procesar_codigo_escaneado(self, txt_raw):
        """
        Analiza el texto escaneado.
        Puede ser un código de barras normal, un código de balanza, un artículo común (+), o un multiplicador (*).
        Retorna un tuple: (éxito: bool, producto: dict, cantidad: float, mensaje_error: str)
        """
        txt, cantidad_multiplicador = BarcodeParser.parse_scan_text(txt_raw)
        
        if not txt:
            return False, None, 0, "FINALIZAR_VENTA"

        # 1. Artículo Común intencional usando el prefijo '+'
        p_manual, success = BarcodeParser.try_parse_manual_item(txt_raw.strip())
        if success:
            return True, p_manual, cantidad_multiplicador, ""

        # 2. Búsqueda por ID exacto (Barcode completo) primero
        p_exacto = self.buscar_producto_exacto(txt)
        if p_exacto:
            return True, p_exacto, cantidad_multiplicador, ""

        # 3. Códigos de Balanza (Configuración Dinámica)
        if BarcodeParser.is_balanza_ean(txt):
            try:
                from src.repositories.producto_repository import ProductoRepository
            except ImportError:
                return False, None, 0, "Error interno de repositorios."

            plu, plu_limpio = BarcodeParser.extract_plu_from_barcode(txt)
            p = ProductoRepository.obtener_por_plu_balanza(plu)
            if p:
                precio_unitario = float(p['precio'])
                _, cantidad_balanza = BarcodeParser.parse_balanza_code(txt, precio_unitario)
                if cantidad_balanza is not None and cantidad_balanza > 0:
                    return True, p, cantidad_balanza, ""
            else:
                msg = (f"Etiqueta de balanza leída (PLU {plu_limpio}), pero no hay producto con ese código en inventario.\n\n"
                       f"El ID del producto debe coincidir con el PLU de la balanza (ej. producto 2050 → PLU 02050).\n"
                       f"Código escaneado: {txt}")
                return False, None, 0, msg

        # 4. Si no es exacto ni balanza, hacer búsqueda difusa (LIKE nombre)
        res_busqueda = self.buscar_productos(txt)
        if res_busqueda:
            return True, res_busqueda[0], cantidad_multiplicador, ""

        # 5. No encontrado
        return False, None, 0, f"No se encontró ningún producto con el código o nombre: '{txt}'"

    def stock_disponible(self, p, p_id):
        """Calcula el stock real en base de datos para un producto, o infinito si es servicio/artículo común."""
        if p_id == "000": return float('inf')
        
        # En el futuro, aquí se consultaría la BD en tiempo real para evitar condiciones de carrera,
        # pero por rendimiento en cajas, se usa el stock del diccionario provisto si está actualizado.
        try:
            return float(p['stock'] or 0.0)
        except:
            return 0.0
