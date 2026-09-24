"""Comprobación rápida de puerto MariaDB (3306) sin abrir el engine."""
import socket

# Textos de pymysql y del circuit breaker. "access denied" no entra: clave mala no es maestra apagada.
MARCAS_MAESTRA_CAIDA = (
    "lost connection",
    "can't connect",
    "cannot connect",
    "gone away",
    "timed out",
    "timeout",
    "circuit breaker",
    "unreachable",
    "cooldown",
    "2003",
    "2006",
    "2013",
    "10060",
    "10061",
)


def error_indica_maestra_caida(err) -> bool:
    """True si el fallo es red/servidor caído, no un error de SQL o de clave."""
    texto = str(err).lower()
    return any(marca in texto for marca in MARCAS_MAESTRA_CAIDA)


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
