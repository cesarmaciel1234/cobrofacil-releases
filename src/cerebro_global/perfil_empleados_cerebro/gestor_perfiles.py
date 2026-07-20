import hashlib
from src.base_de_datos.database import db_manager

class GestorPerfiles:
    @staticmethod
    def obtener_usuarios_permitidos(rol_solicitante: str):
        """
        Devuelve la lista de usuarios según el rol de quien los solicita.
        - jefe: ve todos.
        - admin: ve solo cajeros y auxiliares.
        """
        res = db_manager.execute_query("SELECT id, username, rol, pin FROM usuarios ORDER BY id")
        if not res:
            return []
        
        usuarios = []
        for r in res:
            if isinstance(r, dict):
                u_id = r.get('id')
                u_name = r.get('username')
                u_rol = r.get('rol', '').lower()
                u_pin = r.get('pin')
            else:
                u_id, u_name, u_rol, u_pin = r[0], r[1], r[2].lower(), r[3]
                
            # Filtro jerárquico
            if rol_solicitante == 'admin' and u_rol in ('admin', 'jefe'):
                continue
                
            usuarios.append({
                'id': u_id,
                'username': u_name,
                'rol': u_rol,
                'pin': u_pin
            })
        return usuarios

    @staticmethod
    def eliminar_usuario(user_id: int):
        db_manager.execute_query("DELETE FROM usuarios WHERE id = ?", (user_id,))
        
    @staticmethod
    def crear_o_actualizar_usuario(user_id, username, password_plain, rol, pin_plain):
        # Encriptar contraseñas y pines
        if password_plain:
            password_hash = hashlib.sha256(password_plain.encode()).hexdigest()
        else:
            password_hash = None
            
        if pin_plain:
            if len(pin_plain) != 64:  # Si no está ya hasheado
                pin_hash = hashlib.sha256(pin_plain.encode()).hexdigest()
            else:
                pin_hash = pin_plain # Ya está hasheado
        else:
            pin_hash = None
            
        if user_id:
            # Actualizar
            if password_hash and pin_hash:
                db_manager.execute_query(
                    "UPDATE usuarios SET username = ?, password_hash = ?, rol = ?, pin = ? WHERE id = ?",
                    (username, password_hash, rol, pin_hash, user_id)
                )
            elif password_hash:
                db_manager.execute_query(
                    "UPDATE usuarios SET username = ?, password_hash = ?, rol = ? WHERE id = ?",
                    (username, password_hash, rol, user_id)
                )
            elif pin_hash:
                db_manager.execute_query(
                    "UPDATE usuarios SET username = ?, rol = ?, pin = ? WHERE id = ?",
                    (username, rol, pin_hash, user_id)
                )
            else:
                db_manager.execute_query(
                    "UPDATE usuarios SET username = ?, rol = ? WHERE id = ?",
                    (username, rol, user_id)
                )
        else:
            # Crear
            # Si no envían password, usar uno por defecto "1234"
            if not password_hash:
                password_hash = hashlib.sha256("1234".encode()).hexdigest()
                
            db_manager.execute_query(
                "INSERT INTO usuarios (username, password_hash, rol, pin) VALUES (?, ?, ?, ?)",
                (username, password_hash, rol, pin_hash)
            )
