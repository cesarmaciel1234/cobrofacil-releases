import hashlib
from src.base_de_datos.database import db_manager
from src.config import config

class AuthController:
    """Controlador para la autenticación y selección de perfiles."""

    def __init__(self):
        pass

    def get_users_by_role(self, role: str):
        """Devuelve la lista de nombres de usuario que tienen un rol específico.
        Si role es 'cajero_test', se usa como alias de 'cajero' pero permite buscar admin si está vacío."""
        if role == "cajero_test":
            res = db_manager.execute_query("SELECT username FROM usuarios WHERE rol = 'cajero'")
            if not res:
                res = db_manager.execute_query("SELECT username FROM usuarios WHERE rol = 'admin'")
            return [r['username'] for r in res]
        else:
            res = db_manager.execute_query("SELECT username FROM usuarios WHERE rol = ?", (role,))
            return [r['username'] for r in res]

    def authenticate(self, username: str, password_plain: str) -> dict:
        """Verifica las credenciales y devuelve el diccionario del usuario si es exitoso, None en caso contrario."""
        res = db_manager.execute_query(
            "SELECT id, username, password_hash, rol FROM usuarios WHERE username = ?", (username,)
        )
        if not res:
            return None

        db_user = res[0]
        hashed_input = hashlib.sha256(password_plain.encode()).hexdigest()
        
        if hashed_input != db_user['password_hash']:
            return None

        return dict(db_user)

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
        db_manager.execute_transaction([
            ("INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)", 
             ("admin", pwd_hash, "admin"))
        ])
