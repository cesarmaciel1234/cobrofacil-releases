# motor_mayoreo.py — Mayoreo global (Inventario admin + Promedios jefe)
import logging

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class MotorMayoreo:
    """
    Umbral de volumen: desde `cant_mayoreo` → `precio_mayoreo`.
    Lo usan Inventario (admin) y Promedios (jefe). No es oferta de cartelería.
    """

    def __init__(self, db=None):
        self.logger = logging.getLogger(__name__)
        self.db = db or db_manager

    def calcular_precio(self, precio_base: float, cant_mayoreo: float,
                        precio_mayoreo: float, cantidad: float) -> tuple[float, float, bool]:
        if cant_mayoreo > 0 and precio_mayoreo > 0 and cantidad >= cant_mayoreo:
            descuento = (precio_base - precio_mayoreo) * cantidad
            return precio_mayoreo, descuento, True
        return precio_base, 0.0, False

    def obtener_config_mayoreo(self, id_producto: str) -> dict:
        try:
            res = self.db.execute_query(
                "SELECT cant_mayoreo, precio_mayoreo FROM productos WHERE id=?",
                (id_producto,),
            )
            if res:
                return {
                    "cant_mayoreo": float(res[0]["cant_mayoreo"] or 0.0),
                    "precio_mayoreo": float(res[0]["precio_mayoreo"] or 0.0),
                }
        except Exception as e:
            self.logger.error(f"Error obteniendo config mayoreo para {id_producto}: {e}")
        return {"cant_mayoreo": 0.0, "precio_mayoreo": 0.0}

    def obtener_por_nombre(self, nombre: str) -> dict:
        try:
            res = self.db.execute_query(
                "SELECT id, precio, costo, cant_mayoreo, precio_mayoreo FROM productos WHERE nombre=?",
                (nombre,),
            )
            if res:
                r = res[0]
                return {
                    "id": r["id"],
                    "precio": float(r["precio"] or 0.0),
                    "costo": float(r.get("costo") or 0.0),
                    "cant_mayoreo": float(r["cant_mayoreo"] or 0.0),
                    "precio_mayoreo": float(r["precio_mayoreo"] or 0.0),
                }
        except Exception as e:
            self.logger.error(f"Error mayoreo por nombre ({nombre}): {e}")
        return {
            "id": None, "precio": 0.0, "costo": 0.0,
            "cant_mayoreo": 0.0, "precio_mayoreo": 0.0,
        }

    def actualizar_mayoreo(self, id_producto: str, cant_mayoreo: float,
                           precio_mayoreo: float) -> bool:
        try:
            return bool(self.db.execute_non_query(
                "UPDATE productos SET cant_mayoreo=?, precio_mayoreo=? WHERE id=?",
                (cant_mayoreo, precio_mayoreo, id_producto),
            ))
        except Exception as e:
            self.logger.error(f"Error actualizando mayoreo del producto {id_producto}: {e}")
            return False

    def aplicar_desde_promedios(
        self,
        nombre: str,
        precio: float,
        costo: float,
        cant_mayoreo: float,
        precio_mayoreo: float,
        categoria: str = "",
    ) -> bool:
        """
        Escritura desde jefe → promedios. Precio/costo + mayoreo.
        No toca cant_oferta / precio_oferta (cartelería = Ofertas).
        """
        nombre = (nombre or "").strip()
        if not nombre:
            return False
        if precio <= 0 and precio_mayoreo <= 0:
            return False
        try:
            res = self.db.execute_query("SELECT id FROM productos WHERE nombre=?", (nombre,))
            if res:
                return bool(self.db.execute_non_query(
                    "UPDATE productos SET precio=?, costo=?, cant_mayoreo=?, precio_mayoreo=? WHERE nombre=?",
                    (precio, costo, cant_mayoreo, precio_mayoreo, nombre),
                ))
            import random
            cod = f"PROM-{random.randint(1000, 9999)}"
            return bool(self.db.execute_non_query(
                "INSERT INTO productos (nombre, precio, cant_mayoreo, precio_mayoreo, "
                "categoria, unidad, codigo, es_pesable, costo) "
                "VALUES (?, ?, ?, ?, ?, 'KG', ?, 1, ?)",
                (nombre, precio, cant_mayoreo, precio_mayoreo, (categoria or "").upper(), cod, costo),
            ))
        except Exception as e:
            self.logger.error(f"Error aplicando mayoreo desde promedios ({nombre}): {e}")
            return False

    def obtener_productos_con_mayoreo(self) -> list:
        try:
            return self.db.execute_query(
                "SELECT * FROM productos WHERE cant_mayoreo > 0 AND precio_mayoreo > 0 ORDER BY nombre"
            ) or []
        except Exception as e:
            self.logger.error(f"Error obteniendo productos con mayoreo: {e}")
            return []
