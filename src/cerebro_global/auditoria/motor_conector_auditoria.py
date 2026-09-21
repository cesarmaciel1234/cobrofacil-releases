"""
Conector entre la UI de auditoría y el inventario.
El stock se ajusta con SET (conteo físico). El log no vuelve a escribir stock.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("MotorConectorAuditoria")


class MotorConectorAuditoria:
    def __init__(self):
        self._motor_inventario = None
        self._db_manager = None
        self._cache_productos = {}
        self._cache_timestamp = None
        self._cache_duration = 15

    def _obtener_motor_inventario(self):
        if self._motor_inventario is None:
            try:
                from src.motor_inventario.motor_catalogo import MotorCatalogo
                self._motor_inventario = MotorCatalogo()
            except Exception as e:
                logger.error(f"Error cargando MotorCatalogo: {e}")
                self._motor_inventario = None
        return self._motor_inventario

    def _obtener_db_manager(self):
        if self._db_manager is None:
            try:
                from src.base_de_datos.database import db_manager
                self._db_manager = db_manager
            except Exception as e:
                logger.error(f"Error cargando db_manager: {e}")
                self._db_manager = None
        return self._db_manager

    def invalidar_cache(self):
        self._cache_productos = {}
        self._cache_timestamp = None

    def _validar_cache(self):
        if self._cache_timestamp is None:
            return False
        edad = (datetime.now() - self._cache_timestamp).total_seconds()
        return edad < self._cache_duration

    def _fila_auditoria(self, prod: dict) -> dict:
        unidad = str(prod.get("unidad") or "UN").strip()
        pesable = prod.get("es_pesable")
        if pesable in (None, ""):
            pesable = unidad.upper() in ("KG", "KILO", "KILOS")
        return {
            "id": prod.get("id"),
            "codigo": prod.get("codigo", "") or "",
            "nombre": prod.get("nombre", "") or "",
            "departamento": prod.get("departamento") or "GENERAL",
            "stock": float(prod.get("stock") or 0.0),
            "precio": float(prod.get("precio") or 0.0),
            "unidad": unidad,
            "es_pesable": bool(pesable),
        }

    def _actualizar_cache(self):
        db = self._obtener_db_manager()
        if db:
            try:
                from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
                productos = MotorAuditoria.obtener_inventario(db)
                self._cache_productos = {}
                for prod in productos:
                    fila = self._fila_auditoria(prod)
                    self._cache_productos[fila["id"]] = fila
                self._cache_timestamp = datetime.now()
                return True
            except Exception as e:
                logger.error(f"Error actualizando caché vía MotorAuditoria: {e}")

        motor = self._obtener_motor_inventario()
        if not motor:
            return False
        try:
            productos, _ = motor.obtener_productos(limite=10000)
            self._cache_productos = {}
            for prod in productos:
                fila = self._fila_auditoria(prod)
                self._cache_productos[fila["id"]] = fila
            self._cache_timestamp = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error actualizando caché: {e}")
            return False

    def obtener_inventario_para_auditoria(self, forzar_actualizacion=False) -> List[Dict]:
        if forzar_actualizacion or not self._validar_cache():
            if not self._actualizar_cache():
                return []
        return list(self._cache_productos.values())

    def buscar_producto_por_codigo(self, codigo: str) -> Optional[Dict]:
        motor = self._obtener_motor_inventario()
        if not motor:
            return None
        try:
            producto = motor.obtener_producto_por_codigo(codigo)
            if producto:
                return self._fila_auditoria(producto)
        except Exception as e:
            logger.error(f"Error buscando código {codigo}: {e}")
        return None

    def buscar_producto_por_id(self, producto_id: int) -> Optional[Dict]:
        motor = self._obtener_motor_inventario()
        if not motor:
            return None
        try:
            producto = motor.obtener_producto_por_id(producto_id)
            if producto:
                return self._fila_auditoria(producto)
        except Exception as e:
            logger.error(f"Error buscando ID {producto_id}: {e}")
        return None

    def solicitar_ajuste_stock(
        self, producto_id: int, stock_nuevo: float, usuario: str, motivo: str = ""
    ) -> Tuple[bool, str]:
        db = self._obtener_db_manager()
        if not db:
            return False, "Base de datos no disponible"
        if stock_nuevo < 0:
            return False, "El stock no puede ser negativo"

        from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria

        producto = self.buscar_producto_por_id(producto_id)
        if not producto:
            return False, f"Producto ID {producto_id} no encontrado"

        stock_anterior = float(producto.get("stock") or 0.0)
        diferencia = float(stock_nuevo) - stock_anterior
        if abs(diferencia) < 1e-9:
            return True, "Sin cambio"

        ajuste = {
            "id": producto_id,
            "nombre": producto.get("nombre", ""),
            "stock_sistema": stock_anterior,
            "stock_fisico": float(stock_nuevo),
            "diferencia": diferencia,
        }

        if not MotorAuditoria.aplicar_ajuste_stock(db, producto_id, float(stock_nuevo)):
            return False, "No se pudo actualizar el stock"

        MotorAuditoria.registrar_ajuste(db, ajuste, usuario, motivo)
        self.invalidar_cache()
        try:
            from src.cerebro_global.motor_global import invalidar_catalogo
            invalidar_catalogo()
        except Exception:
            pass
        return True, "Ajuste aplicado correctamente"

    def aplicar_lote_ajustes(self, ajustes: List[Dict], usuario: str, motivo: str = "") -> Tuple[bool, List[str]]:
        errores = []
        for ajuste in ajustes:
            exito, mensaje = self.solicitar_ajuste_stock(
                ajuste["id"],
                ajuste["stock_fisico"],
                usuario,
                motivo or f"Ajuste de auditoría. Diferencia: {ajuste.get('diferencia', 0):.2f}",
            )
            if not exito:
                errores.append(f"{ajuste.get('nombre', ajuste['id'])}: {mensaje}")
        self.invalidar_cache()
        return (len(errores) == 0), errores

    def obtener_historial_ajustes(self, producto_id: Optional[int] = None, codigo: Optional[str] = None) -> List[Dict]:
        db = self._obtener_db_manager()
        if not db:
            return []
        from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
        return MotorAuditoria.obtener_historial_ajustes(db, producto_id=producto_id, codigo=codigo)

    def verificar_integridad(self) -> Dict:
        return {
            "motor_inventario_disponible": self._obtener_motor_inventario() is not None,
            "db_manager_disponible": self._obtener_db_manager() is not None,
            "cache_valido": self._validar_cache(),
            "productos_en_cache": len(self._cache_productos),
            "ultimo_actualizacion": self._cache_timestamp,
        }


_conector_global = None


def obtener_conector_auditoria() -> MotorConectorAuditoria:
    global _conector_global
    if _conector_global is None:
        _conector_global = MotorConectorAuditoria()
    return _conector_global
