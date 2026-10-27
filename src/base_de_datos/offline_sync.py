import json
import os
import sys
import threading
import time
from src.utils.paths import get_base_path
import logging

logger = logging.getLogger("PunPro")

class OfflineSync:
    def __init__(self):
        self.base_path = get_base_path()
        self.queue_file = os.path.join(self.base_path, "offline_queue.json")
        self._ensure_queue_file()

        self._candado_archivo = None
        if "--server" not in sys.argv:
            self.sync_worker = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_worker.start()

    def _ensure_queue_file(self):
        if not os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(f"No se pudo crear offline_queue: {e}")

    def _volcar_cola(self, queue) -> None:
        """Reemplaza el archivo entero. Un corte deja la cola anterior, no una vacía."""
        temporal = self.queue_file + ".tmp"
        with open(temporal, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, self.queue_file)

    def guardar_venta_offline(self, venta_data, items, fiado=None):
        """Guarda la venta en el JSON local cuando la LAN falla."""
        candado = self._esperar_candado()
        if candado is None:
            logger.error("Cola ocupada. La venta quedó en la base local y no se pudo encolar.")
            return
        try:
            self._encolar(venta_data, items, fiado)
        finally:
            self._soltar_candado(candado)

    def _encolar(self, venta_data, items, fiado=None) -> None:
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)

            registro = {
                "venta_data": venta_data,
                "items": items,
                "timestamp": time.time(),
            }
            if fiado:
                registro["fiado"] = fiado
            queue.append(registro)
            self._volcar_cola(queue)
            logger.info("Venta guardada en BUFFER OFFLINE.")
            self._avisar_venta_sin_maestra(venta_data)
        except Exception as e:
            logger.error(f"Error escribiendo en buffer offline: {e}")

    def _avisar_venta_sin_maestra(self, venta_data):
        """Nexus escucha este aviso en la LAN. No espera a que la venta suba a la maestra."""
        datos = {
            "total": (venta_data or {}).get("total", 0),
            "metodo_pago": (venta_data or {}).get("metodo_pago", ""),
            "caja_id": (venta_data or {}).get("caja_id", 1),
            "request_id": (venta_data or {}).get("request_id") or "",
            "pago_efectivo": (venta_data or {}).get("pago_efectivo", 0),
            "pago_otro": (venta_data or {}).get("pago_otro", 0),
            "fuera_de_maestra": True,
        }
        try:
            from src.central_red_global.network_engine import get_network_engine

            engine = get_network_engine()
            if engine is not None:
                engine.broadcast("VENTA_NUEVA", datos)
                return
        except Exception as e:
            logger.warning(f"No se pudo avisar la venta por el motor de red: {e}")
        try:
            import socket
            from src.central_red_global.network_engine import NEXUS_UDP_PORT
            from src.config import config

            host = socket.gethostname()
            caja = datos["caja_id"] or config.get("caja_id", 1)
            payload = {
                "origen": f"{host}|cajero|caja{caja}",
                "tipo": "VENTA_NUEVA",
                "datos": datos,
                "ts": time.time(),
            }
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(
                    json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    ("255.255.255.255", NEXUS_UDP_PORT),
                )
            finally:
                sock.close()
        except Exception as e:
            logger.warning(f"Venta en cola; Nexus no recibió el aviso: {e}")

    def sync_pendientes(self):
        """Sincroniza ventas en offline_queue.json hacia la base de datos."""
        from src.base_de_datos.database import db_manager
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception as e:
            logger.error("Cola ilegible. No se toca: %s", e)
            return 0
        if not isinstance(queue, list) or not queue:
            return 0

        subidas = 0
        changed = False
        host = ""
        try:
            from src.central_red_global.master_presence import es_pc_maestra_local

            host = "127.0.0.1" if es_pc_maestra_local() else (db_manager._host_tienda() or "")
        except Exception:
            host = ""
        for record in queue:
            if not isinstance(record, dict):
                continue
            # La misma titular ya lo aceptó: no se reenvía. Si cambió la PC, sí.
            if record.get("en_titular") and host and record.get("titular_ip") == host:
                continue
            if not db_manager.sync_venta_to_master(
                record.get("venta_data") or {}, record.get("items") or [], record.get("fiado")
            ):
                break
            subidas += 1
            rid = str((record.get("venta_data") or {}).get("request_id") or "")
            try:
                from src.central_red_global.servidor.pareja.acuse import debe_esperar

                esperar = debe_esperar(rid)
            except Exception:
                esperar = False
            if esperar:
                record["en_titular"] = True
                record["titular_ip"] = host
            else:
                record["_soltar"] = True
            changed = True

        if changed:
            pendientes = []
            for record in queue:
                if isinstance(record, dict) and record.pop("_soltar", False):
                    continue
                pendientes.append(record)
            try:
                self._volcar_cola(pendientes)
                logger.info(f"{subidas} ventas offline sincronizadas.")
            except Exception as e:
                logger.error(f"Error actualizando cola post-sync: {e}")
        self._pedir_acuse(queue)
        return subidas

    def _cola_en_titular(self) -> list:
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            return []
        if not isinstance(queue, list):
            return []
        return [r for r in queue if isinstance(r, dict) and r.get("en_titular")]

    def _pedir_acuse(self, queue) -> None:
        ids = [
            str((r.get("venta_data") or {}).get("request_id") or "")
            for r in queue
            if isinstance(r, dict) and r.get("en_titular")
        ]
        ids = [i for i in ids if i]
        if not ids:
            return
        try:
            from src.central_red_global.servidor.pareja.acuse import pedir

            pedir(ids)
        except Exception:
            pass

    def soltar_confirmados(self, ids) -> int:
        """La reserva ya tiene estos tickets. Salen de la cola."""
        confirmados = {str(i).strip() for i in ids if str(i or "").strip()}
        if not confirmados:
            return 0
        candado = self._tomar_candado()
        if candado is None:
            return 0
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                queue = json.load(f)
            if not isinstance(queue, list):
                return 0
            queda = []
            soltados = 0
            for record in queue:
                if not isinstance(record, dict):
                    queda.append(record)
                    continue
                rid = str((record.get("venta_data") or {}).get("request_id") or "")
                if record.get("en_titular") and rid in confirmados:
                    soltados += 1
                    continue
                queda.append(record)
            if soltados:
                self._volcar_cola(queda)
                logger.info("tickets  la reserva los tiene: %s", soltados)
            return soltados
        except Exception as e:
            logger.warning("cola  no se pudo soltar el acuse: %s", e)
            return 0
        finally:
            self._soltar_candado(candado)

    def obtener_resumen_completo_pendientes(self) -> dict:
        """Devuelve desglose completo de tickets y cambios de negocio offline pendientes."""
        from src.base_de_datos.offline_nutricion import offline_nutricion_manager
        n_ventas = self.obtener_cantidad_pendientes()
        resumen_nutr = offline_nutricion_manager.obtener_resumen_pendientes()
        return {
            "ventas": n_ventas,
            "productos": resumen_nutr.get("productos", 0),
            "recepciones": resumen_nutr.get("recepciones", 0),
            "clientes": resumen_nutr.get("clientes", 0),
            "total": n_ventas + resumen_nutr.get("total", 0)
        }

    def obtener_cantidad_pendientes(self) -> int:
        """Devuelve el total de tickets offline en espera."""
        try:
            if not os.path.exists(self.queue_file):
                return 0
            with open(self.queue_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0

    def subir_colas(self) -> dict:
        """Sube tickets y cambios a la maestra. Si no contesta, la cola queda."""
        candado = self._tomar_candado()
        if candado is None:
            return {"ok": False, "ocupado": True, "ventas": 0, "stats": {}}
        try:
            from src.base_de_datos.database import db_manager
            from src.base_de_datos.offline_nutricion import offline_nutricion_manager

            host = ""
            try:
                host = db_manager._host_tienda()
            except Exception:
                host = ""
            if not host or not db_manager._puerto_maestra_vivo(host):
                try:
                    from src.central_red_global.servidor.pareja.buscar import buscar

                    host = buscar()
                except Exception:
                    host = host or ""
            if not host or not db_manager._puerto_maestra_vivo(host):
                return {"ok": False, "ocupado": False, "ventas": 0, "stats": {}}
            if getattr(db_manager, "db_engine_type", "") != "mariadb" or getattr(db_manager, "_forced_local_offline", False):
                db_manager.reconectar_mariadb(host)
                db_manager.is_master = False
            ok, _msg, stats = offline_nutricion_manager.nutrir_maestra(db_manager)
            ventas = int(self.sync_pendientes() or 0)
            stats = stats or {}
            cambios = int(stats.get("productos", 0) or 0) + int(stats.get("recepciones", 0) or 0) + int(stats.get("clientes", 0) or 0)
            if ventas or cambios:
                logger.info("tickets  subidos a la maestra: %s  cambios %s", ventas, cambios)
                try:
                    from src.central_red_global.sync_tienda.aviso_tv import avisar_datos_nuevos

                    avisar_datos_nuevos()
                except Exception:
                    pass
            return {"ok": bool(ok), "ocupado": False, "ventas": ventas, "stats": stats}
        except Exception as e:
            logger.warning("cola  no se pudo subir: %s", e)
            return {"ok": False, "ocupado": False, "ventas": 0, "stats": {}}
        finally:
            self._soltar_candado(candado)

    def _esperar_candado(self, segundos: int = 60):
        """Espera a que la otra subida suelte la cola. Si no hay candado, no pisa el archivo."""
        limite = time.time() + segundos
        while True:
            candado = self._tomar_candado()
            if candado is not None:
                return candado
            if time.time() >= limite:
                return None
            time.sleep(0.2)

    def _tomar_candado(self):
        try:
            import msvcrt
        except ImportError:
            return "sin"
        carpeta = os.path.join(self.base_path, "locks")
        os.makedirs(carpeta, exist_ok=True)
        archivo = open(os.path.join(carpeta, "cola_maestra.lock"), "a+b")
        archivo.seek(0)
        if not archivo.read(1):
            archivo.write(b" ")
            archivo.flush()
        archivo.seek(0)
        try:
            msvcrt.locking(archivo.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            archivo.close()
            return None
        return archivo

    def _soltar_candado(self, archivo) -> None:
        if archivo in (None, "sin"):
            return
        try:
            import msvcrt

            archivo.seek(0)
            msvcrt.locking(archivo.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
        try:
            archivo.close()
        except Exception:
            pass

    def ejecutar_ciclo_nutricion_completo(self, db_manager) -> tuple[bool, str]:
        """
        Ciclo Maestro-Esclavo Empresarial:
        FASE 1 (Nutrir Maestra - Upload):
          - Sube modificaciones de productos y precios hechas en casa.
          - Sube recepciones de mercadería y compras cargadas con escáner.
          - Sube altas y ediciones de clientes.
          - Sube tickets de venta guardados en el buffer offline.
          - Avisa por red LAN a todas las terminales y TVs.
        FASE 2 (Nutrir Notebook - Download):
          - Descarga el catálogo consolidado y departamentos a SQLite local (punpro.db).
          - Descarga la cartera de clientes actualizada a SQLite local.
          - Descarga las ventas recientes para auditoría fuera de línea.
          - Refresca el espejo total de la tienda (espejo_tienda.db) para el modo Jefe.
        """
        if getattr(db_manager, "db_engine_type", "") != "mariadb" or not db_manager.is_connected():
            return False, "MariaDB Maestra no está disponible para iniciar la nutrición."

        logger.info("⚡ Iniciando Ciclo de Nutrición Bidireccional con la Maestra...")

        # --- FASE 1: NUTRIR MAESTRA (UPLOAD) ---
        subida = self.subir_colas()
        if subida.get("ocupado"):
            return False, "Otra subida de la cola ya está en curso."
        if not subida.get("ok"):
            return False, "La cola sigue en esta PC. La maestra no recibió el envío."
        stats_nutr = subida.get("stats") or {}
        sincronizadas_ventas = int(subida.get("ventas") or 0)

        # Difundir evento a la red LAN y cartelería
        try:
            from src.central_red_global.sync_tienda.aviso_tv import avisar_datos_nuevos
            avisar_datos_nuevos()
        except Exception:
            pass

        # --- FASE 2: NUTRIR NOTEBOOK (DOWNLOAD) ---
        self._replicar_catalogo_local(db_manager)

        # Refrescar espejo total para Jefe / Auditoría
        try:
            from src.jefe.nodo_portable.espejo import copia
            copia.refrescar(completo=False)
        except Exception as e_esp:
            logger.debug(f"Aviso refrescando espejo local: {e_esp}")

        resumen = (
            f"🚀 Nutrición Bidireccional exitosa:\n"
            f"• Subidos a Maestra: {stats_nutr.get('productos', 0)} productos, "
            f"{stats_nutr.get('recepciones', 0)} recepciones, {stats_nutr.get('clientes', 0)} clientes, "
            f"{sincronizadas_ventas} tickets de venta.\n"
            f"• Descargados a Notebook: Catálogo, clientes y ventas consolidados para trabajo offline."
        )
        logger.info(resumen)
        return True, resumen

    def forzar_sincronizacion(self) -> tuple[bool, str]:
        """Intenta reconectar a la Maestra y ejecutar el ciclo de nutrición completo."""
        from src.base_de_datos.database import db_manager
        host = ""
        try:
            host = db_manager._host_tienda()
        except Exception:
            pass
        if not host:
            return False, "No hay IP de PC Maestra configurada."

        if not db_manager._puerto_maestra_vivo(host):
            tot = self.obtener_resumen_completo_pendientes()
            return (
                False,
                f"La PC Maestra ({host}) no responde en la red.\n"
                f"Tus datos siguen 100% seguros en modo offline local ({tot['total']} cambios/ventas guardados)."
            )

        try:
            db_manager.reconectar_mariadb(host)
            db_manager.is_master = False
            ok, msg = self.ejecutar_ciclo_nutricion_completo(db_manager)
            return ok, msg
        except Exception as e:
            return False, f"Error al sincronizar con Maestra: {e}"

    def _replicar_catalogo_local(self, db_manager):
        """Descarga copia fiel del catálogo, departamentos, clientes y ventas recientes al SQLite local."""
        try:
            import sqlite3
            local_db_path = os.path.join(self.base_path, "punpro.db")
            conn_loc = sqlite3.connect(local_db_path)
            c_loc = conn_loc.cursor()

            # 1. Catálogo de productos
            prods = db_manager.execute_query("""
                SELECT id, codigo, nombre, precio, stock, categoria, departamento, unidad, costo, 
                       es_pesable, cant_mayoreo, precio_mayoreo, stock_minimo, stock_maximo,
                       cant_oferta, precio_oferta, tipo_unidad_oferta, precio_oferta_relampago
                FROM productos
            """)
            if prods:
                c_loc.execute("""
                    CREATE TABLE IF NOT EXISTS productos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT,
                        nombre TEXT,
                        precio REAL DEFAULT 0,
                        stock REAL DEFAULT 0,
                        categoria TEXT DEFAULT 'GENERAL',
                        departamento TEXT DEFAULT '',
                        unidad TEXT DEFAULT 'UN',
                        costo REAL DEFAULT 0,
                        es_pesable INTEGER DEFAULT 0,
                        cant_mayoreo REAL DEFAULT 0,
                        precio_mayoreo REAL DEFAULT 0,
                        stock_minimo REAL DEFAULT 0,
                        stock_maximo REAL DEFAULT 0,
                        cant_oferta REAL DEFAULT 0,
                        precio_oferta REAL DEFAULT 0,
                        tipo_unidad_oferta TEXT DEFAULT 'Unidades',
                        precio_oferta_relampago REAL DEFAULT 0
                    )
                """)
                c_loc.execute("DELETE FROM productos")

                reg_prods = [
                    (p.get('id'), p.get('codigo'), p.get('nombre'), p.get('precio', 0),
                     p.get('stock', 0), p.get('categoria', 'GENERAL'), p.get('departamento', ''),
                     p.get('unidad', 'UN'), p.get('costo', 0), p.get('es_pesable', 0),
                     p.get('cant_mayoreo', 0), p.get('precio_mayoreo', 0),
                     p.get('stock_minimo', 0), p.get('stock_maximo', 0),
                     p.get('cant_oferta', 0), p.get('precio_oferta', 0),
                     p.get('tipo_unidad_oferta', 'Unidades'), p.get('precio_oferta_relampago', 0))
                    for p in prods
                ]

                c_loc.executemany("""
                    INSERT INTO productos (
                        id, codigo, nombre, precio, stock, categoria, departamento, unidad, costo,
                        es_pesable, cant_mayoreo, precio_mayoreo, stock_minimo, stock_maximo,
                        cant_oferta, precio_oferta, tipo_unidad_oferta, precio_oferta_relampago
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, reg_prods)

            # 2. Departamentos e impuestos
            deptos = db_manager.execute_query("SELECT id, nombre, iva FROM departamentos")
            if deptos:
                c_loc.execute("CREATE TABLE IF NOT EXISTS departamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL, iva REAL DEFAULT 21.0)")
                c_loc.execute("DELETE FROM departamentos")
                reg_deptos = [(d.get('id'), d.get('nombre'), d.get('iva', 21.0)) for d in deptos]
                c_loc.executemany("INSERT INTO departamentos (id, nombre, iva) VALUES (?,?,?)", reg_deptos)

            # 3. Clientes y límites de crédito
            clis = db_manager.execute_query("""
                SELECT id, nombre, telefono, dni, direccion, limite_credito, deuda_actual,
                       tipo_cliente, plazo_dias, uid, origen_pc, creado_por, creado_en, actualizado_en
                FROM clientes
            """)
            if clis:
                c_loc.execute("""
                    CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT,
                        telefono TEXT,
                        limite_credito REAL DEFAULT 0,
                        deuda_actual REAL DEFAULT 0,
                        fecha_registro TEXT,
                        dni TEXT,
                        tipo_cliente TEXT DEFAULT 'regular',
                        direccion TEXT,
                        uid TEXT,
                        origen_pc TEXT,
                        creado_por TEXT,
                        creado_en TEXT,
                        actualizado_en TEXT,
                        plazo_dias INTEGER DEFAULT 0
                    )
                """)
                c_loc.execute("DELETE FROM clientes")
                reg_clis = [
                    (c.get('id'), c.get('nombre'), c.get('telefono'), c.get('limite_credito', 0),
                     c.get('deuda_actual', 0), c.get('creado_en') or '', c.get('dni'),
                     c.get('tipo_cliente', 'regular'), c.get('direccion'), c.get('uid'),
                     c.get('origen_pc'), c.get('creado_por'), c.get('creado_en'),
                     c.get('actualizado_en'), c.get('plazo_dias', 0))
                    for c in clis
                ]
                c_loc.executemany("""
                    INSERT INTO clientes (
                        id, nombre, telefono, limite_credito, deuda_actual, fecha_registro,
                        dni, tipo_cliente, direccion, uid, origen_pc, creado_por, creado_en,
                        actualizado_en, plazo_dias
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, reg_clis)

            # 4. Ventas y Detalles de los últimos 30 días (para auditoría en la notebook)
            ventas_rec = db_manager.execute_query("""
                SELECT id, fecha, total, pago_con, cambio, pago_efectivo, pago_otro, usuario,
                       estado, metodo_pago, caja_id, descuento, recargo, request_id, cliente_nombre
                FROM ventas
                WHERE fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                ORDER BY id DESC
            """)
            if ventas_rec:
                reg_v = [
                    (v.get('id'), str(v.get('fecha')), v.get('total', 0), v.get('pago_con', 0),
                     v.get('cambio', 0), v.get('pago_efectivo', 0), v.get('pago_otro', 0),
                     str(v.get('usuario') or ''), v.get('estado', 'COMPLETADA'),
                     v.get('metodo_pago', 'Efectivo'), v.get('caja_id', 1),
                     v.get('descuento', 0), v.get('recargo', 0), v.get('request_id'),
                     v.get('cliente_nombre'))
                    for v in ventas_rec
                ]
                c_loc.executemany("""
                    INSERT OR REPLACE INTO ventas (
                        id, fecha, total, pago_con, cambio, pago_efectivo, pago_otro, usuario,
                        estado, metodo_pago, caja_id, descuento, recargo, request_id, cliente_nombre
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, reg_v)

                v_ids = [v.get('id') for v in ventas_rec if v.get('id')]
                if v_ids:
                    min_id = min(v_ids)
                    detalles_rec = db_manager.execute_query("""
                        SELECT id, venta_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal
                        FROM detalles_ventas
                        WHERE venta_id >= ?
                    """, (min_id,))
                    if detalles_rec:
                        reg_d = [
                            (d.get('id'), d.get('venta_id'), d.get('producto_id'),
                             d.get('nombre_producto', ''), d.get('cantidad', 1),
                             d.get('precio_unitario', 0), d.get('subtotal', 0))
                            for d in detalles_rec
                        ]
                        c_loc.executemany("""
                            INSERT OR REPLACE INTO detalles_ventas (
                                id, id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal
                            ) VALUES (?,?,?,?,?,?,?)
                        """, reg_d)

            conn_loc.commit()
            conn_loc.close()
            logger.info("Modo Offline: Catálogo, departamentos, clientes y ventas recientes sincronizados a SQLite local.")
        except Exception as e_repl:
            logger.warning(f"Modo Offline: Falló la réplica local de datos: {e_repl}")

    def _sync_loop(self):
        """Monitorea la red cada 15s: auto-reconecta si vuelve la maestra y ejecuta ciclo de nutrición."""
        from src.base_de_datos.database import db_manager

        loop_counter = 0

        while True:
            time.sleep(15)
            loop_counter += 1

            # 1. Comprobar si la PC Maestra volvió a la red ("oler la red WiFi de la tienda")
            host = ""
            try:
                host = db_manager._host_tienda()
            except Exception:
                host = ""

            estaba_offline = bool(getattr(db_manager, "_forced_local_offline", False) or getattr(db_manager, "db_engine_type", "") != "mariadb")
            if host and estaba_offline:
                if db_manager._puerto_maestra_vivo(host):
                    try:
                        db_manager.reconectar_mariadb(host)
                        db_manager.is_master = False
                        logger.info(f"🟢 PC Maestra en {host} detectada en la red WiFi. Iniciando Nutrición...")
                        self.ejecutar_ciclo_nutricion_completo(db_manager)
                    except Exception as ex_r:
                        logger.debug(f"Aviso al reconectar MariaDB en segundo plano: {ex_r}")

            # 2. Descargar imágenes de cartelería cada ~2 minutos
            if loop_counter % 8 == 0 and not db_manager.is_master:
                try:
                    from src.central_red_global.sync_tienda import bajar_pngs_de_maestra
                    bajar_pngs_de_maestra()
                except Exception:
                    pass

            # 3. Réplica periódica del catálogo (cada ~5 minutos si estamos online)
            if loop_counter >= 20:
                loop_counter = 0
                if not db_manager.is_master and getattr(db_manager, 'mariadb_engine', None):
                    self._replicar_catalogo_local(db_manager)

            # 4. Sincronizar cambios offline pendientes si estamos online
            if getattr(db_manager, "db_engine_type", "") == "mariadb" and getattr(db_manager, "mariadb_engine", None):
                resumen_pend = self.obtener_resumen_completo_pendientes()
                if resumen_pend.get("total", 0) > 0:
                    try:
                        self.subir_colas()
                    except Exception as e_q:
                        logger.debug(f"Aviso vaciando colas offline en background: {e_q}")

offline_sync_manager = OfflineSync()
