import logging
import os
import re
import socket
import subprocess
import sys
import time

from src.config import config

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

# Evita spam de reintentos a una maestra caída (misma IP)
_SLAVE_FAIL_COOLDOWN_SEC = 45
_last_slave_fail_at: dict[str, float] = {}


class MotorRed:
    """Motor central para la gestión de la red LAN y modos (Maestra/Esclava)."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def obtener_estado_red(self):
        """Devuelve el estado actual de la red."""
        return {
            "is_master": getattr(db_manager, "is_master", True),
            "caja_id": config.get("caja_id", 1),
            "db_engine": getattr(db_manager, "db_engine_type", "sqlite"),
            "db_host": config.get("db_host", "") or "localhost",
            "descubrimiento_udp_puerto": 37020,
        }

    @staticmethod
    def _normalizar_ip(ip_maestra: str) -> str:
        if not ip_maestra:
            return ""
        match = re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ip_maestra)
        return match.group(0) if match else ip_maestra.strip()

    @staticmethod
    def _probe_mariadb(host: str, port: int = 3306, timeout: float = 1.5) -> bool:
        """True si el puerto MariaDB acepta TCP (sin tocar el motor de BD activo)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            ok = sock.connect_ex((host, port)) == 0
            sock.close()
            return ok
        except Exception:
            return False

    @staticmethod
    def _detener_servidor_tienda_local():
        """Apaga el proceso --server local al pasar a esclava (best-effort)."""
        try:
            from src.utils.candados import get_store_server_pid, release_store_server_lock
            pid = get_store_server_pid()
            if pid and pid != os.getpid():
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/PID", str(pid), "/T", "/F"],
                        capture_output=True,
                        check=False,
                    )
                else:
                    os.kill(pid, 15)
            release_store_server_lock()
        except Exception as e:
            logging.getLogger(__name__).debug(f"No se pudo detener Servidor de Tienda: {e}")

    def convertir_en_maestra(self):
        """Convierte la PC en maestra (base de datos local MariaDB)."""
        try:
            config.set("is_master", True)
            config.set("db_engine", "mariadb")
            config.set("db_host", "localhost")
            config.set("auto_start_store_server", True)
            try:
                config.set("carteleria_is_slave", False)
                config.data["preferred_master_ip"] = ""
                config.save()
            except Exception:
                pass
            db_manager.reconectar_mariadb("localhost")
            return True, "Configurado exitosamente como MAESTRA (Servidor MariaDB Local)."
        except Exception as e:
            self.logger.error(f"Error convirtiendo a maestra: {e}")
            return False, f"Error: {e}"

    def convertir_en_esclava(self, ip_maestra):
        """Convierte la PC en esclava conectándose a la IP maestra.

        Importante: prueba TCP *antes* de cambiar el motor activo, para no
        tumbar SQLite local ni spamear timeouts si la maestra está apagada.
        """
        ip_maestra = self._normalizar_ip(ip_maestra)

        if not ip_maestra or ip_maestra.lower() in ("localhost", "127.0.0.1"):
            return False, "Debes ingresar una IP válida de red (ej: 192.168.0.100)."

        now = time.time()
        last_fail = _last_slave_fail_at.get(ip_maestra, 0)
        remaining = _SLAVE_FAIL_COOLDOWN_SEC - (now - last_fail)
        if remaining > 0:
            return (
                False,
                f"La Maestra en {ip_maestra} no respondió hace poco. "
                f"Reintentá en {int(remaining)}s o verificá que esté encendida.",
            )

        if not self._probe_mariadb(ip_maestra):
            _last_slave_fail_at[ip_maestra] = now
            # Recordamos la IP deseada sin cambiar el motor en vivo
            config.data["preferred_master_ip"] = ip_maestra
            try:
                config.save()
            except Exception:
                pass
            return (
                False,
                f"No hay MariaDB en {ip_maestra}:3306.\n\n"
                "La PC Maestra parece apagada o fuera de la red.\n"
                "Seguís en modo local (SQLite) sin cambios.",
            )

        # Snapshot para revertir solo si el switch real falla
        prev_master = getattr(db_manager, "is_master", True)
        prev_engine = getattr(db_manager, "db_engine_type", "sqlite")
        prev_host = config.get("db_host", "") or "localhost"
        prev_cfg_engine = config.get("db_engine", "sqlite")
        prev_cfg_master = config.get("is_master", True)

        try:
            config.set("is_master", False)
            config.set("db_engine", "mariadb")
            config.set("db_host", ip_maestra)
            config.data["preferred_master_ip"] = ip_maestra

            db_manager.reconectar_mariadb(ip_maestra)

            if db_manager.is_connected():
                _last_slave_fail_at.pop(ip_maestra, None)
                # Persistir rol esclavo: sin esto, al reiniciar el Servidor local
                # volvía a adjuntarse como maestra.
                try:
                    config.set("carteleria_master_ip", ip_maestra)
                    config.set("carteleria_is_slave", True)
                    config.set("auto_start_store_server", False)
                    config.data["preferred_master_ip"] = ip_maestra
                    config.data["is_master"] = False
                    config.data["db_host"] = ip_maestra
                    config.save()
                except Exception:
                    pass
                self._detener_servidor_tienda_local()
                return True, f"Conexión exitosa a la Maestra en {ip_maestra}."

            # Puerto abierto pero auth/DB falló: volver al estado anterior
            _last_slave_fail_at[ip_maestra] = time.time()
            config.set("is_master", prev_cfg_master)
            config.set("db_engine", prev_cfg_engine)
            config.set("db_host", prev_host)
            if prev_engine == "mariadb" and prev_host not in ("", "localhost", "127.0.0.1"):
                db_manager.reconectar_mariadb(prev_host)
            else:
                db_manager.reconectar_local()
            return (
                False,
                "El puerto 3306 responde pero no se pudo usar la base.\n"
                "Verificá usuario/clave MariaDB en la Maestra. Se mantuvo el modo anterior.",
            )
        except Exception as e:
            _last_slave_fail_at[ip_maestra] = time.time()
            self.logger.error(f"Error convirtiendo a esclava: {e}")
            try:
                config.set("is_master", prev_cfg_master)
                config.set("db_engine", prev_cfg_engine)
                config.set("db_host", prev_host)
                if prev_master and prev_engine != "mariadb":
                    db_manager.reconectar_local()
            except Exception:
                pass
            return False, f"Error inesperado: {e}"
