"""
session_service.py - Servicio simple para manejar el usuario activo y sus permisos.
Nivel Medio: Encapsula la sesión actual para que la UI no acceda a variables crudas de configuración.
"""

from src.config import config

class SessionService:
    @staticmethod
    def obtener_rol_usuario() -> str:
        """Devuelve 'admin', 'jefe' o 'cajero' de forma segura sin colapsar."""
        try:
            return config.current_role
        except Exception:
            return "cajero"

    @staticmethod
    def es_cajero() -> bool:
        """Devuelve True si el usuario actual es un cajero (solo lectura)."""
        return SessionService.obtener_rol_usuario() == "cajero"

    @staticmethod
    def es_admin_o_jefe() -> bool:
        """Devuelve True si el usuario tiene privilegios de administrador o jefe."""
        return SessionService.obtener_rol_usuario() in ("admin", "jefe")
