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


class CreditoInsuficiente(Exception):
    """El cupo ya no alcanza dentro de la misma transacción de la venta."""


def _texto_cargo(id_venta, fiado):
    texto = f"Venta a crédito Ticket #{id_venta}"
    quien = str((fiado or {}).get("excepcion") or "").strip()
    if quien:
        texto = f"{texto} (excepción {quien})"
    nota = str((fiado or {}).get("nota") or "").strip()
    if nota:
        texto = f"{texto} ({nota})"
    return texto


def _celda(row, clave, indice):
    if row is None:
        return None
    try:
        return row[clave]
    except Exception:
        try:
            return row[indice]
        except Exception:
            return None


def _aplicar_fiado(cursor, fiado, id_venta):
    cid = (fiado or {}).get("cliente_id")
    total = float((fiado or {}).get("total") or 0)
    if not cid:
        raise ValueError("Fiado sin cliente")
    bloqueo = " FOR UPDATE" if type(cursor).__name__ == "MariaDBCursorWrapper" else ""
    cursor.execute(
        f"SELECT deuda_actual, nombre, limite_credito FROM clientes WHERE id = ?{bloqueo}",
        (cid,),
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError("Cliente no encontrado")
    try:
        deuda = float(_celda(row, "deuda_actual", 0) or 0)
    except (TypeError, ValueError):
        deuda = 0.0
    nombre = _celda(row, "nombre", 1) or ""
    ya_vendido = bool((fiado or {}).get("ya_vendido"))
    excepcion = str((fiado or {}).get("excepcion") or "").strip()
    limite_raw = _celda(row, "limite_credito", 2)
    if not ya_vendido and not excepcion and limite_raw is not None:
        try:
            limite = float(limite_raw or 0)
        except (TypeError, ValueError):
            limite = None
        if limite is not None and total > (limite - deuda) + 0.01:
            raise CreditoInsuficiente("Crédito insuficiente")
    cursor.execute(
        "UPDATE clientes SET deuda_actual = COALESCE(deuda_actual, 0) + ? WHERE id = ?",
        (total, cid),
    )
    cursor.execute("SELECT deuda_actual, nombre FROM clientes WHERE id = ?", (cid,))
    row2 = cursor.fetchone()
    if row2:
        try:
            nueva = float(row2["deuda_actual"] or 0)
            nombre = row2["nombre"] or nombre
        except Exception:
            nueva = float(row2[0] or 0)
            nombre = row2[1] or nombre
    else:
        nueva = deuda + total
    cursor.execute(
        "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion, venta_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (cid, "CARGO", total, nueva, _texto_cargo(id_venta, fiado), id_venta),
    )
    return nombre


def _anular_cargo(cursor, id_venta):
    """Baja la deuda del ticket que se cancela. Si no hubo cargo, no toca la cuenta."""
    cursor.execute(
        "SELECT cliente_id, monto FROM cuenta_corriente "
        "WHERE venta_id = ? AND tipo = 'CARGO' ORDER BY id DESC LIMIT 1",
        (id_venta,),
    )
    cargo = cursor.fetchone()
    if not cargo:
        return
    cursor.execute(
        "SELECT id FROM cuenta_corriente WHERE venta_id = ? AND tipo = 'ANULACION' LIMIT 1",
        (id_venta,),
    )
    if cursor.fetchone():
        return
    cid = _celda(cargo, "cliente_id", 0)
    try:
        monto = float(_celda(cargo, "monto", 1) or 0)
    except (TypeError, ValueError):
        monto = 0.0
    if not cid or monto <= 0:
        return
    bloqueo = " FOR UPDATE" if type(cursor).__name__ == "MariaDBCursorWrapper" else ""
    cursor.execute(
        f"SELECT deuda_actual FROM clientes WHERE id = ?{bloqueo}",
        (cid,),
    )
    fila = cursor.fetchone()
    try:
        deuda = float(_celda(fila, "deuda_actual", 0) or 0)
    except (TypeError, ValueError):
        deuda = 0.0
    nueva = deuda - monto
    cursor.execute(
        "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
        (nueva, cid),
    )
    cursor.execute(
        "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion, venta_id) "
        "VALUES (?, 'ANULACION', ?, ?, ?, ?)",
        (cid, monto, nueva, f"Anulación Ticket #{id_venta}", id_venta),
    )


class VentasRepoMixin:
    def guardar_venta_completa(self, venta_data, items, fiado=None):
        """ Guarda la cabecera de venta y sus detalles en una sola transacción. """

        request_id = venta_data.get('request_id')
        if not request_id:
            request_id = str(uuid.uuid4())
            venta_data['request_id'] = request_id

        # Esclava: si ya hay MariaDB de la maestra, guardar ahí (misma BD).
        # La API LAN solo se usa si NO hay motor MariaDB y el puerto de la maestra sí responde.
        # Si la maestra no contesta, no se espera el timeout ni se cancela: se guarda en SQLite.
        if not self.is_master:
            from src.config import config
            mariadb_ok = (
                str(getattr(self, "db_engine_type", "")).lower() == "mariadb"
                and getattr(self, "mariadb_engine", None) is not None
            )
            api_url = str(config.get("api_url", "") or "").rstrip("/")
            host = self._host_tienda() if not mariadb_ok else ""
            maestra_viva = bool(host) and self._puerto_maestra_vivo(host)
            if api_url and not mariadb_ok and maestra_viva:
                try:
                    import requests
                    payload = {
                        "venta_data": venta_data,
                        "items": items,
                        "fiado": fiado,
                    }
                    from src.config import config
                    token = config.token_api_lan()
                    headers = {"Authorization": f"Bearer {token}"}
                    response = requests.post(f"{api_url}/api/guardar_venta", json=payload, headers=headers, timeout=5.0)
                    if response.status_code == 200:
                        res_data = response.json()
                        if res_data.get("status") == "success":
                            logger.info(f"Venta guardada remotamente vía API LAN (ID: {res_data.get('id_venta')})")
                            return res_data.get("id_venta")
                    logger.warning(f"Error del Servidor API LAN: HTTP {response.status_code}")
                except Exception as e:
                    logger.error(f"Fallo de conexión a la API LAN: {e}")
                    self._maestra_viva_hasta = 0.0
                if self._puerto_maestra_vivo(host):
                    logger.warning("Fallo en API LAN con la maestra en línea. Cancelando venta.")
                    return None
                logger.warning("La maestra dejó de responder. La venta se guarda en SQLite local.")
            elif api_url and not mariadb_ok and not maestra_viva:
                logger.warning("Maestra no responde. La venta se guarda en SQLite local.")

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
            usr_sec = venta_data.get("usuario_secundario") or ""
            vals_ext = (
                venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                usr_sec,
                venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0),
                venta_data.get('cliente_nombre', ''),
            )
            vals_base = (
                venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0),
                venta_data.get('cliente_nombre', ''),
            )
            try:
                cursor.execute("""
                    INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, usuario, usuario_secundario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre, request_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, vals_ext + (request_id,))
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
                err = str(e).lower()
                if "usuario_secundario" in err:
                    cursor.execute("""
                        INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre, request_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, vals_base + (request_id,))
                elif "request_id" in err:
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
                    from src.base_de_datos.repos.stock_descuento import descontar_stock
                    descontar_stock(cursor, it['id'], it['cant'])
                    try:
                        from src.base_de_datos.diario_ventas_externo import _anotar_medicion_stock

                        _anotar_medicion_stock(
                            {
                                "origen": "cobro",
                                "venta_id": id_venta,
                                "producto_id": it["id"],
                                "nombre": it.get("nombre") or "",
                                "cantidad": it.get("cant") or 0,
                                "ok": getattr(cursor, "rowcount", None) != 0,
                            }
                        )
                    except Exception:
                        pass

            if fiado:
                nombre_cli = _aplicar_fiado(cursor, fiado, id_venta)
                if nombre_cli:
                    venta_data["cliente_nombre"] = nombre_cli
                    try:
                        cursor.execute(
                            "UPDATE ventas SET cliente_nombre = ? WHERE id = ?",
                            (nombre_cli, id_venta),
                        )
                    except Exception:
                        pass

            conn.commit()
            if (
                not self.is_master
                and self._host_tienda()
                and getattr(self, "db_engine_type", "sqlite") != "mariadb"
            ):
                try:
                    from src.base_de_datos.offline_sync import offline_sync_manager
                    offline_sync_manager.guardar_venta_offline(venta_data, items, fiado=fiado)
                except Exception as e_off:
                    logger.warning(f"Venta local guardada; no se pudo encolar para la maestra: {e_off}")
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
            from src.base_de_datos.repos.stock_descuento import SinStock
            if isinstance(e, (SinStock, CreditoInsuficiente)):
                raise
            return None
        finally:
            if conn: conn.close()

    def sync_venta_to_master(self, venta_data, items, fiado=None):
        """Intenta guardar una venta offline en la base de datos principal sin fallback."""
        if getattr(self, "db_engine_type", "sqlite") != "mariadb" or not getattr(self, "mariadb_engine", None):
            return False
        if getattr(self, "_forced_local_offline", False):
            return False
        conn = None
        request_id = (venta_data or {}).get("request_id")
        try:
            conn = self.get_connection(caer_si_maestra_caida=False)
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
                if "request_id" in str(e).lower():
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
                    from src.base_de_datos.repos.stock_descuento import descontar_stock
                    descontar_stock(cursor, it.get('id'), it.get('cant', 1))

            if fiado:
                datos_fiado = dict(fiado)
                datos_fiado["ya_vendido"] = True
                _aplicar_fiado(cursor, datos_fiado, id_venta)

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

            _anular_cargo(cursor, id_venta)

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


