from typing import List, Tuple, Any, Optional
import sqlite3
import os
import sys
import uuid
from src.logger import logger


def _id_fila(row):
    if row is None:
        return None
    try:
        return row["id"]
    except Exception:
        return row[0]


def _buscar_por_request(cursor, request_id):
    if not request_id:
        return None
    try:
        cursor.execute("SELECT id FROM ventas WHERE request_id = ?", (request_id,))
        return _id_fila(cursor.fetchone())
    except Exception:
        return None


def _es_duplicado(err) -> bool:
    msg = str(err or "").lower()
    return "unique" in msg or "duplicate" in msg or "idx_ventas_request_id" in msg


class VentasRepoMixin:
    def guardar_venta_completa(self, venta_data, items):
        """ Guarda la cabecera de venta y sus detalles en una sola transacción. """
        
        request_id = venta_data.get('request_id')
        if not request_id:
            request_id = str(uuid.uuid4())
            venta_data['request_id'] = request_id

        # Esclava: si ya hay MariaDB de la maestra, guardar ahí (misma BD).
        # La API LAN solo se usa si NO hay motor MariaDB (offline / mal cableada).
        if not self.is_master:
            from src.config import config
            mariadb_ok = (
                str(getattr(self, "db_engine_type", "")).lower() == "mariadb"
                and getattr(self, "mariadb_engine", None) is not None
            )
            api_url = str(config.get("api_url", "") or "").rstrip("/")
            if api_url and not mariadb_ok:
                try:
                    import requests
                    payload = {
                        "venta_data": venta_data,
                        "items": items
                    }
                    response = requests.post(f"{api_url}/api/guardar_venta", json=payload, timeout=5.0)
                    if response.status_code == 200:
                        res_data = response.json()
                        if res_data.get("status") == "success":
                            logger.info(f"Venta guardada remotamente vía API LAN (ID: {res_data.get('id_venta')})")
                            return res_data.get("id_venta")
                    logger.warning(f"Error del Servidor API LAN: HTTP {response.status_code}")
                except Exception as e:
                    logger.error(f"Fallo de conexión a la API LAN: {e}")
                logger.warning("Fallo en API LAN y sin MariaDB de maestra. Cancelando venta.")
                return None

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            existente = _buscar_por_request(cursor, request_id)
            if existente:
                logger.info(f"Venta ignorada por idempotencia (request_id: {request_id})")
                return existente
            
            from datetime import datetime
            fecha_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            from src.config import config
            c_id = config.get("caja_id", 1)
            vals_base = (
                venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0),
                venta_data.get('cliente_nombre', ''),
            )
            try:
                cursor.execute("""
                    INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre, request_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, vals_base + (request_id,))
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    cursor = conn.cursor()
                if _es_duplicado(e):
                    existente = _buscar_por_request(cursor, request_id)
                    if existente:
                        return existente
                if "request_id" in str(e).lower() or "unknown column" in str(e).lower():
                    cursor.execute("""
                        INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, vals_base)
                else:
                    raise
            
            id_venta = cursor.lastrowid
            
            for it in items:
                cursor.execute("""
                    INSERT INTO detalles_ventas (id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_venta, it['id'], it['nombre'], it['cant'], it['precio'], it['subtotal']))
                
                if it['id'] and str(it['id']).strip() not in ('000', ''):
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (it['cant'], it['id']))
            
            conn.commit()
            return id_venta
        except Exception as e:
            if conn: conn.rollback()
            existente = None
            try:
                if conn:
                    existente = _buscar_por_request(conn.cursor(), request_id)
            except Exception:
                existente = None
            if existente:
                return existente
            logger.warning(f"Error al guardar venta en base de datos: {e}")
            return None
        finally:
            if conn: conn.close()

    def sync_venta_to_master(self, venta_data, items):
        """Intenta guardar una venta offline en la base de datos principal sin fallback."""
        conn = None
        request_id = (venta_data or {}).get("request_id")
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if request_id and _buscar_por_request(cursor, request_id):
                return True
            
            from datetime import datetime
            fecha_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c_id = venta_data.get('caja_id', 1)
            vals = (
                venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0),
                venta_data.get('cliente_nombre', ''),
            )
            try:
                cursor.execute("""
                    INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, 
                                       usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre, request_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, vals + (request_id,))
            except Exception as e:
                if request_id and _es_duplicado(e):
                    if conn:
                        conn.rollback()
                    return True
                if "request_id" in str(e).lower() or "unknown column" in str(e).lower():
                    cursor.execute("""
                        INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, 
                                           usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, vals)
                else:
                    raise
            id_venta = cursor.lastrowid
            
            for it in items:
                cursor.execute("""
                    INSERT INTO detalles_ventas (id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_venta, it.get('id', ''), it.get('nombre', ''), it.get('cant', 1), it.get('precio', 0), it.get('subtotal', 0)))
                
                if it.get('id') and str(it['id']).strip() not in ('000', ''):
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (it.get('cant', 1), it.get('id')))
            
            conn.commit()
            return True
        except Exception as e:
            if conn: conn.rollback()
            if request_id:
                try:
                    if conn and _buscar_por_request(conn.cursor(), request_id):
                        return True
                except Exception:
                    pass
            logger.warning(f"Fallo en sync_venta_to_master: {e}")
            return False
        finally:
            if conn: conn.close()

    def cancelar_venta_transaccional(self, id_venta: int, username: str) -> bool:
        """
        Cancela una venta de forma transaccional y devuelve stock
        (excepto el artículo común '000'). El esperado de caja se corrige solo
        al excluir la venta CANCELADA del SUM (sin RETIRO duplicado).
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT estado, caja_id, usuario, total FROM ventas WHERE id = ?",
                (id_venta,),
            )
            venta = cursor.fetchone()
            if not venta:
                logger.error(f"Venta {id_venta} no encontrada para cancelar.")
                return False
                
            estado = venta['estado']
            if estado == 'CANCELADA':
                logger.warning(f"Venta {id_venta} ya está cancelada.")
                return True

            from datetime import datetime
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            caja_accion = 1
            perfil = "desconocido"
            try:
                from src.config import config
                caja_accion = int(config.get("caja_id", 1) or 1)
                perfil = getattr(config, "current_role", None) or "desconocido"
            except Exception:
                pass
            caja_origen = venta["caja_id"] if "caja_id" in venta.keys() else 1
            usuario_venta = venta["usuario"] if "usuario" in venta.keys() else ""
            monto = float(venta["total"] or 0) if "total" in venta.keys() else 0.0
                
            cursor.execute("SELECT id_producto, cantidad FROM detalles_ventas WHERE id_venta = ?", (id_venta,))
            detalles = cursor.fetchall()
            for det in detalles:
                prod_id = det['id_producto']
                if prod_id and str(prod_id).strip() not in ('000', ''):
                    cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (det['cantidad'], prod_id))
            
            try:
                cursor.execute(
                    """UPDATE ventas SET estado = 'CANCELADA',
                       cancelado_por = ?, fecha_cancel = ?, perfil_cancel = ?, caja_cancel = ?
                       WHERE id = ?""",
                    (username or "—", ahora, str(perfil), caja_accion, id_venta),
                )
            except Exception:
                cursor.execute("UPDATE ventas SET estado = 'CANCELADA' WHERE id = ?", (id_venta,))
            try:
                cursor.execute(
                    """INSERT INTO auditoria_cancelaciones
                       (id_venta, fecha, usuario, perfil, caja_origen, caja_accion, monto, usuario_venta)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (id_venta, ahora, username or "—", str(perfil), caja_origen, caja_accion, monto, usuario_venta),
                )
            except Exception as e:
                logger.warning(f"Auditoría de cancelación no grabada (ticket {id_venta}): {e}")

            conn.commit()
            return True
        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"Error transaccional al cancelar venta {id_venta}: {e}")
            return False
        finally:
            if conn: conn.close()


