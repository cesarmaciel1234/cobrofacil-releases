from src.base_de_datos.database import db_manager
from src.logger import logger

TABLA_MAPEO = "abastecimiento_proveedor_map"
_tabla_lista = False

def _es_maria() -> bool:
    return getattr(db_manager, "db_engine_type", "") == "mariadb"


def asegurar_tabla_enlace():
    """
    Crea la tabla aislada para relacionar departamentos o productos con proveedores,
    garantizando que la tabla original 'productos' no se toque ni se altere.
    """
    global _tabla_lista
    if _tabla_lista:
        return
    if _es_maria():
        sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLA_MAPEO} (
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
    else:
        sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLA_MAPEO} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criterio_tipo TEXT NOT NULL,
                criterio_valor TEXT NOT NULL,
                proveedor_nombre TEXT NOT NULL,
                proveedor_telefono TEXT DEFAULT '',
                proveedor_email TEXT DEFAULT '',
                proveedor_id INTEGER,
                UNIQUE(criterio_tipo, criterio_valor)
            )
        """
    try:
        db_manager.execute_non_query(sql)
        _asegurar_columna_id()
        _tabla_lista = True
    except Exception as e:
        logger.error(f"Error al asegurar tabla {TABLA_MAPEO}: {e}")


def _asegurar_columna_id():
    """Las fichas viejas no tienen proveedor_id. Se agrega sin tocar las filas."""
    try:
        if _es_maria():
            cols = db_manager.execute_query(f"SHOW COLUMNS FROM {TABLA_MAPEO}") or []
            nombres = [c.get("Field", "") if isinstance(c, dict) else c[0] for c in cols]
            if "proveedor_id" not in nombres:
                db_manager.execute_non_query(
                    f"ALTER TABLE {TABLA_MAPEO} ADD COLUMN proveedor_id INT NULL"
                )
        else:
            cols = db_manager.execute_query(f"PRAGMA table_info({TABLA_MAPEO})") or []
            nombres = [c.get("name", "") if isinstance(c, dict) else c[1] for c in cols]
            if "proveedor_id" not in nombres:
                db_manager.execute_non_query(
                    f"ALTER TABLE {TABLA_MAPEO} ADD COLUMN proveedor_id INTEGER"
                )
    except Exception as e:
        logger.error(f"No se pudo agregar proveedor_id en {TABLA_MAPEO}: {e}")

def asignar_proveedor(
    criterio_tipo, criterio_valor, proveedor_nombre,
    proveedor_telefono='', proveedor_email='', proveedor_id=None,
):
    """
    Registra o actualiza el enlace. Crea o reusa la ficha en la maestra.
    Devuelve la ficha, o False si no hay tienda.
    """
    from src.proveedor_global.backend.ficha import FichaProveedor

    if proveedor_id is None:
        ficha = FichaProveedor.obtener_o_crear(proveedor_nombre, proveedor_telefono)
        if not ficha:
            logger.warning("Sin maestra no se asigna proveedor: no se inventa un id.")
            return False
    else:
        from src.proveedor_global.backend.motor_proveedor import MotorProveedor

        if not MotorProveedor.tienda_disponible():
            logger.error("Sin la maestra no se asigna el id de proveedor.")
            return False
        ficha = {
            "id": proveedor_id,
            "codigo": "",
            "nombre": str(proveedor_nombre or "").strip(),
            "telefono": str(proveedor_telefono or "").strip(),
            "email": str(proveedor_email or "").strip(),
        }
    asegurar_tabla_enlace()
    tipo = criterio_tipo.strip().lower()
    valor = str(criterio_valor).strip().upper()
    nombre = ficha["nombre"]
    telefono = ficha.get("telefono") or ""
    email = ficha.get("email") or ""
    proveedor_id = ficha["id"]
    if _es_maria():
        sql = f"""
            INSERT INTO {TABLA_MAPEO}
                (criterio_tipo, criterio_valor, proveedor_nombre, proveedor_telefono, proveedor_email, proveedor_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                proveedor_nombre=VALUES(proveedor_nombre),
                proveedor_telefono=VALUES(proveedor_telefono),
                proveedor_email=VALUES(proveedor_email),
                proveedor_id=VALUES(proveedor_id)
        """
    else:
        sql = f"""
            INSERT INTO {TABLA_MAPEO}
                (criterio_tipo, criterio_valor, proveedor_nombre, proveedor_telefono, proveedor_email, proveedor_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(criterio_tipo, criterio_valor)
            DO UPDATE SET
                proveedor_nombre=excluded.proveedor_nombre,
                proveedor_telefono=excluded.proveedor_telefono,
                proveedor_email=excluded.proveedor_email,
                proveedor_id=excluded.proveedor_id
        """
    try:
        ok = db_manager.execute_non_query(
            sql, (tipo, valor, nombre, telefono, email, proveedor_id)
        )
    except Exception as e:
        logger.error(f"Error al asignar proveedor en {TABLA_MAPEO}: {e}")
        return False
    if not ok:
        return False
    return ficha

def obtener_mapeos():
    """Retorna todos los enlaces vigentes de proveedores."""
    asegurar_tabla_enlace()
    try:
        from src.proveedor_global.backend.ficha import FichaProveedor

        FichaProveedor.asegurar(db_manager)
    except Exception as e:
        logger.warning(f"Ficha de proveedores no quedó lista: {e}")
    consulta = (
        f"SELECT m.*, p.codigo AS proveedor_codigo FROM {TABLA_MAPEO} m "
        "LEFT JOIN proveedores p ON p.id = m.proveedor_id "
        "ORDER BY m.proveedor_nombre ASC"
    )
    try:
        return db_manager.execute_query(consulta) or []
    except Exception as e:
        logger.warning(f"Enlace sin ficha, se lee el nombre guardado: {e}")
    try:
        return db_manager.execute_query(
            f"SELECT * FROM {TABLA_MAPEO} ORDER BY proveedor_nombre ASC"
        ) or []
    except Exception as e:
        logger.error(f"Error al leer mapeos de {TABLA_MAPEO}: {e}")
        return []


def resolver_proveedor(mapeos, producto) -> dict | None:
    """Primero el producto, después el departamento. Si no hay regla, None."""
    map_por_prod = {}
    map_por_depto = {}
    for m in mapeos or []:
        tipo = (m.get("criterio_tipo") or "").lower()
        val = (m.get("criterio_valor") or "").upper()
        info = {
            "id": m.get("proveedor_id"),
            "codigo": m.get("proveedor_codigo") or "",
            "nombre": m.get("proveedor_nombre"),
            "telefono": m.get("proveedor_telefono") or "",
            "email": m.get("proveedor_email") or "",
        }
        if tipo == "producto_id":
            map_por_prod[val] = info
        elif tipo == "departamento":
            map_por_depto[val] = info
    pid = str((producto or {}).get("id", "")).upper()
    depto = str((producto or {}).get("departamento", "")).strip().upper()
    return map_por_prod.get(pid) or map_por_depto.get(depto)

def asociar_proveedores_a_productos(productos_faltantes):
    """
    Toma la lista de productos faltantes y los agrupa por proveedor.
    Prioridad: 
    1. Si el producto tiene un proveedor asignado por 'producto_id', usa ese.
    2. Si el departamento tiene un proveedor asignado, usa ese.
    3. Si no tiene enlace, lo asigna a 'SIN PROVEEDOR ASIGNADO'.
    """
    asegurar_tabla_enlace()
    mapeos = obtener_mapeos()

    pedidos_por_proveedor = {}

    for p in productos_faltantes:
        prov = resolver_proveedor(mapeos, p)

        if prov and prov.get("nombre"):
            nombre_prov = prov["nombre"]
            tel_prov = prov["telefono"]
            email_prov = prov["email"]
            codigo_prov = prov.get("codigo") or ""
            id_prov = prov.get("id")
        else:
            nombre_prov = "SIN PROVEEDOR ASIGNADO"
            tel_prov = ""
            email_prov = ""
            codigo_prov = ""
            id_prov = None

        if nombre_prov not in pedidos_por_proveedor:
            pedidos_por_proveedor[nombre_prov] = {
                "proveedor": nombre_prov,
                "proveedor_id": id_prov,
                "codigo": codigo_prov,
                "telefono": tel_prov,
                "email": email_prov,
                "items": [],
                "total_items": 0,
                "costo_total_estimado": 0.0
            }

        pedidos_por_proveedor[nombre_prov]["items"].append(p)
        pedidos_por_proveedor[nombre_prov]["total_items"] += 1
        pedidos_por_proveedor[nombre_prov]["costo_total_estimado"] += p.get('costo_estimado_total', 0.0)

    # Redondear costos totales
    for k in pedidos_por_proveedor:
        pedidos_por_proveedor[k]["costo_total_estimado"] = round(pedidos_por_proveedor[k]["costo_total_estimado"], 2)

    return pedidos_por_proveedor
