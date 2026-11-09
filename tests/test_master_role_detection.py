from src.central_red_global import master_presence
from src.central_red_global.servidor.rol import maestra
from src.base_de_datos.core import red_rol


def test_ip_de_esta_pc_no_se_considera_maestra_remota(monkeypatch):
    from src.config import config

    values = {
        "db_host": "192.168.0.50",
        "is_master": True,
        "carteleria_is_slave": False,
        "preferred_master_ip": "",
    }
    monkeypatch.setattr(config, "get", lambda key, default=None: values.get(key, default))
    monkeypatch.setattr(
        "src.central_red_global.servidor.rol.ip.es_ip_de_esta_pc",
        lambda _host: True,
    )

    assert master_presence.es_pc_maestra_local() is True


def test_ip_de_otra_pc_sigue_siendo_esclava(monkeypatch):
    from src.config import config

    values = {
        "db_host": "192.168.0.77",
        "is_master": True,
        "carteleria_is_slave": False,
        "preferred_master_ip": "",
    }
    monkeypatch.setattr(config, "get", lambda key, default=None: values.get(key, default))
    monkeypatch.setattr(
        "src.central_red_global.servidor.rol.ip.es_ip_de_esta_pc",
        lambda _host: False,
    )

    assert master_presence.es_pc_maestra_local() is False


def test_reparacion_de_rol_solo_si_host_es_esta_pc_y_mariadb_local_responde(monkeypatch):
    from src.config import config

    monkeypatch.setattr(
        config,
        "get",
        lambda key, default=None: "192.168.0.50" if key == "db_host" else default,
    )
    monkeypatch.setattr(maestra, "es_ip_de_esta_pc", lambda _host: True)
    monkeypatch.setattr(maestra, "probe_mariadb", lambda host: host == "127.0.0.1")

    assert maestra.puede_corregir_rol_a_maestra_local() is True

    monkeypatch.setattr(maestra, "es_ip_de_esta_pc", lambda _host: False)
    assert maestra.puede_corregir_rol_a_maestra_local() is False


def test_config_con_ip_propia_no_se_interpreta_como_esclava(monkeypatch):
    monkeypatch.setattr(red_rol, "es_ip_de_esta_pc", lambda _host: True)

    es_esclava, host = red_rol.leer_rol_red_desde_config(
        {
            "db_host": "192.168.0.50",
            "preferred_master_ip": "192.168.0.50",
            "carteleria_master_ip": "",
            "is_master": True,
            "carteleria_is_slave": False,
        }
    )

    assert es_esclava is False
    assert host == "192.168.0.50"


def test_config_con_ip_remota_sigue_como_esclava(monkeypatch):
    monkeypatch.setattr(red_rol, "es_ip_de_esta_pc", lambda _host: False)

    es_esclava, host = red_rol.leer_rol_red_desde_config(
        {
            "db_host": "192.168.0.77",
            "is_master": True,
            "carteleria_is_slave": False,
        }
    )

    assert es_esclava is True
    assert host == "192.168.0.77"
