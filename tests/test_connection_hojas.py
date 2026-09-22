import os

from src.base_de_datos.core.db_path import normalize_db_path
from src.base_de_datos.core.red_rol import leer_rol_red_desde_config


def test_rol_esclava_por_is_master_false():
    es_esclava, host = leer_rol_red_desde_config(
        {"is_master": False, "db_host": "192.168.0.10"}
    )
    assert es_esclava is True
    assert host == "192.168.0.10"


def test_rol_maestra_localhost():
    es_esclava, host = leer_rol_red_desde_config(
        {"is_master": True, "db_host": "127.0.0.1"}
    )
    assert es_esclava is False
    assert host == "127.0.0.1"


def test_rol_esclava_por_ip_remota_sin_flag():
    es_esclava, host = leer_rol_red_desde_config({"db_host": "10.0.0.5"})
    assert es_esclava is True
    assert host == "10.0.0.5"


def test_rol_preferred_master_ip():
    es_esclava, host = leer_rol_red_desde_config(
        {"is_master": False, "db_host": "localhost", "preferred_master_ip": "192.168.1.2"}
    )
    assert es_esclava is True
    assert host == "192.168.1.2"


def test_normalize_relativo_y_abs():
    base = r"C:\app"
    assert normalize_db_path("punpro.db", base) == os.path.normpath(
        os.path.join(base, "punpro.db")
    )
    assert normalize_db_path("", base) == ""
    abs_p = r"D:\datos\caja.db"
    assert normalize_db_path(abs_p, base) == os.path.normpath(abs_p)


def test_mixin_reexporta_mismas_firmas():
    from src.base_de_datos.core.connection import ConnectionMixin

    es, host = ConnectionMixin._leer_rol_red_desde_config({"db_host": "8.8.8.8"})
    assert es is True and host == "8.8.8.8"
