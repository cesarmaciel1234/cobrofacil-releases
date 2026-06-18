from src.base_de_datos.database import db_manager

class ClienteRepository:
    """
    Capa de acceso a datos para la tabla 'clientes'.
    Aísla las consultas SQL de la Interfaz Gráfica.
    """
    
    @staticmethod
    def obtener_clientes_con_deuda() -> list:
        """
        Devuelve una lista de clientes que tienen deuda activa,
        ordenados alfabéticamente.
        """
        query = "SELECT id, nombre, deuda_actual FROM clientes WHERE deuda_actual > 0 ORDER BY nombre ASC"
        return db_manager.execute_query(query)

    @staticmethod
    def obtener_por_id(cliente_id: str) -> dict:
        """Devuelve un cliente por su ID o None si no existe."""
        query = "SELECT * FROM clientes WHERE id = ?"
        resultados = db_manager.execute_query(query, (cliente_id,))
        return resultados[0] if resultados else None
