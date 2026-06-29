from src.base_de_datos.database import db_manager
from src.config import config


FIADO_EXPRESS_LIMITE_DEFAULT = 20000.0


class ClienteRepository:
    """
    Capa de acceso a datos para la tabla 'clientes'.
    Aísla las consultas SQL de la Interfaz Gráfica.
    """

    @staticmethod
    def _limite_express_default() -> float:
        return float(config.get("fiado_express_limite", FIADO_EXPRESS_LIMITE_DEFAULT))

    @staticmethod
    def limite_credito_excedido(cliente: dict, monto_venta: float) -> bool:
        """True si la venta supera el crédito disponible (dispara alarma en mostrador)."""
        return monto_venta > ClienteRepository.credito_disponible(cliente) + 0.01

    @staticmethod
    def obtener_clientes_con_deuda() -> list:
        """Clientes con deuda activa, ordenados alfabéticamente."""
        query = (
            "SELECT id, nombre, deuda_actual FROM clientes "
            "WHERE deuda_actual > 0 ORDER BY nombre ASC"
        )
        return db_manager.execute_query(query)

    @staticmethod
    def obtener_por_id(cliente_id) -> dict:
        """Devuelve un cliente por su ID o None si no existe."""
        query = "SELECT * FROM clientes WHERE id = ?"
        resultados = db_manager.execute_query(query, (cliente_id,))
        return resultados[0] if resultados else None

    @staticmethod
    def buscar_por_dni(dni: str):
        """Busca cliente por DNI/documento. Retorna dict o None."""
        dni = (dni or "").strip()
        if not dni:
            return None
        rows = db_manager.execute_query(
            "SELECT id, nombre, limite_credito, deuda_actual, dni, tipo_cliente "
            "FROM clientes WHERE dni = ?",
            (dni,),
        )
        return rows[0] if rows else None

    @staticmethod
    def normalizar_dni(dni: str) -> str:
        dni = (dni or "").strip().replace(".", "").replace("-", "").replace(" ", "")
        if not dni or not dni.isdigit() or len(dni) < 7:
            return ""
        return dni

    @staticmethod
    def verificar_y_crear_cliente(dni: str):
        """
        Fiado Express: identifica por DNI o crea perfil 'Express [DNI]'.
        Retorna (cliente_dict | None, estado_str, mensaje_ui).
        estado: 'identificado' | 'creado' | 'error'
        """
        dni = ClienteRepository.normalizar_dni(dni)
        if not dni:
            return None, "error", "DNI inválido (mínimo 7 dígitos)"

        existente = ClienteRepository.buscar_por_dni(dni)
        if existente:
            return existente, "identificado", existente["nombre"]

        limite = ClienteRepository._limite_express_default()
        nombre = f"Express {dni}"
        ok = db_manager.execute_non_query(
            "INSERT INTO clientes (nombre, telefono, limite_credito, deuda_actual, dni, tipo_cliente) "
            "VALUES (?, ?, ?, 0, ?, 'express')",
            (nombre, None, limite, dni),
        )
        if not ok:
            return None, "error", "No se pudo crear el cliente Express"

        creado = ClienteRepository.buscar_por_dni(dni)
        if not creado:
            return None, "error", "Cliente creado pero no se pudo recuperar"
        return creado, "creado", f"Cliente creado: {nombre}"

    @staticmethod
    def credito_disponible(cliente: dict) -> float:
        c_dict = dict(cliente) if hasattr(cliente, "keys") else cliente
        return float(c_dict.get("limite_credito", 0)) - float(c_dict.get("deuda_actual", 0))
