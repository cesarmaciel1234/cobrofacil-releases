from src.base_de_datos.database import db_manager

class ProductoRepository:
    """
    Capa de acceso a datos para la tabla 'productos'.
    Aísla las consultas SQL de la Interfaz Gráfica.
    """
    
    @staticmethod
    def obtener_por_id(producto_id: str) -> dict:
        """Devuelve un producto por su ID (código de barras) o None si no existe."""
        query = "SELECT id, nombre, precio, cant_oferta, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, es_sos FROM productos WHERE id = ?"
        resultados = db_manager.execute_query(query, (producto_id,))
        if resultados:
            return resultados[0]
        return None

    @staticmethod
    def obtener_por_plu_balanza(plu_raw: str) -> dict | None:
        """Busca producto por PLU de balanza (id numérico, con/sin ceros, o campo codigo)."""
        plu_limpio = plu_raw.lstrip("0") or "0"
        candidates: list[str] = []
        for c in (plu_raw, plu_limpio):
            if c and c not in candidates:
                candidates.append(c)
        if plu_limpio.isdigit():
            n = int(plu_limpio)
            for c in (str(n), str(n).zfill(len(plu_raw))):
                if c not in candidates:
                    candidates.append(c)

        query = (
            "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta, es_pesable, codigo "
            "FROM productos WHERE CAST(id AS CHAR) = ? OR codigo = ? LIMIT 1"
        )
        for c in candidates:
            rows = db_manager.execute_query(query, (c, c))
            if rows:
                return rows[0]
        return None

    @staticmethod
    def apagar_ofertas_sos_masivas():
        """Apaga todas las ofertas relámpago marcadas como SOS."""
        query = "UPDATE productos SET precio_oferta_relampago = 0 WHERE es_sos = 1"
        return db_manager.execute_non_query(query)

    @staticmethod
    def actualizar_precio_oferta_relampago(producto_id: str, nuevo_precio: float):
        """Actualiza la oferta relámpago de un producto específico."""
        query = "UPDATE productos SET precio_oferta_relampago = ? WHERE id = ?"
        return db_manager.execute_non_query(query, (nuevo_precio, producto_id))
