from typing import List, Tuple, Any, Optional
import sqlite3
import os
import sys
from src.logger import logger

class VentasRepoMixin:
    def guardar_venta_completa(self, venta_data, items):
        """ Guarda la cabecera de venta y sus detalles en una sola transacción. """
        
        # Intercept for LAN API (Nivel 2)
        if not self.is_master:
            from src.config import config
            api_url = config.get("api_url", "")
            if api_url:
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
                
                # If API fails, fall back to offline sync (it acts like network drop)
                logger.warning("Fallo en API LAN detectado. Guardando offline.")
                try:
                    from src.base_de_datos.offline_sync import offline_sync_manager
                    offline_sync_manager.guardar_venta_offline(venta_data, items)
                    return 9999999
                except Exception as ex:
                    logger.error(f"Fallo crítico offline tras error API: {ex}")
                    return None

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Generar la hora local real en Python en lugar de usar CURRENT_TIMESTAMP de SQLite (que es UTC)
            from datetime import datetime
            fecha_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 1. Insertar Cabecera
            from src.config import config
            c_id = config.get("caja_id", 1)
            cursor.execute("""
                INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0),
                venta_data.get('cliente_nombre', '')
            ))
            
            id_venta = cursor.lastrowid
            
            # 2. Insertar Detalles y Actualizar Stock
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
            # Derivar al Buffer Offline si falla la conexión a la base de datos de red
            logger.warning(f"Fallo de red detectado al guardar venta. Guardando offline: {e}")
            try:
                from src.base_de_datos.offline_sync import offline_sync_manager
                offline_sync_manager.guardar_venta_offline(venta_data, items)
                return 9999999 # Retornar un ID falso para simular éxito en la UI
            except Exception as ex:
                logger.error(f"Fallo crítico: No se pudo guardar ni online ni offline: {ex}")
                return None
        finally:
            if conn: conn.close()

    def sync_venta_to_master(self, venta_data, items):
        """Intenta guardar una venta offline en la base de datos principal sin fallback."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            from datetime import datetime
            fecha_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c_id = venta_data.get('caja_id', 1)
            
            cursor.execute("""
                INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, 
                                   usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0),
                venta_data.get('cliente_nombre', '')
            ))
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
                    cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ? OR codigo = ?", (det['cantidad'], prod_id, prod_id))
            
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


