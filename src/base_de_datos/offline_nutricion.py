"""
offline_nutricion.py - Gestor de Nutrición y Outbox Offline para Nodo Portable / Esclavo.

Permite al dueño del negocio trabajar con su notebook en su casa desconectado de la red:
1. Cargar stock y recepciones de mercadería con escáner.
2. Modificar precios, ofertas y catálogo.
3. Editar clientes, plazos, límites de crédito y fiado express.
4. Dar de alta un proveedor y enlazarle productos o departamentos.

Al regresar al negocio y reconectar a la red ("oler el WiFi de la tienda"):
- Nutre a la Maestra (Upload): Vuelca precios, stock, recepciones, clientes,
  proveedores y sus enlaces a MariaDB. El id del proveedor nace ahí, no en casa.
- Nutre a la Notebook (Download): La Maestra replica su catálogo consolidado y transacciones
  recientes a SQLite para la siguiente jornada.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any

from src.utils.paths import get_base_path

logger = logging.getLogger("OfflineNutricion")


class OfflineNutricionManager:
    """Administra la cola de cambios de negocio realizados sin conexión a la PC Maestra."""

    def __init__(self):
        self.base_path = get_base_path()
        self.outbox_file = os.path.join(self.base_path, "offline_cambios.json")
        self._lock = threading.RLock()
        self._ensure_file()

    def _ensure_file(self):
        with self._lock:
            if not os.path.exists(self.outbox_file):
                try:
                    with open(self.outbox_file, "w", encoding="utf-8") as f:
                        json.dump({
                            "productos": [], "recepciones": [], "clientes": [],
                            "proveedores": [], "vinculos": [],
                        }, f, indent=4)
                except Exception as e:
                    logger.error(f"Error creando offline_cambios.json: {e}")

    def _leer_cola(self) -> dict:
        try:
            if not os.path.exists(self.outbox_file):
                return self._cola_vacia()
            with open(self.outbox_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._normalizar_cola(data)
        except Exception as e:
            logger.error(f"Error leyendo outbox offline_cambios: {e}")
            return self._cola_vacia()

    @staticmethod
    def _cola_vacia() -> dict:
        return {
            "productos": [], "recepciones": [], "clientes": [],
            "proveedores": [], "vinculos": [],
        }

    @classmethod
    def _normalizar_cola(cls, data) -> dict:
        if not isinstance(data, dict):
            data = {}
        for clave in cls._cola_vacia():
            if not isinstance(data.get(clave), list):
                data[clave] = []
        return data

    def _escribir_cola(self, data: dict):
        try:
            temp_file = self.outbox_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, self.outbox_file)
        except Exception as e:
            logger.error(f"Error escribiendo outbox offline_cambios: {e}")

    def encolar_producto(self, datos: dict) -> bool:
        """Encola la creación o modificación de un producto realizada fuera de línea."""
        if not datos:
            return False
        with self._lock:
            cola = self._leer_cola()
            registro = {
                "id": datos.get("id"),
                "codigo": datos.get("codigo"),
                "nombre": datos.get("nombre"),
                "datos": dict(datos),
                "timestamp": time.time(),
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # Evitar duplicados consecutivos para el mismo producto: actualizar si ya existe en cola
            actualizado = False
            for p in cola["productos"]:
                if (registro["id"] and p.get("id") == registro["id"]) or (
                    registro["codigo"] and p.get("codigo") == registro["codigo"]
                ):
                    p["baja"] = False
                    p["datos"].update(registro["datos"])
                    p["id"] = registro["id"] or p.get("id")
                    p["codigo"] = registro["codigo"] or p.get("codigo")
                    p["timestamp"] = registro["timestamp"]
                    p["fecha"] = registro["fecha"]
                    actualizado = True
                    break
            if not actualizado:
                cola["productos"].append(registro)

            self._escribir_cola(cola)
            logger.info(f"📦 Producto '{datos.get('nombre')}' encolado en buffer offline para nutrir Maestra.")
            return True

    def encolar_baja_producto(self, producto_id, codigo="", nombre="") -> bool:
        """El producto se fue. En casa la copia lo esconde y en la tienda se borra."""
        ident = str(producto_id or "").strip()
        codigo = str(codigo or "").strip()
        if not ident and not codigo:
            return False
        with self._lock:
            cola = self._leer_cola()
            registro = {
                "id": ident or None,
                "codigo": codigo or None,
                "nombre": nombre,
                "baja": True,
                "datos": {"id": ident or None, "codigo": codigo or None, "nombre": nombre},
                "timestamp": time.time(),
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            nuevo = []
            puesto = False
            for p in cola.get("productos") or []:
                mismo_id = ident and str(p.get("id") or "") == ident
                if mismo_id:
                    if not puesto:
                        nuevo.append(registro)
                        puesto = True
                    continue
                nuevo.append(p)
            if not puesto:
                nuevo.append(registro)
            cola["productos"] = nuevo
            self._escribir_cola(cola)
            return True

    def encolar_recepcion(
        self, proveedor: str, items: list, total_bultos: float,
        total_monto: float, condicion_pago: str = "A Pagar", perfil: str = "admin",
        fecha: str = "",
    ) -> bool:
        """Encola una recepción de mercadería (escaneo de remito/bultos) efectuada offline."""
        if not items:
            return False
        with self._lock:
            cola = self._leer_cola()
            registro = {
                "proveedor": proveedor,
                "items": items,
                "total_bultos": float(total_bultos),
                "total_monto": float(total_monto),
                "condicion_pago": condicion_pago,
                "perfil": perfil,
                "timestamp": time.time(),
                "fecha": (fecha or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            cola["recepciones"].append(registro)
            self._escribir_cola(cola)
            logger.info(f"🚚 Recepción de {proveedor} (${total_monto:,.2f}) encolada en buffer offline.")
            return True

    def encolar_cliente(self, accion: str, datos: dict) -> bool:
        """Encola un alta o modificación de cliente realizada offline."""
        if not datos:
            return False
        with self._lock:
            cola = self._leer_cola()
            registro = {
                "accion": accion.upper(),  # 'ALTA' o 'EDICION'
                "datos": dict(datos),
                "timestamp": time.time(),
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            cola["clientes"].append(registro)
            self._escribir_cola(cola)
            logger.info(f"👤 Cliente evento {accion} encolado en buffer offline.")
            return True

    def encolar_proveedor(self, nombre: str, telefono: str = "") -> bool:
        """Deja el alta de un proveedor para cuando la notebook vuelva a la tienda."""
        nombre = (nombre or "").strip()
        telefono = (telefono or "").strip()
        if not nombre:
            return False
        with self._lock:
            cola = self._leer_cola()
            ahora = time.time()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for ficha in cola["proveedores"]:
                if str(ficha.get("nombre") or "").strip().upper() == nombre.upper():
                    if telefono:
                        ficha["telefono"] = telefono
                    ficha["timestamp"] = ahora
                    ficha["fecha"] = fecha
                    self._escribir_cola(cola)
                    return True
            cola["proveedores"].append({
                "nombre": nombre,
                "telefono": telefono,
                "timestamp": ahora,
                "fecha": fecha,
            })
            self._escribir_cola(cola)
            logger.info(f"Proveedor '{nombre}' encolado para crear el id en la tienda.")
            return True

    def actualizar_proveedor_pendiente(self, nombre_anterior: str, nombre: str, telefono: str = "") -> bool:
        """Cambia nombre o teléfono de una ficha que todavía no tiene id en la tienda."""
        anterior = (nombre_anterior or "").strip()
        nombre = (nombre or "").strip()
        telefono = (telefono or "").strip()
        if not anterior or not nombre:
            return False
        with self._lock:
            cola = self._leer_cola()
            ahora = time.time()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hallado = False
            for ficha in cola["proveedores"]:
                if str(ficha.get("nombre") or "").strip().upper() != anterior.upper():
                    continue
                ficha["nombre"] = nombre
                ficha["telefono"] = telefono
                ficha["timestamp"] = ahora
                ficha["fecha"] = fecha
                hallado = True
                break
            if not hallado:
                cola["proveedores"].append({
                    "nombre": nombre,
                    "telefono": telefono,
                    "timestamp": ahora,
                    "fecha": fecha,
                })
            for vinculo in cola.get("vinculos") or []:
                if str(vinculo.get("proveedor_nombre") or "").strip().upper() != anterior.upper():
                    continue
                vinculo["proveedor_nombre"] = nombre
                vinculo["proveedor_telefono"] = telefono
            self._escribir_cola(cola)
            return True

    def encolar_vinculo(
        self, criterio_tipo: str, criterio_valor: str, proveedor_nombre: str,
        proveedor_telefono: str = "", proveedor_email: str = "", proveedor_id=None,
    ) -> bool:
        """Deja el enlace producto o departamento → proveedor para subirlo en la tienda."""
        tipo = (criterio_tipo or "").strip().lower()
        valor = str(criterio_valor or "").strip().upper()
        nombre = (proveedor_nombre or "").strip()
        if not tipo or not valor or not nombre:
            return False
        with self._lock:
            cola = self._leer_cola()
            ahora = time.time()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            registro = {
                "criterio_tipo": tipo,
                "criterio_valor": valor,
                "proveedor_nombre": nombre,
                "proveedor_telefono": (proveedor_telefono or "").strip(),
                "proveedor_email": (proveedor_email or "").strip(),
                "proveedor_id": int(proveedor_id or 0),
                "timestamp": ahora,
                "fecha": fecha,
            }
            for vinculo in cola["vinculos"]:
                mismo = (
                    str(vinculo.get("criterio_tipo") or "").lower() == tipo
                    and str(vinculo.get("criterio_valor") or "").upper() == valor
                )
                if mismo:
                    vinculo.update(registro)
                    self._escribir_cola(cola)
                    return True
            cola["vinculos"].append(registro)
            self._escribir_cola(cola)
            logger.info(f"Vínculo {tipo} {valor} → {nombre} encolado para la tienda.")
            return True

    def quitar_vinculo(self, criterio_tipo: str, criterio_valor: str) -> bool:
        """Saca el enlace de la cola y anota la baja para borrarlo en la tienda."""
        tipo = (criterio_tipo or "").strip().lower()
        valor = str(criterio_valor or "").strip().upper()
        if not tipo or not valor:
            return False
        with self._lock:
            cola = self._leer_cola()
            ahora = time.time()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cola["vinculos"] = [
                v for v in (cola.get("vinculos") or [])
                if not (
                    str(v.get("criterio_tipo") or "").lower() == tipo
                    and str(v.get("criterio_valor") or "").upper() == valor
                )
            ]
            cola["vinculos"].append({
                "criterio_tipo": tipo,
                "criterio_valor": valor,
                "baja": True,
                "timestamp": ahora,
                "fecha": fecha,
            })
            self._escribir_cola(cola)
            logger.info(f"Vínculo {tipo} {valor} marcado para desenlazar.")
            return True

    def productos_pendientes(self) -> list:
        with self._lock:
            return list(self._leer_cola().get("productos") or [])

    def proveedores_pendientes(self) -> list:
        with self._lock:
            return list(self._leer_cola().get("proveedores") or [])

    def vinculos_pendientes(self) -> list:
        with self._lock:
            return list(self._leer_cola().get("vinculos") or [])

    def obtener_resumen_pendientes(self) -> dict[str, int]:
        """Devuelve cantidades pendientes de sincronizar con la Maestra."""
        with self._lock:
            cola = self._leer_cola()
            n_prod = len(cola.get("productos", []))
            n_rec = len(cola.get("recepciones", []))
            n_cli = len(cola.get("clientes", []))
            n_prov = len(cola.get("proveedores", []))
            n_vin = len(cola.get("vinculos", []))
            return {
                "productos": n_prod,
                "recepciones": n_rec,
                "clientes": n_cli,
                "proveedores": n_prov,
                "vinculos": n_vin,
                "total": n_prod + n_rec + n_cli + n_prov + n_vin,
            }

    def nutrir_maestra(self, db_manager) -> tuple[bool, str, dict]:
        """
        Vuelca todos los cambios del buffer offline a la base de datos MariaDB de la Maestra.
        Retorna (exito, mensaje, detalle_stats).
        """
        if getattr(db_manager, "db_engine_type", "") != "mariadb" or not db_manager.is_connected():
            return False, "La base de datos Maestra (MariaDB) no está conectada.", {}

        with self._lock:
            cola = self._leer_cola()
            prods = cola.get("productos", [])
            recs = cola.get("recepciones", [])
            clis = cola.get("clientes", [])
            provs = cola.get("proveedores", [])
            vins = cola.get("vinculos", [])

            total_pend = len(prods) + len(recs) + len(clis) + len(provs) + len(vins)
            if total_pend == 0:
                return True, "No hay cambios de negocio offline pendientes.", {
                    "productos": 0, "recepciones": 0, "clientes": 0,
                    "proveedores": 0, "vinculos": 0,
                }

            logger.info(
                "Nutrición a la Maestra: %s productos, %s recepciones, %s clientes, "
                "%s proveedores, %s vínculos.",
                len(prods), len(recs), len(clis), len(provs), len(vins),
            )

            stats = {
                "productos": 0, "recepciones": 0, "clientes": 0,
                "proveedores": 0, "vinculos": 0,
            }

            # 1. Procesar productos
            idx_prod_ok = []
            for i, p in enumerate(prods):
                if self._aplicar_producto_maestra(db_manager, p):
                    idx_prod_ok.append(i)
                else:
                    logger.warning(f"No se pudo sincronizar producto offline {p.get('nombre')}")
                    break
            stats["productos"] = len(idx_prod_ok)

            # El id del proveedor nace en la maestra antes de colgarle productos.
            idx_prov_ok = []
            for i, ficha in enumerate(provs):
                if self._aplicar_proveedor_maestra(db_manager, ficha):
                    idx_prov_ok.append(i)
                else:
                    logger.warning(f"No se pudo crear el proveedor {ficha.get('nombre')}")
                    break
            stats["proveedores"] = len(idx_prov_ok)

            idx_vin_ok = []
            for i, vinculo in enumerate(vins):
                if self._aplicar_vinculo_maestra(db_manager, vinculo):
                    idx_vin_ok.append(i)
                else:
                    logger.warning(
                        f"No se pudo enlazar {vinculo.get('criterio_valor')} "
                        f"con {vinculo.get('proveedor_nombre')}"
                    )
                    break
            stats["vinculos"] = len(idx_vin_ok)

            # 2. Procesar recepciones de mercadería
            idx_rec_ok = []
            for i, r in enumerate(recs):
                if self._aplicar_recepcion_maestra(db_manager, r):
                    idx_rec_ok.append(i)
                else:
                    logger.warning(f"No se pudo sincronizar recepción offline de {r.get('proveedor')}")
                    break
            stats["recepciones"] = len(idx_rec_ok)

            # 3. Procesar clientes
            idx_cli_ok = []
            for i, c in enumerate(clis):
                if self._aplicar_cliente_maestra(db_manager, c):
                    idx_cli_ok.append(i)
                else:
                    logger.warning(f"No se pudo sincronizar cliente offline {c.get('datos', {}).get('nombre')}")
                    break
            stats["clientes"] = len(idx_cli_ok)

            # Limpiar elementos sincronizados de la cola
            if idx_prod_ok:
                cola["productos"] = [p for i, p in enumerate(prods) if i not in idx_prod_ok]
            if idx_rec_ok:
                cola["recepciones"] = [r for i, r in enumerate(recs) if i not in idx_rec_ok]
            if idx_cli_ok:
                cola["clientes"] = [c for i, c in enumerate(clis) if i not in idx_cli_ok]
            if idx_prov_ok:
                cola["proveedores"] = [p for i, p in enumerate(provs) if i not in idx_prov_ok]
            if idx_vin_ok:
                cola["vinculos"] = [v for i, v in enumerate(vins) if i not in idx_vin_ok]

            self._escribir_cola(cola)

            # Notificar por red a las pantallas y cartelería
            try:
                from src.central_red_global.sync_tienda.aviso_tv import avisar_datos_nuevos
                avisar_datos_nuevos()
            except Exception:
                pass

            msg = (
                f"Nutrición a la Maestra completada: {stats['productos']} productos/precios, "
                f"{stats['recepciones']} recepciones, {stats['clientes']} clientes, "
                f"{stats['proveedores']} proveedores y {stats['vinculos']} vínculos."
            )
            logger.info(f"✅ {msg}")
            return True, msg, stats

    def _aplicar_producto_maestra(self, db_manager, registro: dict) -> bool:
        """Aplica un producto directamente en la MariaDB maestra."""
        if registro.get("baja"):
            return self._borrar_producto_maestra(db_manager, registro)
        datos = registro.get("datos") or {}
        if not datos:
            return True

        try:
            _CAMPOS = {
                "codigo", "nombre", "precio", "precio_mayoreo", "cant_mayoreo",
                "cant_oferta", "precio_oferta", "precio_oferta_relampago",
                "precio_oferta_promedio", "limite_oferta_relampago", "tipo_unidad_oferta",
                "costo", "stock", "stock_minimo", "stock_maximo", "unidad",
                "es_pesable", "departamento", "categoria", "icono",
            }
            params = {k: v for k, v in dict(datos).items() if k in _CAMPOS}

            pid = datos.get("id")
            codigo = datos.get("codigo")

            # Verificar si existe en la Maestra por ID o por Código de Barras
            existente_id = None
            if pid:
                row = db_manager.execute_query("SELECT id FROM productos WHERE id = ?", (pid,))
                if row:
                    existente_id = row[0]["id"]
            if not existente_id and codigo:
                row_cod = db_manager.execute_query("SELECT id FROM productos WHERE codigo = ?", (codigo,))
                if row_cod:
                    existente_id = row_cod[0]["id"]

            if existente_id:
                set_clause = ", ".join([f"{k} = ?" for k in params.keys()])
                query = f"UPDATE productos SET {set_clause} WHERE id = ?"
                valores = tuple(list(params.values()) + [existente_id])
                return bool(db_manager.execute_non_query(query, valores))
            else:
                columnas = ", ".join(params.keys())
                placeholders = ", ".join(["?"] * len(params))
                query = f"INSERT INTO productos ({columnas}) VALUES ({placeholders})"
                valores = tuple(params.values())
                return bool(db_manager.execute_non_query(query, valores))
        except Exception as e:
            logger.error(f"Error aplicando producto en Maestra: {e}")
            return False

    def _borrar_producto_maestra(self, db_manager, registro: dict) -> bool:
        """Saca el producto de la tienda. Si ya no está, la baja queda hecha."""
        datos = registro.get("datos") or {}
        pid = registro.get("id") or datos.get("id")
        codigo = registro.get("codigo") or datos.get("codigo")
        try:
            if pid:
                db_manager.execute_non_query("DELETE FROM productos WHERE id = ?", (pid,))
                db_manager.execute_non_query(
                    "DELETE FROM formula_pieza WHERE producto_id = ?", (str(pid),)
                )
            elif codigo:
                db_manager.execute_non_query("DELETE FROM productos WHERE codigo = ?", (codigo,))
            return True
        except Exception as e:
            logger.error(f"Error borrando producto en Maestra: {e}")
            return False

    def _aplicar_recepcion_maestra(self, db_manager, registro: dict) -> bool:
        """Aplica una recepción de mercadería (stock + compras + romaneos + gastos) en MariaDB."""
        try:
            prov_clean = (registro.get("proveedor") or "").strip() or "Proveedor General"
            items = registro.get("items") or []
            total_bultos = float(registro.get("total_bultos") or 0.0)
            total_monto = float(registro.get("total_monto") or 0.0)
            condicion_pago = registro.get("condicion_pago") or "A Pagar"
            perfil = registro.get("perfil") or "admin"
            fecha_str = registro.get("fecha") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fecha_corta = fecha_str[:10]

            # 1. Asegurar ficha del proveedor
            try:
                from src.proveedor_global.backend.ficha import FichaProveedor
                FichaProveedor.obtener_o_crear(prov_clean)
            except Exception:
                pass

            # 2. Registrar en romaneos
            estado_pago_val = "Pagado" if "contado" in condicion_pago.lower() else "Pendiente"
            sql_romaneo = """
                INSERT INTO romaneos (fecha, proveedor, tropa, tipo_carne, precio_unitario, total_kilos, monto_total, estado_pago, registrado_por)
                VALUES (?, ?, ?, 'RECEPCION_MERCADERIA', ?, ?, ?, ?, ?)
            """
            pu = total_monto / max(1.0, total_bultos)
            db_manager.execute_non_query(
                sql_romaneo,
                (fecha_corta, prov_clean, "REMITO_OFFLINE_NUTRICION", pu, total_bultos, total_monto, estado_pago_val, perfil)
            )

            rom_id_rows = db_manager.execute_query("SELECT id FROM romaneos ORDER BY id DESC LIMIT 1") or []
            romaneo_id = rom_id_rows[0]["id"] if rom_id_rows else 0

            # 3. Sumar Stock y Costo en MariaDB
            detalle_desc = f"Recepción Offline Nutrición - Proveedor: {prov_clean}\n"
            for it in items:
                if it.get("extension"):
                    continue
                cant = float(it.get("cantidad", 1.0))
                costo_nuevo = float(it.get("costo", 0.0))
                nom = it.get("nombre", "")
                cod = str(it.get("codigo") or "").strip()
                p_id = it.get("id")

                # Localizar producto en MariaDB por código o id
                target_pid = None
                if cod:
                    r_p = db_manager.execute_query("SELECT id FROM productos WHERE codigo = ?", (cod,))
                    if r_p:
                        target_pid = r_p[0]["id"]
                if not target_pid and p_id:
                    r_p = db_manager.execute_query("SELECT id FROM productos WHERE id = ?", (p_id,))
                    if r_p:
                        target_pid = r_p[0]["id"]

                if target_pid:
                    sql_update = """
                        UPDATE productos 
                        SET stock = COALESCE(stock, 0) + ?,
                            costo = ?
                        WHERE id = ?
                    """
                    db_manager.execute_non_query(sql_update, (cant, costo_nuevo, target_pid))
                else:
                    # Si no existe en la maestra, crearlo con el stock recibido
                    sql_insert = """
                        INSERT INTO productos (codigo, nombre, stock, costo, precio, categoria, departamento)
                        VALUES (?, ?, ?, ?, ?, 'GENERAL', 'GENERAL')
                    """
                    precio_ref = float(it.get("precio_actual") or it.get("precio") or (costo_nuevo * 1.4))
                    db_manager.execute_non_query(sql_insert, (cod, nom, cant, costo_nuevo, precio_ref))

                if romaneo_id:
                    db_manager.execute_non_query(
                        "INSERT INTO romaneo_items (romaneo_id, nro_garrote, peso) VALUES (?, ?, ?)",
                        (romaneo_id, cod or str(target_pid or p_id), cant)
                    )
                detalle_desc += f"• {cant}x {nom} (${costo_nuevo:,.2f})\n"

            try:
                from src.proveedor_global.frontend.formula.motores.extension import escribir_db, texto as texto_extension
                escribir_db(db_manager, items)
                detalle_desc += texto_extension(items)
            except Exception:
                pass

            # 4. Registrar en gastos
            sql_gasto = """
                INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario)
                VALUES (?, 'Mercadería / Stock', ?, ?, ?, ?)
            """
            db_manager.execute_non_query(
                sql_gasto,
                (fecha_str, detalle_desc.strip(), total_monto, estado_pago_val, perfil)
            )

            return True
        except Exception as e:
            logger.error(f"Error aplicando recepción en Maestra: {e}")
            return False

    def _aplicar_cliente_maestra(self, db_manager, registro: dict) -> bool:
        """Aplica un alta o modificación de cliente en MariaDB."""
        try:
            accion = (registro.get("accion") or "ALTA").upper()
            datos = registro.get("datos") or {}

            if accion == "ALTA":
                # Asegurar cliente en MariaDB
                nombre = (datos.get("nombre") or "").strip()
                dni = (datos.get("dni") or "").strip()
                uid = datos.get("uid")

                existente = None
                if uid:
                    r = db_manager.execute_query("SELECT id FROM clientes WHERE uid = ?", (uid,))
                    if r:
                        existente = r[0]
                if not existente and dni:
                    r = db_manager.execute_query("SELECT id FROM clientes WHERE dni = ?", (dni,))
                    if r:
                        existente = r[0]

                if not existente:
                    CAMPOS = ("nombre", "telefono", "dni", "direccion", "email", "limite_credito",
                              "deuda_actual", "tipo_cliente", "plazo_dias", "uid", "origen_pc",
                              "creado_por", "creado_en", "actualizado_en")
                    filtro = {k: v for k, v in datos.items() if k in CAMPOS}
                    cols = list(filtro.keys())
                    db_manager.execute_non_query(
                        f"INSERT INTO clientes ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                        tuple(filtro[c] for c in cols)
                    )
                return True

            elif accion == "EDICION":
                cid = datos.get("id")
                cambios = datos.get("cambios") or {}
                if not cid or not cambios:
                    return True
                # No tocar la deuda aquí para preservar transacciones atómicas
                filtro = {k: v for k, v in cambios.items() if k != "deuda_actual"}
                if filtro:
                    sets = ", ".join(f"{k} = ?" for k in filtro)
                    db_manager.execute_non_query(
                        f"UPDATE clientes SET {sets} WHERE id = ?",
                        tuple(filtro.values()) + (cid,)
                    )
                return True

            return True
        except Exception as e:
            logger.error(f"Error aplicando cliente en Maestra: {e}")
            return False

    def _aplicar_proveedor_maestra(self, db_manager, registro: dict) -> bool:
        """Crea el id en la maestra. Si el nombre ya está, no inventa otro."""
        nombre = (registro.get("nombre") or "").strip()
        telefono = (registro.get("telefono") or "").strip()
        if not nombre:
            return True
        try:
            import uuid

            from src.proveedor_global.backend.ficha import FichaProveedor, codigo_visible
            from src.proveedor_global.backend.motor_proveedor import MotorProveedor, _ConexionTienda

            conn = MotorProveedor._abrir_conexion_tienda(db_manager)
        except Exception as e:
            logger.error(f"No se abrió la maestra para el proveedor {nombre}: {e}")
            return False
        try:
            tienda = _ConexionTienda(db_manager, conn)
            FichaProveedor.asegurar(tienda)
            ya = tienda.execute_query(
                "SELECT id FROM proveedores WHERE UPPER(nombre) = UPPER(?) AND activo = 1",
                (nombre,),
            ) or []
            if ya:
                conn.commit()
                return True
            temporal = "T" + uuid.uuid4().hex[:12]
            if not tienda.execute_non_query(
                "INSERT INTO proveedores (codigo, nombre, telefono, activo) VALUES (?, ?, ?, 1)",
                (temporal, nombre, telefono),
            ):
                raise RuntimeError("La maestra no guardó la ficha.")
            ids = tienda.execute_query("SELECT LAST_INSERT_ID() AS id") or []
            fila = ids[0] if ids else None
            proveedor_id = int(fila["id"] if isinstance(fila, dict) else fila[0])
            if not proveedor_id:
                raise RuntimeError("La maestra no devolvió el id.")
            if not tienda.execute_non_query(
                "UPDATE proveedores SET codigo = ? WHERE id = ?",
                (codigo_visible(proveedor_id), proveedor_id),
            ):
                raise RuntimeError("La maestra no pudo anotar el código.")
            conn.commit()
            return True
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"Error creando proveedor {nombre} en la maestra: {e}")
            return False
        finally:
            conn.close()

    def _aplicar_vinculo_maestra(self, db_manager, registro: dict) -> bool:
        """Cuelga el producto o el departamento del id real. El id de casa no se copia."""
        tipo = (registro.get("criterio_tipo") or "").strip().lower()
        valor = str(registro.get("criterio_valor") or "").strip().upper()
        if registro.get("baja"):
            if not tipo or not valor:
                return True
            ok = db_manager.execute_non_query(
                "DELETE FROM abastecimiento_proveedor_map "
                "WHERE LOWER(criterio_tipo) = ? AND UPPER(criterio_valor) = ?",
                (tipo, valor),
            )
            error = str(getattr(db_manager, "last_error", "") or "").lower()
            if ok or "no such table" in error or "doesn't exist" in error:
                return True
            return False
        nombre = (registro.get("proveedor_nombre") or "").strip()
        telefono = (registro.get("proveedor_telefono") or "").strip()
        email = (registro.get("proveedor_email") or "").strip()
        if not tipo or not valor or not nombre:
            return True
        try:
            proveedor_id = self._id_proveedor_en_maestra(db_manager, registro)
            if not proveedor_id:
                if not self._aplicar_proveedor_maestra(db_manager, {"nombre": nombre, "telefono": telefono}):
                    return False
                proveedor_id = self._id_proveedor_en_maestra(
                    db_manager, {"proveedor_nombre": nombre, "proveedor_id": 0}
                )
            if not proveedor_id:
                return False
            db_manager.execute_non_query(
                """
                CREATE TABLE IF NOT EXISTS abastecimiento_proveedor_map (
                    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    criterio_tipo VARCHAR(32) NOT NULL,
                    criterio_valor VARCHAR(255) NOT NULL,
                    proveedor_nombre VARCHAR(255) NOT NULL,
                    proveedor_telefono VARCHAR(64) NOT NULL DEFAULT '',
                    proveedor_email VARCHAR(255) NOT NULL DEFAULT '',
                    proveedor_id INT NULL,
                    UNIQUE KEY uq_abastecimiento_criterio (criterio_tipo, criterio_valor)
                )
                """
            )
            sql = """
                INSERT INTO abastecimiento_proveedor_map
                    (criterio_tipo, criterio_valor, proveedor_nombre, proveedor_telefono, proveedor_email, proveedor_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                    proveedor_nombre=VALUES(proveedor_nombre),
                    proveedor_telefono=VALUES(proveedor_telefono),
                    proveedor_email=VALUES(proveedor_email),
                    proveedor_id=VALUES(proveedor_id)
            """
            return bool(db_manager.execute_non_query(
                sql, (tipo, valor, nombre, telefono, email, proveedor_id)
            ))
        except Exception as e:
            logger.error(f"Error enlazando {valor} con {nombre}: {e}")
            return False

    @staticmethod
    def _id_proveedor_en_maestra(db_manager, registro: dict) -> int:
        pid = int(registro.get("proveedor_id") or 0)
        nombre = (registro.get("proveedor_nombre") or registro.get("nombre") or "").strip()
        if pid:
            filas = db_manager.execute_query(
                "SELECT id FROM proveedores WHERE id = ? AND activo = 1",
                (pid,),
            ) or []
            if filas:
                fila = filas[0]
                return int(fila["id"] if isinstance(fila, dict) else fila[0])
        if not nombre:
            return 0
        filas = db_manager.execute_query(
            "SELECT id FROM proveedores WHERE UPPER(nombre) = UPPER(?) AND activo = 1",
            (nombre,),
        ) or []
        if not filas:
            return 0
        fila = filas[0]
        return int(fila["id"] if isinstance(fila, dict) else fila[0])


offline_nutricion_manager = OfflineNutricionManager()
