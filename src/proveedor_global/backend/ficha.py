"""Ficha del proveedor. El id nace en la maestra. En casa queda pendiente y se sube al volver."""

from __future__ import annotations

import uuid


def codigo_visible(proveedor_id: int) -> str:
    return f"P{int(proveedor_id):05d}"


def etiqueta(ficha: dict) -> str:
    nombre = str(ficha.get("nombre") or "").strip()
    codigo = str(ficha.get("codigo") or "").strip()
    if not codigo or codigo.upper() == "EN CASA" or ficha.get("pendiente"):
        return nombre
    return f"{codigo}  {nombre}".strip()


def nombre_de_eleccion(texto: str, ficha: dict | None) -> str:
    """Si eligió una ficha, el romaneo guarda el nombre. El código no entra en la deuda."""
    texto = (texto or "").strip()
    if isinstance(ficha, dict) and ficha.get("nombre"):
        nombre = str(ficha["nombre"]).strip()
        if texto == etiqueta(ficha) or texto == nombre:
            return nombre
    return texto or "Proveedor General"


class FichaProveedor:
    @staticmethod
    def _fila(row) -> dict | None:
        if not row:
            return None
        if isinstance(row, dict):
            return {
                "id": int(row.get("id") or 0),
                "codigo": str(row.get("codigo") or ""),
                "nombre": str(row.get("nombre") or ""),
                "telefono": str(row.get("telefono") or ""),
            }
        return {
            "id": int(row[0] or 0),
            "codigo": str(row[1] or ""),
            "nombre": str(row[2] or ""),
            "telefono": str(row[3] or ""),
        }

    @staticmethod
    def asegurar(db) -> None:
        motor = getattr(db, "manager", db)
        maria = getattr(motor, "db_engine_type", "") == "mariadb"
        if maria:
            ddl = """
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    codigo VARCHAR(16) NOT NULL,
                    nombre VARCHAR(255) NOT NULL,
                    telefono VARCHAR(64) NOT NULL DEFAULT '',
                    activo TINYINT NOT NULL DEFAULT 1,
                    UNIQUE KEY uq_proveedores_codigo (codigo)
                )
            """
        else:
            ddl = """
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    telefono TEXT NOT NULL DEFAULT '',
                    activo INTEGER NOT NULL DEFAULT 1
                )
            """
        db.execute_non_query(ddl)

    @staticmethod
    def listar() -> list[dict]:
        from src.proveedor_global.backend.motor_proveedor import MotorProveedor

        db, _modo = MotorProveedor._get_read_db("admin")
        if not db:
            salida = []
            FichaProveedor._sumar_pendientes(salida)
            return salida
        try:
            FichaProveedor.asegurar(db)
        except Exception:
            pass
        try:
            filas = db.execute_query(
                "SELECT id, codigo, nombre, telefono FROM proveedores "
                "WHERE activo = 1 ORDER BY nombre"
            ) or []
        except Exception:
            salida = []
            FichaProveedor._sumar_pendientes(salida)
            return salida
        salida = []
        for fila in filas:
            ficha = FichaProveedor._fila(fila)
            if ficha and ficha["id"] and ficha["nombre"]:
                salida.append(ficha)
        FichaProveedor._sumar_pendientes(salida)
        salida.sort(key=lambda ficha: ficha["nombre"].upper())
        return salida

    @staticmethod
    def _sumar_pendientes(salida: list[dict]) -> None:
        """Las fichas armadas en casa aparecen en el combo antes de tener id."""
        try:
            from src.base_de_datos.offline_nutricion import offline_nutricion_manager

            pendientes = offline_nutricion_manager.proveedores_pendientes()
        except Exception:
            return
        nombres = {ficha["nombre"].strip().upper() for ficha in salida}
        for pendiente in pendientes:
            nombre = str(pendiente.get("nombre") or "").strip()
            if not nombre or nombre.upper() in nombres:
                continue
            salida.append({
                "id": 0,
                "codigo": "EN CASA",
                "nombre": nombre,
                "telefono": str(pendiente.get("telefono") or ""),
                "pendiente": True,
            })
            nombres.add(nombre.upper())

    @staticmethod
    def crear(nombre: str, telefono: str = "") -> tuple[bool, dict | str]:
        """Con la tienda, crea el id. En casa guarda la ficha y el id nace mañana."""
        from src.base_de_datos.database import db_manager
        from src.proveedor_global.backend.motor_proveedor import MotorProveedor, _ConexionTienda

        nombre = (nombre or "").strip()
        telefono = (telefono or "").strip()
        if not nombre:
            return False, "Falta el nombre del proveedor."
        ya = FichaProveedor.buscar_por_nombre(nombre)
        if ya:
            return True, ya
        if not MotorProveedor.tienda_disponible():
            from src.base_de_datos.offline_nutricion import offline_nutricion_manager

            if not offline_nutricion_manager.encolar_proveedor(nombre, telefono):
                return False, "No se pudo guardar el proveedor en esta PC."
            return True, {
                "id": 0,
                "codigo": "EN CASA",
                "nombre": nombre,
                "telefono": telefono,
                "pendiente": True,
            }

        conn = MotorProveedor._abrir_conexion_tienda(db_manager)
        try:
            tienda = _ConexionTienda(db_manager, conn)
            FichaProveedor.asegurar(tienda)
            temporal = "T" + uuid.uuid4().hex[:12]
            if not tienda.execute_non_query(
                "INSERT INTO proveedores (codigo, nombre, telefono, activo) VALUES (?, ?, ?, 1)",
                (temporal, nombre, telefono),
            ):
                raise RuntimeError("La maestra no guardó la ficha.")
            ids = tienda.execute_query("SELECT LAST_INSERT_ID() AS id")
            fila = ids[0] if ids else None
            proveedor_id = int(fila["id"] if isinstance(fila, dict) else fila[0])
            if not proveedor_id:
                raise RuntimeError("La maestra no devolvió el id.")
            codigo = codigo_visible(proveedor_id)
            if not tienda.execute_non_query(
                "UPDATE proveedores SET codigo = ? WHERE id = ?",
                (codigo, proveedor_id),
            ):
                raise RuntimeError("La maestra no pudo anotar el código.")
            conn.commit()
            return True, {
                "id": proveedor_id,
                "codigo": codigo,
                "nombre": nombre,
                "telefono": telefono,
            }
        except Exception as error:
            try:
                conn.rollback()
            except Exception:
                pass
            motivo = getattr(error, "args", [None])
            texto = str(motivo[0] or error) if motivo else str(error)
            return False, texto or "No se pudo crear el proveedor."
        finally:
            conn.close()

    @staticmethod
    def actualizar(ficha: dict, nombre: str, telefono: str = "") -> tuple[bool, dict | str]:
        """Cambia nombre y teléfono. En casa reescribe la cola y los enlaces."""
        from src.base_de_datos.database import db_manager
        from src.proveedor_global.backend.motor_proveedor import MotorProveedor, _ConexionTienda

        nombre = (nombre or "").strip()
        telefono = (telefono or "").strip()
        anterior = str((ficha or {}).get("nombre") or "").strip()
        if not nombre:
            return False, "Falta el nombre del proveedor."
        otro = FichaProveedor.buscar_por_nombre(nombre)
        pid_ficha = int((ficha or {}).get("id") or 0)
        if otro and int(otro.get("id") or 0) not in (0, pid_ficha) and otro.get("nombre", "").upper() == nombre.upper():
            if anterior.upper() != nombre.upper():
                return False, "Ya hay un proveedor con ese nombre."
        pendiente = bool((ficha or {}).get("pendiente")) or pid_ficha <= 0
        if pendiente or not MotorProveedor.tienda_disponible():
            from src.base_de_datos.offline_nutricion import offline_nutricion_manager

            if not offline_nutricion_manager.actualizar_proveedor_pendiente(anterior, nombre, telefono):
                return False, "No se pudo guardar el cambio en esta PC."
            FichaProveedor._renombrar_enlace_local(anterior, nombre, telefono)
            salida = dict(ficha or {})
            salida.update({"nombre": nombre, "telefono": telefono, "pendiente": True, "id": pid_ficha})
            return True, salida

        conn = MotorProveedor._abrir_conexion_tienda(db_manager)
        try:
            tienda = _ConexionTienda(db_manager, conn)
            if not tienda.execute_non_query(
                "UPDATE proveedores SET nombre = ?, telefono = ? WHERE id = ?",
                (nombre, telefono, pid_ficha),
            ):
                raise RuntimeError("La maestra no guardó el cambio.")
            tienda.execute_non_query(
                "UPDATE abastecimiento_proveedor_map SET proveedor_nombre = ?, proveedor_telefono = ? "
                "WHERE proveedor_id = ? OR UPPER(proveedor_nombre) = UPPER(?)",
                (nombre, telefono, pid_ficha, anterior),
            )
            conn.commit()
            salida = dict(ficha or {})
            salida.update({"id": pid_ficha, "nombre": nombre, "telefono": telefono})
            return True, salida
        except Exception as error:
            try:
                conn.rollback()
            except Exception:
                pass
            return False, str(error) or "No se pudo editar el proveedor."
        finally:
            conn.close()

    @staticmethod
    def _renombrar_enlace_local(anterior: str, nombre: str, telefono: str) -> None:
        from src.base_de_datos.database import db_manager

        if not anterior:
            return
        try:
            db_manager.execute_non_query(
                "UPDATE abastecimiento_proveedor_map SET proveedor_nombre = ?, proveedor_telefono = ? "
                "WHERE UPPER(proveedor_nombre) = UPPER(?)",
                (nombre, telefono, anterior),
            )
        except Exception:
            pass

    @staticmethod
    def buscar_por_nombre(nombre: str) -> dict | None:
        from src.proveedor_global.backend.motor_proveedor import MotorProveedor

        limpio = (nombre or "").strip()
        if not limpio:
            return None
        db, _modo = MotorProveedor._get_read_db("admin")
        if not db:
            return None
        try:
            filas = db.execute_query(
                "SELECT id, codigo, nombre, telefono FROM proveedores "
                "WHERE UPPER(nombre) = UPPER(?) AND activo = 1",
                (limpio,),
            ) or []
        except Exception:
            return None
        return FichaProveedor._fila(filas[0]) if filas else None

    @staticmethod
    def obtener_o_crear(nombre: str, telefono: str = "") -> dict | None:
        """Reusa la ficha si el nombre ya está. En casa deja una ficha pendiente. No toca el romaneo."""
        limpio = (nombre or "").strip()
        if not limpio or limpio.upper() == "SIN PROVEEDOR ASIGNADO":
            return None
        ya = FichaProveedor.buscar_por_nombre(limpio)
        if ya:
            return ya
        ok, resultado = FichaProveedor.crear(limpio, telefono)
        return resultado if ok and isinstance(resultado, dict) else None
