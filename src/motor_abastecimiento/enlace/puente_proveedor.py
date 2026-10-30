from src.base_de_datos.database import db_manager
from src.logger import logger

TABLA_MAPEO = "abastecimiento_proveedor_map"
_tabla_lista = False

def _es_maria() -> bool:
    return getattr(db_manager, "db_engine_type", "") == "mariadb"


def _fila(row) -> dict:
    """La copia de la tienda ya es dict. SQLite local devuelve una fila sin .get."""
    if isinstance(row, dict):
        return row
    if hasattr(row, "keys"):
        return {k: row[k] for k in row.keys()}
    return {}


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

def _dejar_enlace_en_casa(ficha, criterio_tipo, criterio_valor, email) -> dict | bool:
    """Guarda el enlace en esta PC. El id real se escribe al volver a la tienda."""
    from src.base_de_datos.offline_nutricion import offline_nutricion_manager

    tipo = str(criterio_tipo or "").strip().lower()
    valor = str(criterio_valor or "").strip().upper()
    nombre = str(ficha.get("nombre") or "").strip()
    if not tipo or not valor or not nombre:
        return False
    telefono = str(ficha.get("telefono") or "")
    if not offline_nutricion_manager.encolar_vinculo(
        tipo, valor, nombre, telefono, email, ficha.get("id") or 0,
    ):
        return False
    if not _es_maria():
        try:
            asegurar_tabla_enlace()
            pid = int(ficha.get("id") or 0) or None
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
            db_manager.execute_non_query(sql, (tipo, valor, nombre, telefono, email or "", pid))
        except Exception as e:
            logger.warning(f"El enlace quedó en la cola y no en la copia local: {e}")
    salida = dict(ficha)
    salida["pendiente"] = True
    salida["email"] = email or ""
    return salida


def asignar_proveedor(
    criterio_tipo, criterio_valor, proveedor_nombre,
    proveedor_telefono='', proveedor_email='', proveedor_id=None,
):
    """
    Registra o actualiza el enlace. Con la tienda, usa el id de la maestra.
    En casa deja el enlace en esta PC y el id nace al volver.
    """
    from src.proveedor_global.backend.ficha import FichaProveedor
    from src.proveedor_global.backend.motor_proveedor import MotorProveedor

    en_casa = not MotorProveedor.tienda_disponible()
    if not proveedor_id:
        ficha = FichaProveedor.obtener_o_crear(proveedor_nombre, proveedor_telefono)
        if not ficha:
            logger.warning("No se pudo guardar el proveedor ni en la tienda ni en esta PC.")
            return False
    else:
        ficha = {
            "id": proveedor_id,
            "codigo": "",
            "nombre": str(proveedor_nombre or "").strip(),
            "telefono": str(proveedor_telefono or "").strip(),
            "email": str(proveedor_email or "").strip(),
        }
    if en_casa or not ficha.get("id"):
        return _dejar_enlace_en_casa(ficha, criterio_tipo, criterio_valor, proveedor_email)
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


def quitar_proveedor(criterio_tipo, criterio_valor) -> bool:
    """Saca el enlace de esta PC y deja la baja para que no vuelva al reconectar."""
    tipo = str(criterio_tipo or "").strip().lower()
    valor = str(criterio_valor or "").strip().upper()
    if not tipo or not valor:
        return False
    asegurar_tabla_enlace()
    ok = db_manager.execute_non_query(
        f"DELETE FROM {TABLA_MAPEO} "
        "WHERE LOWER(criterio_tipo) = ? AND UPPER(criterio_valor) = ?",
        (tipo, valor),
    )
    try:
        from src.base_de_datos.offline_nutricion import offline_nutricion_manager

        encolado = offline_nutricion_manager.quitar_vinculo(tipo, valor)
    except Exception as e:
        logger.warning("No se pudo anotar la baja del enlace: %s", e)
        encolado = False
    return bool(ok or encolado)


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
    filas = []
    try:
        filas = db_manager.execute_query(consulta) or []
    except Exception as e:
        logger.warning(f"Enlace sin ficha, se lee el nombre guardado: {e}")
        try:
            filas = db_manager.execute_query(
                f"SELECT * FROM {TABLA_MAPEO} ORDER BY proveedor_nombre ASC"
            ) or []
        except Exception as error:
            logger.error(f"Error al leer mapeos de {TABLA_MAPEO}: {error}")
            filas = []
    limpias = [f for f in (_fila(row) for row in filas) if f]
    return _sumar_vinculos_en_casa(limpias)


def _sumar_vinculos_en_casa(filas):
    """El enlace armado en casa agrupa el pedido aunque el id todavía no exista."""
    try:
        from src.base_de_datos.offline_nutricion import offline_nutricion_manager

        pendientes = offline_nutricion_manager.vinculos_pendientes()
    except Exception:
        return filas
    if not pendientes:
        return filas
    bajas = set()
    altas = []
    for vinculo in pendientes:
        tipo = str(vinculo.get("criterio_tipo") or "").lower()
        valor = str(vinculo.get("criterio_valor") or "").upper()
        if vinculo.get("baja"):
            bajas.add((tipo, valor))
        else:
            altas.append(vinculo)
    if bajas:
        filas = [
            f for f in filas
            if (
                str((f or {}).get("criterio_tipo") or "").lower(),
                str((f or {}).get("criterio_valor") or "").upper(),
            ) not in bajas
        ]
    indice = {}
    for i, fila in enumerate(filas):
        if not isinstance(fila, dict):
            continue
        clave = (
            str(fila.get("criterio_tipo") or "").lower(),
            str(fila.get("criterio_valor") or "").upper(),
        )
        indice[clave] = i
    for vinculo in altas:
        tipo = str(vinculo.get("criterio_tipo") or "").lower()
        valor = str(vinculo.get("criterio_valor") or "").upper()
        pid = int(vinculo.get("proveedor_id") or 0) or None
        fila = {
            "criterio_tipo": tipo,
            "criterio_valor": valor,
            "proveedor_nombre": vinculo.get("proveedor_nombre") or "",
            "proveedor_telefono": vinculo.get("proveedor_telefono") or "",
            "proveedor_email": vinculo.get("proveedor_email") or "",
            "proveedor_id": pid,
            "proveedor_codigo": "" if pid else "EN CASA",
        }
        clave = (tipo, valor)
        if clave in indice:
            filas[indice[clave]] = fila
        else:
            filas.append(fila)
            indice[clave] = len(filas) - 1
    return filas


def resolver_proveedor(mapeos, producto) -> dict | None:
    """Primero el producto, después el departamento. Si no hay regla, None."""
    map_por_prod = {}
    map_por_depto = {}
    for cruda in mapeos or []:
        m = cruda if isinstance(cruda, dict) else _fila(cruda)
        if not m:
            continue
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
            if str(codigo_prov).upper() == "EN CASA":
                codigo_prov = ""
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
                "costo_total_estimado": 0.0,
                "presupuesto_estimado": 0.0,
            }

        pedidos_por_proveedor[nombre_prov]["items"].append(p)
        if not (p.get("es_formula") and float(p.get("cantidad_a_pedir") or 0) <= 0):
            pedidos_por_proveedor[nombre_prov]["total_items"] += 1
        pedidos_por_proveedor[nombre_prov]["costo_total_estimado"] += p.get('costo_estimado_total', 0.0)
        pedidos_por_proveedor[nombre_prov]["presupuesto_estimado"] += p.get(
            "presupuesto_linea", p.get("costo_estimado_total", 0.0)
        )

    # Redondear costos totales
    for k in pedidos_por_proveedor:
        pedidos_por_proveedor[k]["costo_total_estimado"] = round(pedidos_por_proveedor[k]["costo_total_estimado"], 2)
        pedidos_por_proveedor[k]["presupuesto_estimado"] = round(pedidos_por_proveedor[k]["presupuesto_estimado"], 2)

    for m in mapeos or []:
        if not isinstance(m, dict):
            m = _fila(m)
        nombre = str((m or {}).get("proveedor_nombre") or "").strip()
        if not nombre or nombre in pedidos_por_proveedor:
            continue
        codigo_mapa = str(m.get("proveedor_codigo") or "")
        if codigo_mapa.upper() == "EN CASA":
            codigo_mapa = ""
        pedidos_por_proveedor[nombre] = {
            "proveedor": nombre,
            "proveedor_id": m.get("proveedor_id"),
            "codigo": codigo_mapa,
            "telefono": m.get("proveedor_telefono") or "",
            "email": m.get("proveedor_email") or "",
            "items": [],
            "total_items": 0,
            "costo_total_estimado": 0.0,
            "presupuesto_estimado": 0.0,
        }

    try:
        from src.proveedor_global.backend.ficha import FichaProveedor

        fichas = FichaProveedor.listar()
    except Exception:
        fichas = []
    for ficha in fichas or []:
        nombre = str(ficha.get("nombre") or "").strip()
        if not nombre or nombre in pedidos_por_proveedor:
            continue
        codigo = str(ficha.get("codigo") or "")
        if codigo.upper() == "EN CASA" or ficha.get("pendiente"):
            codigo = ""
        pedidos_por_proveedor[nombre] = {
            "proveedor": nombre,
            "proveedor_id": ficha.get("id") or None,
            "codigo": codigo,
            "telefono": ficha.get("telefono") or "",
            "email": "",
            "items": [],
            "total_items": 0,
            "costo_total_estimado": 0.0,
            "presupuesto_estimado": 0.0,
        }

    return pedidos_por_proveedor
