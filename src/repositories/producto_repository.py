from src.base_de_datos.database import db_manager

class ProductoRepository:
    """
    Capa de acceso a datos para la tabla 'productos'.
    Aísla las consultas SQL de la Interfaz Gráfica.
    """

    @staticmethod
    def obtener_por_id(producto_id: str) -> dict:
        """Devuelve un producto por su ID (código de barras) o None si no existe."""
        query = "SELECT id, nombre, precio, cant_oferta, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, es_sos FROM productos WHERE id = ?"
        resultados = db_manager.execute_query(query, (producto_id,))
        if resultados:
            return resultados[0]
        return None

    @staticmethod
    def obtener_por_plu_balanza(plu_raw: str) -> dict | None:
        """Busca producto por PLU de balanza (id numérico, con/sin ceros, o campo codigo)."""
        plu_limpio = plu_raw.lstrip("0") or "0"
        candidates: list[str] = []
        for c in (plu_raw, plu_limpio):
            if c and c not in candidates:
                candidates.append(c)
        if plu_limpio.isdigit():
            n = int(plu_limpio)
            for c in (str(n), str(n).zfill(len(plu_raw))):
                if c not in candidates:
                    candidates.append(c)

        query = (
            "SELECT id, nombre, precio, stock, cant_oferta, precio_oferta, es_pesable, codigo "
            "FROM productos WHERE CAST(id AS CHAR) = ? OR codigo = ? LIMIT 1"
        )
        for c in candidates:
            rows = db_manager.execute_query(query, (c, c))
            if rows:
                return rows[0]
        return None

    @staticmethod
    def apagar_ofertas_sos_masivas():
        """Apaga todas las ofertas relámpago marcadas como SOS."""
        query = "UPDATE productos SET precio_oferta_relampago = 0 WHERE es_sos = 1"
        return db_manager.execute_non_query(query)

    @staticmethod
    def actualizar_precio_oferta_relampago(producto_id: str, nuevo_precio: float):
        """Actualiza la oferta relámpago de un producto específico."""
        query = "UPDATE productos SET precio_oferta_relampago = ? WHERE id = ?"
        return db_manager.execute_non_query(query, (nuevo_precio, producto_id))

    # --- MULTI-CÓDIGO CORPORATIVO (1 a N) ---
    @staticmethod
    def asegurar_tabla_codigos_adicionales():
        """Garantiza que la tabla de códigos adicionales exista."""
        db_manager.execute_non_query("""
            CREATE TABLE IF NOT EXISTS productos_codigos_adicionales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id BIGINT NOT NULL,
                codigo TEXT NOT NULL,
                tipo TEXT DEFAULT 'EAN',
                factor_unidades REAL DEFAULT 1.0,
                descripcion TEXT,
                creado_el DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    @staticmethod
    def obtener_codigos_adicionales(producto_id: int | str) -> list[dict]:
        """Obtiene la lista de códigos adicionales vinculados a un producto."""
        ProductoRepository.asegurar_tabla_codigos_adicionales()
        query = (
            "SELECT id, producto_id, codigo, tipo, factor_unidades, descripcion, creado_el "
            "FROM productos_codigos_adicionales WHERE producto_id = ? ORDER BY id ASC"
        )
        return db_manager.execute_query(query, (producto_id,)) or []

    @staticmethod
    def agregar_codigo_adicional(producto_id: int | str, codigo: str, tipo: str = "EAN",
                                 factor_unidades: float = 1.0, descripcion: str = "") -> tuple[bool, str]:
        """Agrega un código de barras adicional al producto (validando que no esté repetido)."""
        ProductoRepository.asegurar_tabla_codigos_adicionales()
        cod = str(codigo).strip()
        if not cod:
            return False, "El código no puede estar vacío."
        try:
            factor = float(factor_unidades) if factor_unidades else 1.0
            if factor <= 0:
                factor = 1.0
        except (ValueError, TypeError):
            factor = 1.0

        # Verificar si ya existe en codigos principales
        existe_principal = db_manager.execute_query(
            "SELECT id, nombre FROM productos WHERE codigo = ?", (cod,)
        )
        if existe_principal:
            return False, f"El código ya está asignado como código principal del producto #{existe_principal[0]['id']}."

        # Verificar si ya existe en adicionales
        existe_adic = db_manager.execute_query(
            "SELECT id, producto_id FROM productos_codigos_adicionales WHERE codigo = ?", (cod,)
        )
        if existe_adic:
            return False, f"El código ya está asignado como adicional al producto #{existe_adic[0]['producto_id']}."

        query = (
            "INSERT INTO productos_codigos_adicionales "
            "(producto_id, codigo, tipo, factor_unidades, descripcion) VALUES (?, ?, ?, ?, ?)"
        )
        ok = db_manager.execute_non_query(query, (producto_id, cod, tipo.upper(), factor, descripcion.strip()))
        if ok:
            return True, "Código adicional agregado exitosamente."
        return False, "Error al registrar el código en la base de datos."

    @staticmethod
    def eliminar_codigo_adicional(id_registro: int | str) -> bool:
        """Elimina un código adicional por su ID de registro."""
        ProductoRepository.asegurar_tabla_codigos_adicionales()
        query = "DELETE FROM productos_codigos_adicionales WHERE id = ?"
        return bool(db_manager.execute_non_query(query, (id_registro,)))

    @staticmethod
    def buscar_por_codigo_adicional(codigo: str) -> dict | None:
        """Busca si el código escaneado pertenece a un código secundario/bulto/DUN."""
        ProductoRepository.asegurar_tabla_codigos_adicionales()
        cod = str(codigo).strip()
        if not cod:
            return None
        query = (
            "SELECT p.*, ca.factor_unidades, ca.tipo AS tipo_codigo_adicional, ca.descripcion AS desc_codigo "
            "FROM productos_codigos_adicionales ca "
            "JOIN productos p ON ca.producto_id = p.id "
            "WHERE ca.codigo = ? LIMIT 1"
        )
        filas = db_manager.execute_query(query, (cod,))
        return filas[0] if filas else None
