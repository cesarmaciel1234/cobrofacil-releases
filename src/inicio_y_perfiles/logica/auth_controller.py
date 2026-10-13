import hashlib
from src.base_de_datos.database import db_manager
from src.config import config

class AuthController:
    """Controlador para la autenticación y selección de perfiles."""

    def __init__(self):
        pass

    def listar_credenciales(self, role: str):
        """Una sola lectura al abrir el login. Enter compara en memoria."""
        if role == "cajero_test":
            res = db_manager.execute_query(
                "SELECT id, username, password_hash, rol FROM usuarios WHERE rol = 'cajero'"
            )
            if not res:
                res = db_manager.execute_query(
                    "SELECT id, username, password_hash, rol FROM usuarios WHERE rol = 'admin'"
                )
        else:
            res = db_manager.execute_query(
                "SELECT id, username, password_hash, rol FROM usuarios WHERE rol = ?",
                (role,),
            )
        salida = []
        for fila in res or []:
            if hasattr(fila, "keys"):
                salida.append({k: fila[k] for k in fila.keys()})
            elif isinstance(fila, dict):
                salida.append(fila)
        return salida

    def get_users_by_role(self, role: str):
        """Devuelve la lista de nombres de usuario que tienen un rol específico."""
        return [r["username"] for r in self.listar_credenciales(role)]

    def authenticate(self, username: str, password_plain: str, cache=None) -> dict:
        """Compara el hash en memoria si hay cache. No vuelve a consultar la maestra."""
        hashed_input = hashlib.sha256(password_plain.encode()).hexdigest()
        buscado = (username or "").strip().casefold()
        filas = list(cache) if cache is not None else []
        if not filas:
            res = db_manager.execute_query(
                "SELECT id, username, password_hash, rol FROM usuarios WHERE username = ?",
                (username,),
            )
            for fila in res or []:
                filas.append({k: fila[k] for k in fila.keys()} if hasattr(fila, "keys") else fila)
        for db_user in filas:
            nombre = str(db_user.get("username") or "").strip().casefold()
            if nombre != buscado:
                continue
            if hashed_input != str(db_user.get("password_hash") or ""):
                return None
            return dict(db_user)
        return None

    def set_current_user(self, user_dict: dict):
        """Establece el usuario autenticado en la configuración global."""
        config.current_user = user_dict

    def is_master(self) -> bool:
        """Verifica si la base de datos está en modo master."""
        return db_manager.is_master

    def check_initial_admin(self) -> bool:
        """Verifica si la tabla usuarios está vacía."""
        res = db_manager.execute_query("SELECT COUNT(*) as count FROM usuarios")
        return res[0]['count'] == 0 if res else False

    def create_initial_admin(self, admin_pass: str):
        """Crea el administrador inicial si la base de datos de usuarios está vacía."""
        pwd_hash = hashlib.sha256(admin_pass.encode()).hexdigest()
        db_manager.execute_non_query(
            "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)",
            ("admin", pwd_hash, "admin")
        )

    def ensure_default_jefe(self):
        """Asegura que exista al menos un usuario con rol 'jefe'. Si no hay ninguno, crea 'jefe1' (pass: jefe1)."""
        res = db_manager.execute_query("SELECT COUNT(*) as count FROM usuarios WHERE rol = 'jefe'")
        if res and res[0]['count'] == 0:
            pwd_hash = hashlib.sha256("jefe1".encode()).hexdigest()
            db_manager.execute_non_query(
                "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)",
                ("jefe1", pwd_hash, "jefe")
            )

    def ensure_default_contabilidad(self):
        """Asegura que exista al menos un usuario con rol 'contabilidad'. Si no hay ninguno, crea 'contabilidad' (pass: contabilidad)."""
        res = db_manager.execute_query("SELECT COUNT(*) as count FROM usuarios WHERE rol = 'contabilidad'")
        if res and res[0]['count'] == 0:
            pwd_hash = hashlib.sha256("contabilidad".encode()).hexdigest()
            db_manager.execute_non_query(
                "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)",
                ("contabilidad", pwd_hash, "contabilidad")
            )
