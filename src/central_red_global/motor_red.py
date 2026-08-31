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

    def _intentar_arrancar_mariadb_local(self) -> bool:
        """Best-effort: levanta mysqld portable y espera el puerto 3306."""
        try:
            from src.services.mariadb_controller import mariadb_controller

            mariadb_controller.start_server()
        except Exception as e:
            self.logger.warning(f"No se pudo arrancar MariaDB local: {e}")
        # Poll corto: start_server ya espera, pero re-chequeamos
        for _ in range(10):
            if self._probe_mariadb("127.0.0.1", timeout=1.0):
                return True
            time.sleep(0.5)
        return self._probe_mariadb("127.0.0.1", timeout=1.0)

    def convertir_en_maestra(self):
        """Convierte la PC en maestra (MariaDB local). No pisa el rol si localhost no responde."""
        # En perfil cartelería no arrancar mysqld (congela la TV). Si ya hay
        # MariaDB local, sí se puede promover esclava → maestra.
        era_esclava = False
        try:
            era_esclava = bool(config.get("carteleria_is_slave")) or (
                config.get("is_master") is False
            )
        except Exception:
            era_esclava = False
        no_arrancar_mysqld = era_esclava and (
            "--role" in sys.argv and "carteleria" in sys.argv
        )

        # Snapshot para revertir si falla (p.ej. cartelería/esclava sin mysqld)
        prev_master = getattr(db_manager, "is_master", True)
        prev_engine = getattr(db_manager, "db_engine_type", "sqlite")
        prev_host = (config.get("db_host") or "").strip() or "localhost"
        prev_cfg_engine = config.get("db_engine", "sqlite")
        prev_cfg_master = config.get("is_master", True)
        prev_slave = bool(config.get("carteleria_is_slave"))
        prev_preferred = str(config.get("preferred_master_ip") or config.data.get("preferred_master_ip") or "").strip()
        prev_carteleria_ip = str(config.get("carteleria_master_ip") or "").strip()
        prev_auto_store = config.get("auto_start_store_server", True)

        def _rollback(msg_extra: str = ""):
            try:
                config.set("is_master", prev_cfg_master)
                config.set("db_engine", prev_cfg_engine)
                config.set("db_host", prev_host)
                config.set("carteleria_is_slave", prev_slave)
                config.set("auto_start_store_server", prev_auto_store)
                if prev_preferred:
                    config.data["preferred_master_ip"] = prev_preferred
                if prev_carteleria_ip:
                    config.set("carteleria_master_ip", prev_carteleria_ip)
                config.save()
            except Exception:
                pass
            try:
                if prev_engine == "mariadb" and prev_host not in ("", "localhost", "127.0.0.1"):
                    db_manager.reconectar_mariadb(prev_host)
                elif prev_engine == "mariadb" and self._probe_mariadb("127.0.0.1"):
                    db_manager.reconectar_mariadb("localhost")
                else:
                    db_manager.reconectar_local()
            except Exception as e:
                self.logger.error(f"Rollback tras fallar maestra: {e}")
            return False, msg_extra

        try:
            # 1) Puerto local antes de tocar config
            if not self._probe_mariadb("127.0.0.1"):
                if no_arrancar_mysqld:
                    return (
                        False,
                        "Esta cartelería no tiene MariaDB local.\n\n"
                        "Para ser MAESTRA usá la PC servidor (caja/admin) "
                        "con Servidor de Tienda corriendo.\n"
                        "En la TV seguí como ESCLAVA y reconectá a esa IP.",
                    )
                self.logger.info("MariaDB local no responde; intentando arrancar mysqld portable...")
                if not self._intentar_arrancar_mariadb_local():
                    hint_slave = ""
                    remote = prev_preferred or prev_carteleria_ip or (
                        prev_host if prev_host not in ("", "localhost", "127.0.0.1") else ""
                    )
                    if remote:
                        hint_slave = (
                            f"\n\nEsta PC seguía como esclava de {remote}. "
                            "Volvé a 'Convertir en ESCLAVA' con esa IP si hace falta."
                        )
                    return (
                        False,
                        "No hay MariaDB en esta PC (localhost:3306).\n\n"
                        "Para ser MAESTRA necesitás el Servidor de Tienda / MariaDB "
                        "instalado y corriendo aquí.\n"
                        "En una cartelería o caja esclava no uses 'Convertir en MAESTRA'."
                        + hint_slave,
                    )

            # 2) Recién ahora persistir rol maestra
            config.set("is_master", True)
            config.set("db_engine", "mariadb")
            config.set("db_host", "localhost")
            config.set("auto_start_store_server", True)
            try:
                config.set("carteleria_is_slave", False)
                config.set("carteleria_master_ip", "")
                config.data["preferred_master_ip"] = ""
                config.save()
            except Exception:
                pass

            db_manager.reconectar_mariadb("localhost")
            if not db_manager.is_connected():
                return _rollback(
                    "MariaDB local abrió el puerto pero no responde consultas.\n"
                    "Se mantuvo el modo anterior."
                )

            return True, "Configurado exitosamente como MAESTRA (Servidor MariaDB Local)."
        except Exception as e:
            self.logger.error(f"Error convirtiendo a maestra: {e}")
            return _rollback(
                f"No se pudo activar MAESTRA local:\n{e}\n\nSe restauró el modo anterior."
            )

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
