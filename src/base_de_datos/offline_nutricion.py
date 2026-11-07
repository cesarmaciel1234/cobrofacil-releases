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
import sqlite3
import threading
import time
import uuid
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
                            "proveedores": [], "vinculos": [], "auditorias": [],
                        }, f, indent=4)
                except Exception as e:
                    logger.error(f"Error creando offline_cambios.json: {e}")

    def _leer_cola(self, estricto: bool = False) -> dict | None:
        try:
            if not os.path.exists(self.outbox_file):
                return self._cola_vacia()
            with open(self.outbox_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if estricto and not isinstance(data, dict):
                raise ValueError("el outbox no contiene un objeto JSON")
            if estricto and any(
                clave in data and not isinstance(data[clave], list)
                for clave in self._cola_vacia()
            ):
                raise ValueError("el outbox contiene una cola con formato inválido")
            if estricto and any(
                not isinstance(registro, dict)
                for registro in data.get("recepciones", [])
            ):
                raise ValueError("el outbox contiene una recepción con formato inválido")
            if estricto and any(
                not isinstance(registro, dict)
                for registro in data.get("auditorias", [])
            ):
                raise ValueError("el outbox contiene una auditoría con formato inválido")
            return self._normalizar_cola(data)
        except Exception as e:
            logger.error(f"Error leyendo outbox offline_cambios: {e}")
            if estricto:
                return None
            return self._cola_vacia()

    @staticmethod
    def _cola_vacia() -> dict:
        return {
            "productos": [], "recepciones": [], "clientes": [],
            "proveedores": [], "vinculos": [], "auditorias": [],
        }

    @classmethod
    def _normalizar_cola(cls, data) -> dict:
        if not isinstance(data, dict):
            data = {}
        for clave in cls._cola_vacia():
            if not isinstance(data.get(clave), list):
                data[clave] = []
        return data

    def _escribir_cola(self, data: dict) -> bool:
        try:
            temp_file = self.outbox_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, self.outbox_file)
            return True
        except Exception as e:
            logger.error(f"Error escribiendo outbox offline_cambios: {e}")
            return False

    def _ruta_sqlite_local(self) -> str:
        """Obtiene el archivo SQLite offline aunque db_manager ya haya vuelto a MariaDB."""
        ruta = os.path.join(self.base_path, "punpro.db")
        config_path = os.path.join(self.base_path, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as archivo:
                configuracion = json.load(archivo)
            nombre = str(configuracion.get("db_name") or "punpro.db").strip()
            ruta = nombre if os.path.isabs(nombre) else os.path.join(self.base_path, nombre)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error("No se pudo resolver el SQLite local para el outbox de recepciones: %s", e)
            raise
        return ruta

    def _leer_recepciones_persistentes(self) -> tuple[bool, list[dict]]:
        """Recupera recepciones confirmadas localmente aunque se haya perdido el JSON outbox."""
        ruta = self._ruta_sqlite_local()
        if not os.path.isfile(ruta):
            return True, []
        try:
            conn = sqlite3.connect(ruta, timeout=2)
            try:
                filas = conn.execute(
                    "SELECT payload FROM offline_recepciones ORDER BY created_at, sync_id"
                ).fetchall()
            finally:
                conn.close()
            registros = []
            for fila in filas:
                registro = json.loads(fila[0])
                if not isinstance(registro, dict) or not str(registro.get("sync_id") or "").strip():
                    logger.error("El journal local contiene una recepción inválida.")
                    return False, []
                registros.append(registro)
            return True, registros
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                return True, []
            logger.error("No se pudo leer el journal SQLite de recepciones: %s", e)
            return False, []
        except Exception as e:
            logger.error("No se pudo recuperar el journal SQLite de recepciones: %s", e)
            return False, []

    def _incorporar_recepciones_persistentes(self, cola: dict) -> tuple[bool, set[str]]:
        ok, persistentes = self._leer_recepciones_persistentes()
        if not ok:
            return False, set()
        pendientes = cola.get("recepciones") or []
        por_id = {
            str(registro.get("sync_id") or ""): registro
            for registro in pendientes
            if isinstance(registro, dict) and registro.get("sync_id")
        }
        agregadas = False
        for registro in persistentes:
            sync_id = str(registro["sync_id"])
            existente = por_id.get(sync_id)
            if existente is not None:
                if existente != registro:
                    logger.error("El outbox y el journal discrepan para recepción %s.", sync_id)
                    return False, set()
                continue
            pendientes.append(registro)
            por_id[sync_id] = registro
            agregadas = True
        if agregadas:
            cola["recepciones"] = pendientes
            if not self._escribir_cola(cola):
                return False, set()
        return True, {str(registro["sync_id"]) for registro in persistentes}

    def _confirmar_recepciones_persistentes(self, sync_ids: set[str]) -> bool:
        if not sync_ids:
            return True
        try:
            ruta = self._ruta_sqlite_local()
            if not os.path.isfile(ruta):
                return True
            conn = sqlite3.connect(ruta, timeout=2)
            try:
                conn.executemany(
                    "DELETE FROM offline_recepciones WHERE sync_id = ?",
                    [(sync_id,) for sync_id in sync_ids],
                )
                conn.commit()
            finally:
                conn.close()
            return True
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                return True
            logger.error("No se pudo confirmar el journal de recepciones: %s", e)
            return False
        except Exception as e:
            logger.error("No se pudo confirmar el journal de recepciones: %s", e)
            return False

    def encolar_producto(self, datos: dict) -> bool:
        """Encola la creación o modificación de un producto realizada fuera de línea."""
        if not datos:
            return False
        with self._lock:
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False
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

            if not self._escribir_cola(cola):
                return False
            logger.info(f"📦 Producto '{datos.get('nombre')}' encolado en buffer offline para nutrir Maestra.")
            return True

    def encolar_baja_producto(self, producto_id, codigo="", nombre="") -> bool:
        """El producto se fue. En casa la copia lo esconde y en la tienda se borra."""
        ident = str(producto_id or "").strip()
        codigo = str(codigo or "").strip()
        if not ident and not codigo:
            return False
        with self._lock:
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False
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
            return self._escribir_cola(cola)

    def encolar_recepcion(
        self, proveedor: str, items: list, total_bultos: float,
        total_monto: float, condicion_pago: str = "A Pagar", perfil: str = "admin",
        fecha: str = "", sync_id: str | None = None,
        timestamp: float | None = None,
    ) -> bool:
        """Encola una recepción de mercadería (escaneo de remito/bultos) efectuada offline."""
        if not items:
            return False
        sync_id = str(sync_id or uuid.uuid4()).strip()
        with self._lock:
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False
            registro = {
                "sync_id": sync_id,
                "proveedor": proveedor,
                "items": items,
                "total_bultos": float(total_bultos),
                "total_monto": float(total_monto),
                "condicion_pago": condicion_pago,
                "perfil": perfil,
                "timestamp": float(timestamp) if timestamp is not None else time.time(),
                "fecha": (fecha or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            existente = next(
                (
                    actual
                    for actual in cola["recepciones"]
                    if isinstance(actual, dict)
                    and str(actual.get("sync_id") or "") == sync_id
                ),
                None,
            )
            if existente is not None:
                campos_evento = (
                    "proveedor", "items", "total_bultos", "total_monto",
                    "condicion_pago", "perfil", "fecha",
                )
                if any(existente.get(campo) != registro.get(campo) for campo in campos_evento):
                    logger.error("Colisión de sync_id en recepción offline: %s", sync_id)
                    return False
                return True
            cola["recepciones"].append(registro)
            if not self._escribir_cola(cola):
                return False
            logger.info(f"🚚 Recepción de {proveedor} (${total_monto:,.2f}) encolada en buffer offline.")
            return True

    def encolar_cliente(self, accion: str, datos: dict) -> bool:
        """Encola un alta o modificación de cliente realizada offline."""
        if not datos:
            return False
        with self._lock:
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False
            registro = {
                "accion": accion.upper(),  # 'ALTA' o 'EDICION'
                "datos": dict(datos),
                "timestamp": time.time(),
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            cola["clientes"].append(registro)
            if not self._escribir_cola(cola):
                return False
            logger.info(f"👤 Cliente evento {accion} encolado en buffer offline.")
            return True

    def encolar_auditoria(self, registro: dict) -> bool:
        """Guarda un evento de auditoría con identidad estable antes de subirlo."""
        datos = dict(registro or {})
        sync_id = str(datos.get("sync_id") or "").strip()
        if not sync_id:
            return False
        datos["sync_id"] = sync_id
        with self._lock:
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False
            if any(str(item.get("sync_id") or "") == sync_id for item in cola["auditorias"]):
                return True
            cola["auditorias"].append(datos)
            if not self._escribir_cola(cola):
                return False
            logger.info("Auditoría encolada para la maestra: %s", sync_id)
            return True

    def encolar_proveedor(self, nombre: str, telefono: str = "") -> bool:
        """Deja el alta de un proveedor para cuando la notebook vuelva a la tienda."""
        nombre = (nombre or "").strip()
        telefono = (telefono or "").strip()
        if not nombre:
            return False
        with self._lock:
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False
            ahora = time.time()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for ficha in cola["proveedores"]:
                if str(ficha.get("nombre") or "").strip().upper() == nombre.upper():
                    if telefono:
                        ficha["telefono"] = telefono
                    ficha["timestamp"] = ahora
                    ficha["fecha"] = fecha
                    return self._escribir_cola(cola)
            cola["proveedores"].append({
                "nombre": nombre,
                "telefono": telefono,
                "timestamp": ahora,
                "fecha": fecha,
            })
            if not self._escribir_cola(cola):
                return False
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
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False
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
            return self._escribir_cola(cola)

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
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False
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
                    return self._escribir_cola(cola)
            cola["vinculos"].append(registro)
            if not self._escribir_cola(cola):
                return False
            logger.info(f"Vínculo {tipo} {valor} → {nombre} encolado para la tienda.")
            return True

    def quitar_vinculo(self, criterio_tipo: str, criterio_valor: str) -> bool:
        """Saca el enlace de la cola y anota la baja para borrarlo en la tienda."""
        tipo = (criterio_tipo or "").strip().lower()
        valor = str(criterio_valor or "").strip().upper()
        if not tipo or not valor:
            return False
        with self._lock:
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False
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
            if not self._escribir_cola(cola):
                return False
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
            cola = self._leer_cola(estricto=True)
            if cola is None:
                logger.error("Outbox ilegible: se mantiene bloqueada la sincronización.")
                return {
                    "productos": 0, "recepciones": 0, "clientes": 0,
                    "proveedores": 0, "vinculos": 0, "auditorias": 0,
                    "error": 1, "total": 1,
                }
            n_prod = len(cola.get("productos", []))
            n_rec = len(cola.get("recepciones", []))
            n_cli = len(cola.get("clientes", []))
            n_prov = len(cola.get("proveedores", []))
            n_vin = len(cola.get("vinculos", []))
            n_aud = len(cola.get("auditorias", []))
            return {
                "productos": n_prod,
                "recepciones": n_rec,
                "clientes": n_cli,
                "proveedores": n_prov,
                "vinculos": n_vin,
                "auditorias": n_aud,
                "total": n_prod + n_rec + n_cli + n_prov + n_vin + n_aud,
            }

    def nutrir_maestra(self, db_manager) -> tuple[bool, str, dict]:
        """
        Vuelca todos los cambios del buffer offline a la base de datos MariaDB de la Maestra.
        Retorna (exito, mensaje, detalle_stats).
        """
        if getattr(db_manager, "db_engine_type", "") != "mariadb" or not db_manager.is_connected():
            return False, "La base de datos Maestra (MariaDB) no está conectada.", {}

        with self._lock:
            cola = self._leer_cola(estricto=True)
            if cola is None:
                return False, "El outbox offline no se pudo leer; se conservó sin cambios.", {}
            journal_ok, recepciones_journal_ids = self._incorporar_recepciones_persistentes(cola)
            if not journal_ok:
                return False, "No se pudo recuperar el journal de recepciones; se conservó sin cambios.", {}
            prods = cola.get("productos", [])
            recs = cola.get("recepciones", [])
            clis = cola.get("clientes", [])
            provs = cola.get("proveedores", [])
            vins = cola.get("vinculos", [])
            auds = cola.get("auditorias", [])

            recepciones_migradas = False
            for recepcion in recs:
                if not isinstance(recepcion, dict):
                    return False, "Hay una recepción offline inválida; se conservó el outbox.", {}
                if not str(recepcion.get("sync_id") or "").strip():
                    recepcion["sync_id"] = str(uuid.uuid4())
                    recepciones_migradas = True
            if recepciones_migradas and not self._escribir_cola(cola):
                return False, "No se pudo guardar la identidad de las recepciones pendientes.", {}

            total_pend = len(prods) + len(recs) + len(clis) + len(provs) + len(vins) + len(auds)
            if total_pend == 0:
                return True, "No hay cambios de negocio offline pendientes.", {
                    "productos": 0, "recepciones": 0, "clientes": 0,
                    "proveedores": 0, "vinculos": 0, "auditorias": 0,
                }

            logger.info(
                "Nutrición a la Maestra: %s productos, %s recepciones, %s clientes, "
                "%s proveedores, %s vínculos y %s auditorías.",
                len(prods), len(recs), len(clis), len(provs), len(vins), len(auds),
            )

            stats = {
                "productos": 0, "recepciones": 0, "clientes": 0,
                "proveedores": 0, "vinculos": 0, "auditorias": 0,
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

            idx_aud_ok = []
            for i, registro in enumerate(auds):
                if self._aplicar_auditoria_maestra(db_manager, registro):
                    idx_aud_ok.append(i)
                else:
                    logger.warning(
                        "No se pudo sincronizar auditoría offline %s",
                        registro.get("sync_id") or "(sin id)",
                    )
                    break
            stats["auditorias"] = len(idx_aud_ok)

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
            if idx_aud_ok:
                cola["auditorias"] = [v for i, v in enumerate(auds) if i not in idx_aud_ok]

            if not self._escribir_cola(cola):
                return False, "La maestra aplicó cambios, pero no se pudo guardar el acuse local; se reintentará con idempotencia.", stats

            recepciones_confirmadas = {
                str(recs[i].get("sync_id") or "")
                for i in idx_rec_ok
                if isinstance(recs[i], dict)
            } & recepciones_journal_ids
            if not self._confirmar_recepciones_persistentes(recepciones_confirmadas):
                return False, (
                    "La maestra confirmó las recepciones, pero el journal local no pudo limpiarse; "
                    "se reintentará sin duplicar operaciones."
                ), stats

            # Notificar por red a las pantallas y cartelería
            try:
                from src.central_red_global.sync_tienda.aviso_tv import avisar_datos_nuevos
                avisar_datos_nuevos()
            except Exception:
                pass

            msg = (
                f"Nutrición a la Maestra completada: {stats['productos']} productos/precios, "
                f"{stats['recepciones']} recepciones, {stats['clientes']} clientes, "
                f"{stats['proveedores']} proveedores, {stats['vinculos']} vínculos y "
                f"{stats['auditorias']} auditorías."
            )
            pendientes = sum(
                len(cola.get(clave) or [])
                for clave in ("productos", "recepciones", "clientes", "proveedores", "vinculos", "auditorias")
            )
            if pendientes:
                msg = f"Sincronización parcial: {msg} Quedan {pendientes} elementos pendientes."
                logger.warning(msg)
                return False, msg, stats
            logger.info(f"✅ {msg}")
            return True, msg, stats

    def _aplicar_auditoria_maestra(self, db_manager, registro: dict) -> bool:
        """Inserta el evento una sola vez; la cola solo se confirma tras verificarlo."""
        sync_id = str(registro.get("sync_id") or "").strip()
        if not sync_id:
            logger.error("Auditoría offline sin sync_id; se conserva en el outbox.")
            return False
        try:
            from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria

            if not MotorAuditoria.asegurar_tabla_auditorias(db_manager):
                return False
            existente = db_manager.execute_query(
                "SELECT id FROM auditorias_inventario WHERE sync_id = ? LIMIT 1",
                (sync_id,),
            ) or []
            if existente:
                return True
            insertado = db_manager.execute_non_query(
                """INSERT INTO auditorias_inventario
                   (sync_id, fecha, producto_id, nombre_producto, stock_sistema,
                    stock_fisico, diferencia, responsable, motivo)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sync_id,
                    registro.get("fecha"),
                    registro.get("producto_id"),
                    registro.get("nombre_producto") or "",
                    registro.get("stock_sistema", 0.0),
                    registro.get("stock_fisico", 0.0),
                    registro.get("diferencia", 0.0),
                    registro.get("responsable") or "",
                    registro.get("motivo") or "",
                ),
            )
            if not insertado:
                return False
            verificado = db_manager.execute_query(
                "SELECT id FROM auditorias_inventario WHERE sync_id = ? LIMIT 1",
                (sync_id,),
            ) or []
            return bool(verificado)
        except Exception as e:
            logger.error("Error aplicando auditoría offline en la maestra: %s", e)
            return False

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

    @staticmethod
    def _ejecutar_recepcion(db_manager, cursor, query, params=(), consulta=False):
        normalizar = getattr(db_manager, "_normalize_query", None)
        cursor.execute(normalizar(query) if normalizar else query, params)
        return cursor.fetchall() if consulta else True

    @staticmethod
    def _asegurar_idempotencia_recepcion(db_manager) -> bool:
        """Prepara la clave única antes de abrir la transacción de negocio."""
        mariadb = getattr(db_manager, "db_engine_type", "") == "mariadb"
        columnas = db_manager.execute_query(
            "SHOW COLUMNS FROM romaneos" if mariadb else "PRAGMA table_info(romaneos)"
        ) or []
        if not columnas:
            logger.error("No se pudo leer el esquema de romaneos para sincronizar recepciones.")
            return False

        def campo(fila, nombre, default=None):
            try:
                return fila.get(nombre, default)
            except AttributeError:
                try:
                    return fila[nombre]
                except (KeyError, IndexError, TypeError):
                    return default

        nombres = {
            str((campo(fila, "Field") if mariadb else campo(fila, "name")) or "").lower()
            for fila in columnas
        }
        if "sync_id" not in nombres and not db_manager.execute_non_query(
            "ALTER TABLE romaneos ADD COLUMN sync_id VARCHAR(36)"
        ):
            logger.error("No se pudo agregar romaneos.sync_id.")
            return False

        if mariadb:
            indices = db_manager.execute_query("SHOW INDEX FROM romaneos") or []
            por_indice = {}
            for fila in indices:
                if int(campo(fila, "Non_unique", 1)) != 0:
                    continue
                nombre = str(campo(fila, "Key_name") or "")
                por_indice.setdefault(nombre, []).append(
                    (
                        int(campo(fila, "Seq_in_index", 0)),
                        str(campo(fila, "Column_name") or "").lower(),
                    )
                )
            indexado = any(
                sorted(columnas_indice) == [(1, "sync_id")]
                for columnas_indice in por_indice.values()
            )
        else:
            indices = db_manager.execute_query("PRAGMA index_list(romaneos)") or []
            indexado = False
            for indice in indices:
                if not campo(indice, "unique"):
                    continue
                nombre = campo(indice, "name")
                detalle = db_manager.execute_query(f'PRAGMA index_info("{nombre}")') or []
                if [campo(fila, "name") for fila in detalle] == ["sync_id"]:
                    indexado = True
                    break
        if not indexado and not db_manager.execute_non_query(
            "CREATE UNIQUE INDEX uq_romaneos_sync_id ON romaneos (sync_id)"
        ):
            logger.error("No se pudo asegurar la clave idempotente de las recepciones.")
            return False
        return True

    class _AdaptadorTransaccion:
        def __init__(self, db_manager, conn):
            self._db_manager = db_manager
            self._conn = conn

        def execute_query(self, query, params=()):
            cursor = self._conn.cursor()
            try:
                normalizar = getattr(self._db_manager, "_normalize_query", None)
                cursor.execute(normalizar(query) if normalizar else query, params)
                return cursor.fetchall()
            finally:
                cerrar = getattr(cursor, "close", None)
                if callable(cerrar):
                    cerrar()

        def execute_non_query(self, query, params=()):
            cursor = self._conn.cursor()
            try:
                normalizar = getattr(self._db_manager, "_normalize_query", None)
                cursor.execute(normalizar(query) if normalizar else query, params)
                return True
            finally:
                cerrar = getattr(cursor, "close", None)
                if callable(cerrar):
                    cerrar()

    def _aplicar_recepcion_maestra(self, db_manager, registro: dict) -> bool:
        sync_id = str(registro.get("sync_id") or "").strip()
        if not sync_id:
            logger.error("Recepción offline sin sync_id; se conserva en el outbox.")
            return False
        try:
            if not self._asegurar_idempotencia_recepcion(db_manager):
                return False
        except Exception as e:
            logger.error("No se pudo preparar la idempotencia de la recepción: %s", e)
            return False
        if (
            getattr(db_manager, "db_engine_type", "") != "mariadb"
            or getattr(db_manager, "_forced_local_offline", False)
        ):
            logger.warning("La conexión dejó de ser MariaDB; la recepción queda pendiente.")
            return False

        conn = None
        try:
            conn = db_manager.get_connection(caer_si_maestra_caida=False)
            cursor = conn.cursor()
            if hasattr(conn, "begin"):
                conn.begin()
            else:
                cursor.execute("BEGIN")

            existente = self._ejecutar_recepcion(
                db_manager, cursor,
                "SELECT id FROM romaneos WHERE sync_id = ? LIMIT 1",
                (sync_id,), consulta=True,
            )
            if existente:
                conn.rollback()
                return True

            prov_clean = (registro.get("proveedor") or "").strip() or "Proveedor General"
            items = registro.get("items") or []
            if not isinstance(items, list) or not items:
                raise ValueError("La recepción no contiene artículos válidos.")
            total_bultos = float(registro.get("total_bultos") or 0.0)
            total_monto = float(registro.get("total_monto") or 0.0)
            condicion_pago = registro.get("condicion_pago") or "A Pagar"
            perfil = registro.get("perfil") or "admin"
            fecha_str = registro.get("fecha") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fecha_corta = fecha_str[:10]

            estado_pago_val = "Pagado" if "contado" in condicion_pago.lower() else "Pendiente"
            sql_romaneo = """
                INSERT INTO romaneos
                    (fecha, proveedor, tropa, tipo_carne, precio_unitario, total_kilos,
                     monto_total, estado_pago, registrado_por, sync_id)
                VALUES (?, ?, ?, 'RECEPCION_MERCADERIA', ?, ?, ?, ?, ?, ?)
            """
            pu = total_monto / max(1.0, total_bultos)
            self._ejecutar_recepcion(
                db_manager, cursor, sql_romaneo,
                (
                    fecha_corta, prov_clean, "REMITO_OFFLINE_NUTRICION", pu,
                    total_bultos, total_monto, estado_pago_val, perfil, sync_id,
                ),
            )
            romaneo_id = int(getattr(cursor, "lastrowid", 0) or 0)
            if not romaneo_id:
                raise RuntimeError("La maestra no devolvió el id del remito offline.")

            detalle_desc = f"Recepción Offline Nutrición - Proveedor: {prov_clean}\n"
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError("La recepción contiene un artículo inválido.")
                if item.get("extension"):
                    continue
                cantidad = float(item.get("cantidad", 1.0))
                costo = float(item.get("costo", 0.0))
                nombre = item.get("nombre", "")
                codigo = str(item.get("codigo") or "").strip()
                producto_id = item.get("id")
                producto_maestra = None
                if codigo:
                    filas = self._ejecutar_recepcion(
                        db_manager, cursor,
                        "SELECT id FROM productos WHERE codigo = ?", (codigo,), consulta=True,
                    )
                    if filas:
                        producto_maestra = filas[0]["id"]
                if not producto_maestra and producto_id:
                    filas = self._ejecutar_recepcion(
                        db_manager, cursor,
                        "SELECT id FROM productos WHERE id = ?", (producto_id,), consulta=True,
                    )
                    if filas:
                        producto_maestra = filas[0]["id"]

                if producto_maestra and not item.get("desde_formula"):
                    self._ejecutar_recepcion(
                        db_manager, cursor,
                        """
                            UPDATE productos
                            SET stock = COALESCE(stock, 0) + ?, costo = ?
                            WHERE id = ?
                        """,
                        (cantidad, costo, producto_maestra),
                    )
                    if not getattr(cursor, "rowcount", 1):
                        existe = self._ejecutar_recepcion(
                            db_manager, cursor,
                            "SELECT id FROM productos WHERE id = ?",
                            (producto_maestra,), consulta=True,
                        )
                        if not existe:
                            raise RuntimeError(f"El producto {nombre} desapareció durante la recepción.")
                elif not producto_maestra and not item.get("desde_formula"):
                    precio = float(item.get("precio_actual") or item.get("precio") or (costo * 1.4))
                    self._ejecutar_recepcion(
                        db_manager, cursor,
                        """
                            INSERT INTO productos
                                (codigo, nombre, stock, costo, precio, categoria, departamento)
                            VALUES (?, ?, ?, ?, ?, 'GENERAL', 'GENERAL')
                        """,
                        (codigo, nombre, cantidad, costo, precio),
                    )
                    producto_maestra = int(getattr(cursor, "lastrowid", 0) or 0)
                    if not producto_maestra:
                        raise RuntimeError(f"La maestra no devolvió el id del producto {nombre}.")

                if not item.get("extension"):
                    self._ejecutar_recepcion(
                        db_manager, cursor,
                        "INSERT INTO romaneo_items (romaneo_id, nro_garrote, peso) VALUES (?, ?, ?)",
                        (romaneo_id, codigo or str(producto_maestra or producto_id), cantidad),
                    )
                detalle_desc += f"• {cantidad}x {nombre} (${costo:,.2f})\n"

            db_transaccional = self._AdaptadorTransaccion(db_manager, conn)
            if any(item.get("desde_formula") for item in items if isinstance(item, dict)):
                from src.proveedor_global.backend.recepcion_service import _avisar_formula
                _avisar_formula(cursor, items, db_transaccional)
            else:
                from src.proveedor_global.frontend.formula.motores.extension import escribir_db
                escribir_db(db_transaccional, items)

            from src.proveedor_global.frontend.formula.motores.extension import texto as texto_extension
            detalle_desc += texto_extension(items)

            sql_gasto = """
                INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario)
                VALUES (?, 'Mercadería / Stock', ?, ?, ?, ?)
            """
            self._ejecutar_recepcion(
                db_manager, cursor, sql_gasto,
                (fecha_str, detalle_desc.strip(), total_monto, estado_pago_val, perfil),
            )
            conn.commit()
            return True
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    logger.exception("No se pudo revertir la recepción offline fallida.")
            logger.error("Error aplicando recepción offline en Maestra: %s", e)
            return False
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    logger.exception("No se pudo cerrar la conexión de recepción offline.")

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
                              "deuda_actual", "tipo_cliente", "plazo_dias", "estado_cuenta",
                              "promesa_fecha", "promesa_nota", "uid", "origen_pc",
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
