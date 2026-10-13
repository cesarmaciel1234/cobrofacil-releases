from src.base_de_datos.database import db_manager
from src.utils.barcode_parser import BarcodeParser

_COLS_PROD = (
    "SELECT id, nombre, codigo, precio, stock, cant_oferta, precio_oferta, cant_mayoreo, precio_mayoreo, "
    "precio_oferta_relampago, limite_oferta_relampago, ventas_oferta_relampago, "
    "es_pesable, unidad, departamento FROM productos "
)


def _palabras(nombre):
    return str(nombre or "").replace("-", " ").replace("/", " ").split()


def _coincide_inicio_nombre(nombre, consulta):
    """'asa' pega ASADO o CARNE ASADA. No pega masa ni lo que lleva asa al medio."""
    tokens = str(consulta or "").strip().lower().split()
    if not tokens:
        return False
    palabras = [p.lower() for p in _palabras(nombre)]
    if not palabras:
        return False
    if len(tokens) == 1:
        q = tokens[0]
        return any(p.startswith(q) for p in palabras[:2])
    if len(palabras) < len(tokens):
        return False
    for i in range(0, min(2, len(palabras) - len(tokens) + 1)):
        if all(palabras[i + k].startswith(tokens[k]) for k in range(len(tokens))):
            return True
    return False


class CarritoService:
    def buscar_productos(self, txt):
        """Nombre: desde 3 letras, solo inicio de 1.ª o 2.ª palabra. Código: prefijo. Límite 8."""
        txt = (txt or "").strip()
        if not txt:
            return []
        if txt.isdigit():
            res = db_manager.execute_query(
                _COLS_PROD + "WHERE id = ? OR codigo = ? LIMIT 5",
                (int(txt), txt),
            )
            return res or []
        if len(txt) < 3:
            return []
        pref = f"{txt}%"
        palabra = f"% {txt}%"
        res = db_manager.execute_query(
            _COLS_PROD + "WHERE nombre LIKE ? OR nombre LIKE ? OR COALESCE(codigo,'') LIKE ? LIMIT 24",
            (pref, palabra, pref),
        )
        out = []
        for fila in res or []:
            fila_d = dict(fila) if hasattr(fila, "keys") else fila
            nombre = fila_d.get("nombre") if hasattr(fila_d, "get") else fila_d["nombre"]
            codigo = ""
            try:
                codigo = str(fila_d.get("codigo") or "")
            except Exception:
                pass
            if codigo.lower().startswith(txt.lower()) or _coincide_inicio_nombre(nombre, txt):
                out.append(fila)
            if len(out) >= 8:
                break
        return out

    def buscar_producto_exacto(self, txt):
        """Busca un producto exactamente por su ID o codigo de barras."""
        if txt.isdigit():
            res = db_manager.execute_query(
                "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta, cant_mayoreo, precio_mayoreo, "
                "precio_oferta_relampago, limite_oferta_relampago, ventas_oferta_relampago, "
                "es_pesable, unidad, departamento FROM productos WHERE id = ? OR codigo = ?",
                (int(txt), txt),
            )
        else:
            res = db_manager.execute_query(
                "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta, cant_mayoreo, precio_mayoreo, "
                "precio_oferta_relampago, limite_oferta_relampago, ventas_oferta_relampago, "
                "es_pesable, unidad, departamento FROM productos WHERE codigo = ?",
                (txt,),
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

        # El código de barras no hace LIKE al nombre: eso traba la caja.
        if txt.isdigit() or (txt.isalnum() and any(ch.isdigit() for ch in txt) and len(txt) >= 8):
            return False, None, 0, f"No se encontró ningún producto con el código: '{txt}'"

        res_busqueda = self.buscar_productos(txt)
        if res_busqueda:
            return True, res_busqueda[0], cantidad_multiplicador, ""

        return False, None, 0, f"No se encontró ningún producto con el código o nombre: '{txt}'"
