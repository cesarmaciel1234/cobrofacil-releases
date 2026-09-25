import unicodedata

from src.base_de_datos.database import db_manager
from src.repositories.cliente_repository import ClienteRepository


def _plegar(texto):
    base = unicodedata.normalize("NFD", str(texto or ""))
    sin = "".join(letra for letra in base if unicodedata.category(letra) != "Mn")
    return " ".join(sin.split()).casefold()


def _ficha(fila):
    if isinstance(fila, dict):
        return fila
    if hasattr(fila, "keys"):
        return {clave: fila[clave] for clave in fila.keys()}
    return {}


class MotorCuenta:
    """Lectura y escritura de la ficha. No cobra la venta."""

    def normalizar_dni(self, dni):
        return ClienteRepository.normalizar_dni(dni)

    def identificar_dni(self, dni):
        return ClienteRepository.verificar_y_crear_cliente(dni)

    def identificar_nombre(self, nombre):
        return ClienteRepository.verificar_y_crear_por_nombre(nombre)

    def obtener(self, cliente_id):
        if not cliente_id:
            return None
        return ClienteRepository.obtener_por_id(cliente_id)

    def credito_disponible(self, cliente):
        if not cliente:
            return 0.0
        return ClienteRepository.credito_disponible(cliente)

    def limite_excedido(self, cliente, monto):
        if not cliente:
            return True
        return ClienteRepository.limite_credito_excedido(cliente, float(monto or 0))

    def buscar_por_dni(self, dni):
        return ClienteRepository.buscar_por_dni(dni)

    def buscar_por_nombre(self, nombre):
        return ClienteRepository.buscar_por_nombre(nombre)

    def sugerir_nombres(self, texto):
        busqueda = _plegar(texto)
        if len(busqueda) < 2:
            return []
        filas = db_manager.execute_query(
            "SELECT id, nombre, dni, limite_credito, deuda_actual FROM clientes ORDER BY nombre ASC"
        ) or []
        salida = []
        for fila in filas:
            ficha = _ficha(fila)
            if busqueda in _plegar(ficha.get("nombre")):
                salida.append(ficha)
            if len(salida) >= 8:
                break
        return salida

    def buscar(self, texto):
        busqueda = (texto or "").strip()
        return db_manager.execute_query(
            "SELECT * FROM clientes WHERE nombre LIKE ? OR COALESCE(dni, '') LIKE ? "
            "ORDER BY deuda_actual DESC, nombre ASC",
            (f"%{busqueda}%", f"%{busqueda}%"),
        ) or []

    def listar(self):
        return db_manager.execute_query(
            "SELECT id, nombre, limite_credito, deuda_actual FROM clientes ORDER BY nombre ASC"
        ) or []

    def listar_con_deuda(self):
        return ClienteRepository.obtener_clientes_con_deuda()

    def ultimo_cargo(self, cliente_id):
        return db_manager.execute_scalar(
            "SELECT fecha FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'CARGO' "
            "ORDER BY fecha DESC LIMIT 1",
            (cliente_id,),
        )

    def movimientos(self, cliente_id):
        return db_manager.execute_query(
            "SELECT fecha, tipo, monto, saldo_resultante, descripcion, venta_id "
            "FROM cuenta_corriente WHERE cliente_id = ? ORDER BY fecha DESC, id DESC",
            (cliente_id,),
        ) or []

    def alta_regular(self, nombre, telefono, limite, dni):
        return db_manager.execute_non_query(
            "INSERT INTO clientes (nombre, telefono, limite_credito, dni, tipo_cliente) "
            "VALUES (?, ?, ?, ?, 'regular')",
            (nombre, telefono, limite, dni),
        )

    def actualizar_existente(self, cliente_id, nombre, telefono, limite, dni):
        return db_manager.execute_non_query(
            "UPDATE clientes SET nombre = ?, telefono = ?, limite_credito = ?, dni = ? WHERE id = ?",
            (nombre, telefono, limite, dni, cliente_id),
        )

    def actualizar_ficha(self, cliente_id, nombre, dni, telefono, direccion, tipo):
        return db_manager.execute_non_query(
            "UPDATE clientes SET nombre = ?, dni = ?, telefono = ?, direccion = ?, tipo_cliente = ? WHERE id = ?",
            (nombre, dni, telefono or None, direccion or None, tipo, cliente_id),
        )

    def fijar_limite(self, cliente_id, limite):
        return db_manager.execute_non_query(
            "UPDATE clientes SET limite_credito = ? WHERE id = ?",
            (limite, cliente_id),
        )

    def abonar(self, cliente_id, monto, descripcion):
        cliente = self.obtener(cliente_id)
        if not cliente:
            return False, 0.0, ""
        ficha = dict(cliente)
        deuda_actual = float(ficha.get("deuda_actual") or 0.0)
        nuevo_saldo = max(0.0, deuda_actual - float(monto or 0))
        nombre = ficha.get("nombre", "")
        db_manager.execute_non_query(
            "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
            (nuevo_saldo, cliente_id),
        )
        db_manager.execute_non_query(
            "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion) "
            "VALUES (?, 'ABONO', ?, ?, ?)",
            (cliente_id, monto, nuevo_saldo, descripcion),
        )
        return True, nuevo_saldo, nombre

    def cargar_manual(self, cliente_id, monto, descripcion):
        cliente = self.obtener(cliente_id)
        if not cliente:
            return False, 0.0, ""
        ficha = dict(cliente)
        deuda_actual = float(ficha.get("deuda_actual") or 0.0)
        monto = float(monto or 0)
        nombre = ficha.get("nombre", "")
        if monto <= 0:
            return False, deuda_actual, nombre
        nuevo_saldo = deuda_actual + monto
        bajo = db_manager.execute_non_query(
            "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
            (nuevo_saldo, cliente_id),
        )
        anotado = db_manager.execute_non_query(
            "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion) "
            "VALUES (?, 'CARGO', ?, ?, ?)",
            (cliente_id, monto, nuevo_saldo, descripcion),
        )
        if not bajo or not anotado:
            return False, deuda_actual, nombre
        return True, nuevo_saldo, nombre
