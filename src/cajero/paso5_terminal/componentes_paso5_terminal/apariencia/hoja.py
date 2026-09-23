"""Junta las hojas del cajero y las pega al final del tema."""

from pathlib import Path

_AQUI = Path(__file__).resolve().parent


def _leer(relativo):
    return (_AQUI / relativo).read_text(encoding="utf-8")


def hoja_cajero():
    """Azul o rosa, y después el marco del aviso. El aviso va último."""
    return "\n".join(
        (
            _leer("perfil/francia.qss"),
            _leer("perfil/rosa.qss"),
            _leer("aviso/marco.qss"),
        )
    )


def borde_barra():
    """Borde que la barra pinta sola, porque su estilo propio tapa al tema."""
    return _leer("aviso/barra.qss")


def anexar(css):
    """Deja el tema como está y agrega la apariencia del cajero al final."""
    return css + "\n" + hoja_cajero()
