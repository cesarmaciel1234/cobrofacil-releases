from src.central_red_global.sync_tienda.mp_token import tienda


class ConfigFalsa:
    def __init__(self, valores):
        self.valores = valores

    def _load_config(self):
        return None

    def get(self, clave, default=None):
        return self.valores.get(clave, default)

    def set(self, clave, valor):
        self.valores[clave] = valor


class DbTiendaFalsa:
    def __init__(self):
        self.configuracion = {}

    def execute_non_query(self, query, params=()):
        clave, valor = params
        self.configuracion[clave] = valor
        return True

    def execute_query(self, query, params=()):
        valor = self.configuracion.get(params[0])
        return [{"valor": valor}] if valor is not None else []


def test_maestra_publica_claves_y_esclava_las_cachea(monkeypatch):
    from src.config import config
    from src.central_red_global.sync_tienda import rol

    base = ConfigFalsa({
        "mp_access_token": "token-prueba",
        "mp_user_id": "usuario-prueba",
        "mp_device_id": "point-prueba",
        "mp_qr_pos_external_id": "qr-prueba",
    })
    tienda_db = DbTiendaFalsa()
    monkeypatch.setattr(config, "_load_config", base._load_config)
    monkeypatch.setattr(config, "get", base.get)
    monkeypatch.setattr(config, "set", base.set)
    monkeypatch.setattr(tienda, "_db", lambda: tienda_db)
    monkeypatch.setattr(rol, "es_esclava", lambda: False)

    assert tienda.publicar()
    assert tienda_db.configuracion == base.valores

    cache_esclava = ConfigFalsa({})
    monkeypatch.setattr(config, "_load_config", cache_esclava._load_config)
    monkeypatch.setattr(config, "get", cache_esclava.get)
    monkeypatch.setattr(config, "set", cache_esclava.set)
    monkeypatch.setattr(rol, "es_esclava", lambda: True)

    assert tienda.traer() == "token-prueba"
    assert cache_esclava.valores == base.valores

    from src.services.mp_escucha import EscuchaMP

    cache_esclava.valores.clear()
    assert EscuchaMP.token() == "token-prueba"
    assert cache_esclava.valores == base.valores
