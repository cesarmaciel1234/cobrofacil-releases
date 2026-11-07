from src.central_red_global.servidor.pareja import buscar


def test_descubrimiento_rechaza_otra_identidad_de_tienda(monkeypatch):
    monkeypatch.setattr(buscar, "_guardada", lambda: "192.168.1.20")
    monkeypatch.setattr(buscar, "_store_id_guardado", lambda: "tienda-a")
    monkeypatch.setattr(buscar, "tiene_la_tienda", lambda _host: True)

    elegida = buscar._elegir_aviso(
        [
            {
                "server_ip": "192.168.1.30",
                "store_id": "tienda-b",
                "mode": "MAESTRA",
            },
            {
                "server_ip": "192.168.1.40",
                "store_id": "tienda-a",
                "mode": "MAESTRA",
            },
        ]
    )

    assert elegida["server_ip"] == "192.168.1.40"


def test_descubrimiento_rechaza_maestra_sin_identidad(monkeypatch):
    monkeypatch.setattr(buscar, "_guardada", lambda: "192.168.1.20")
    monkeypatch.setattr(buscar, "_store_id_guardado", lambda: "tienda-a")
    monkeypatch.setattr(buscar, "tiene_la_tienda", lambda _host: True)

    assert buscar._elegir_aviso(
        [
            {
                "server_ip": "192.168.1.30",
                "mode": "MAESTRA",
            },
        ]
    ) == {}


def test_sin_identidad_no_salta_de_ip_a_otro_servidor(monkeypatch):
    monkeypatch.setattr(buscar, "_guardada", lambda: "192.168.1.20")
    monkeypatch.setattr(buscar, "_store_id_guardado", lambda: "")
    monkeypatch.setattr(buscar, "tiene_la_tienda", lambda _host: True)

    assert buscar._elegir_aviso(
        [
            {
                "server_ip": "192.168.1.30",
                "store_id": "tienda-a",
                "mode": "MAESTRA",
            },
        ]
    ) == {}


def test_descubrimiento_prefiere_ip_enlazada_si_sigue_anunciada(monkeypatch):
    monkeypatch.setattr(buscar, "_guardada", lambda: "192.168.1.20")
    monkeypatch.setattr(buscar, "_store_id_guardado", lambda: "tienda-a")
    monkeypatch.setattr(buscar, "tiene_la_tienda", lambda _host: True)
    guardada = {
        "server_ip": "192.168.1.20",
        "store_id": "tienda-a",
        "mode": "MAESTRA",
    }

    assert buscar._elegir_aviso(
        [
            {
                "server_ip": "192.168.1.30",
                "store_id": "tienda-a",
                "mode": "MAESTRA",
            },
            guardada,
        ]
    ) == guardada


def test_buscar_no_acepta_ip_guardada_sin_anuncio_de_identidad(monkeypatch):
    from src.central_red_global import master_presence

    monkeypatch.setattr(master_presence, "es_pc_maestra_local", lambda: False)
    monkeypatch.setattr(buscar, "_guardada", lambda: "192.168.1.20")
    monkeypatch.setattr(buscar, "_store_id_guardado", lambda: "tienda-a")
    monkeypatch.setattr(buscar, "oir_anuncios", lambda: [])
    monkeypatch.setattr(buscar, "tiene_la_tienda", lambda _host: True)

    assert buscar.buscar() == ""


def test_buscar_rechaza_ip_guardada_con_identidad_distinta(monkeypatch):
    from src.central_red_global import master_presence

    monkeypatch.setattr(master_presence, "es_pc_maestra_local", lambda: False)
    monkeypatch.setattr(buscar, "_guardada", lambda: "192.168.1.20")
    monkeypatch.setattr(buscar, "_store_id_guardado", lambda: "tienda-a")
    monkeypatch.setattr(
        buscar,
        "oir_anuncios",
        lambda: [{"server_ip": "192.168.1.20", "store_id": "tienda-b"}],
    )
    monkeypatch.setattr(buscar, "tiene_la_tienda", lambda _host: True)

    assert buscar.buscar() == ""


def test_buscar_confirma_identidad_del_host_guardado(monkeypatch):
    from src.central_red_global import master_presence

    llamadas = []
    monkeypatch.setattr(master_presence, "es_pc_maestra_local", lambda: False)
    monkeypatch.setattr(buscar, "_guardada", lambda: "192.168.1.20")
    monkeypatch.setattr(buscar, "_store_id_guardado", lambda: "tienda-a")
    monkeypatch.setattr(
        buscar,
        "oir_anuncios",
        lambda: llamadas.append("udp") or [{
            "server_ip": "192.168.1.20",
            "store_id": "tienda-a",
            "mode": "MAESTRA",
        }],
    )
    monkeypatch.setattr(buscar, "tiene_la_tienda", lambda _host: True)

    assert buscar.buscar() == "192.168.1.20"
    assert llamadas == ["udp"]


def test_identidad_para_ip_acepta_la_tienda_enlazada(monkeypatch):
    monkeypatch.setattr(buscar, "oir_anuncios", lambda: [{
        "server_ip": "192.168.1.30",
        "store_id": "tienda-a",
        "mode": "MAESTRA",
    }])
    monkeypatch.setattr(buscar, "_store_id_guardado", lambda: "tienda-a")
    monkeypatch.setattr(buscar, "_guardada", lambda: "192.168.1.20")
    monkeypatch.setattr(buscar, "tiene_la_tienda", lambda _host: True)

    assert buscar.identidad_para_ip("192.168.1.30") == "tienda-a"


def test_identidad_para_ip_rechaza_otro_negocio(monkeypatch):
    monkeypatch.setattr(buscar, "oir_anuncios", lambda: [{
        "server_ip": "192.168.1.30",
        "store_id": "tienda-b",
        "mode": "MAESTRA",
    }])
    monkeypatch.setattr(buscar, "_store_id_guardado", lambda: "tienda-a")
    monkeypatch.setattr(buscar, "_guardada", lambda: "192.168.1.20")
    monkeypatch.setattr(buscar, "tiene_la_tienda", lambda _host: True)

    assert buscar.identidad_para_ip("192.168.1.30") == ""


def test_reconectar_en_fondo_actualiza_engine_a_ip_adoptada(monkeypatch):
    from src.base_de_datos.repos.red import RedRepoMixin

    class Engine:
        host = "192.168.1.20"

    class Repo(RedRepoMixin):
        db_engine_type = "mariadb"
        mariadb_engine = Engine()
        is_master = False

        def _host_tienda(self):
            return "192.168.1.30"

        def _buscar_maestra_en_fondo(self, host):
            self.descubierta = host

    repo = Repo()
    assert repo.asegurar_lectura_tienda() is False
    assert repo.descubierta == "192.168.1.30"


def test_busqueda_en_fondo_reconecta_a_la_ip_descubierta(monkeypatch):
    import threading

    from src.base_de_datos.repos import red

    encontrada = threading.Event()

    class Repo(red.RedRepoMixin):
        def _host_tienda(self):
            return "192.168.1.20"

        def reconectar_mariadb(self, host):
            self.host_enlazado = host
            encontrada.set()

    monkeypatch.setattr(
        "src.central_red_global.servidor.pareja.buscar.buscar",
        lambda: "192.168.1.30",
    )
    repo = Repo()
    repo._buscar_maestra_en_fondo("192.168.1.20")

    assert encontrada.wait(2)
    assert repo.host_enlazado == "192.168.1.30"


def test_reserva_no_se_promueve_sin_identidad_de_tienda(monkeypatch):
    from src.central_red_global.servidor.pareja import promover
    from src.config import config
    from src.jefe.nodo_portable.espejo import copia

    monkeypatch.setattr(copia, "existe", lambda: True)
    monkeypatch.setattr(config, "get", lambda key, default=None: "" if key == "store_id" else default)

    assert promover._promover() is False
