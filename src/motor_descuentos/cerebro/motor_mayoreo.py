# motor_mayoreo.py - Módulo dedicado a la lógica de precios por volumen (mayoreo)
import logging

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class MotorMayoreo:
    """
    Motor específico para lógica de precios por volumen (mayoreo).
    Se activa cuando la cantidad del producto supera `cant_mayoreo`.
    Separado del motor de ofertas para mayor claridad y rendimiento.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calcular_precio(self, precio_base: float, cant_mayoreo: float,
                        precio_mayoreo: float, cantidad: float) -> tuple[float, float, bool]:
        """
        Calcula el precio final considerando el escalón de mayoreo.
        Returns: (precio_final, descuento_total, es_mayoreo)
        """
        if cant_mayoreo > 0 and precio_mayoreo > 0 and cantidad >= cant_mayoreo:
            descuento = (precio_base - precio_mayoreo) * cantidad
            return precio_mayoreo, descuento, True
        return precio_base, 0.0, False

    def obtener_config_mayoreo(self, id_producto: str) -> dict:
        """
        Obtiene la configuración de mayoreo de un producto desde la BD.
        Returns: {'cant_mayoreo': float, 'precio_mayoreo': float}
        """
        try:
            res = db_manager.execute_query(
                "SELECT cant_mayoreo, precio_mayoreo FROM productos WHERE id=?",
                (id_producto,)
            )
            if res:
                return {
                    'cant_mayoreo': float(res[0]['cant_mayoreo'] or 0.0),
                    'precio_mayoreo': float(res[0]['precio_mayoreo'] or 0.0)
                }
        except Exception as e:
            self.logger.error(f"Error obteniendo config mayoreo para {id_producto}: {e}")
        return {'cant_mayoreo': 0.0, 'precio_mayoreo': 0.0}

    def actualizar_mayoreo(self, id_producto: str, cant_mayoreo: float,
                           precio_mayoreo: float) -> bool:
        """Guarda la configuración de mayoreo de un producto."""
        try:
            return db_manager.execute_non_query(
                "UPDATE productos SET cant_mayoreo=?, precio_mayoreo=? WHERE id=?",
                (cant_mayoreo, precio_mayoreo, id_producto)
            )
        except Exception as e:
            self.logger.error(f"Error actualizando mayoreo del producto {id_producto}: {e}")
            return False

    def obtener_productos_con_mayoreo(self) -> list:
        """Obtiene todos los productos que tienen precio mayoreo configurado."""
        try:
            return db_manager.execute_query(
                "SELECT * FROM productos WHERE cant_mayoreo > 0 AND precio_mayoreo > 0 ORDER BY nombre"
            ) or []
        except Exception as e:
            self.logger.error(f"Error obteniendo productos con mayoreo: {e}")
            return []
