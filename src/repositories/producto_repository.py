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
    def apagar_ofertas_sos_masivas():
        """Apaga todas las ofertas relámpago marcadas como SOS."""
        query = "UPDATE productos SET precio_oferta_relampago = 0 WHERE es_sos = 1"
        return db_manager.execute_non_query(query)

    @staticmethod
    def actualizar_precio_oferta_relampago(producto_id: str, nuevo_precio: float):
        """Actualiza la oferta relámpago de un producto específico."""
        query = "UPDATE productos SET precio_oferta_relampago = ? WHERE id = ?"
        return db_manager.execute_non_query(query, (nuevo_precio, producto_id))
