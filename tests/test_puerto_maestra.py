"""Un parpadeo del puerto no baja a la caja de la maestra."""

from src.base_de_datos.core.connection import ConnectionMixin
from src.base_de_datos.core.mariadb_probe import es_freno_local


def _caja():
    caja = object.__new__(ConnectionMixin)
    caja._fallos_puerto = 0
    caja._maestra_viva_hasta = 0
    caja._maestra_muerta_hasta = 0
    return caja


def test_un_parpadeo_no_declara_el_puerto_cerrado(monkeypatch):
    import src.base_de_datos.core.connection as conexion

    monkeypatch.setattr(conexion, "puerto_mariadb_abierto", lambda host, timeout=0.8: False)
    caja = _caja()
    assert caja._puerto_maestra_vivo("192.168.0.7") is True
    assert caja._fallos_puerto == 1


def test_el_segundo_parpadeo_si_corta(monkeypatch):
    import src.base_de_datos.core.connection as conexion

    monkeypatch.setattr(conexion, "puerto_mariadb_abierto", lambda host, timeout=0.8: False)
    caja = _caja()
    caja._puerto_maestra_vivo("192.168.0.7")
    caja._maestra_viva_hasta = 0
    assert caja._puerto_maestra_vivo("192.168.0.7") is False


def test_el_primer_corte_de_consulta_no_cambia_de_base():
    caja = _caja()
    assert caja._corte_confirmado() is False
    assert caja._corte_confirmado() is True


def test_el_freno_local_no_es_la_maestra_apagada():
    assert es_freno_local("Circuit breaker: MariaDB is currently unreachable (cooldown)")
    assert not es_freno_local("(2003, \"Can't connect to MySQL server on '192.168.0.7' (timed out)\")")
