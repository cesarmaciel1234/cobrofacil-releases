"""Junta las hojas del cajero y las pega al final del tema."""

from pathlib import Path

from src.utils.paths import get_resource_path

_AQUI = Path(__file__).resolve().parent
_EN_PAQUETE = Path("src") / "cajero" / "paso5_terminal" / "componentes_paso5_terminal" / "apariencia"


def _leer(relativo):
    """Lee el qss al lado del código o dentro del ejecutable. Si no está, no tumba la venta."""
    candidatos = (
        _AQUI / relativo,
        Path(get_resource_path(str(_EN_PAQUETE / relativo))),
    )
    for ruta in candidatos:
        if ruta.is_file():
            return ruta.read_text(encoding="utf-8")
    return ""


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
