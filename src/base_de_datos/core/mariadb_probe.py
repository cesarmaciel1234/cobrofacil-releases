"""Comprobación rápida de puerto MariaDB (3306) sin abrir el engine."""
import socket


def puerto_mariadb_abierto(host: str, timeout: float = 2.0) -> bool:
    if not host:
        return False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((host, 3306)) == 0
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass
