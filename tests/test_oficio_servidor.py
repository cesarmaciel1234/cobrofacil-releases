"""El servidor esclava no abre MariaDB. El de maestra sí la vigila."""

import threading


def test_la_esclava_no_vigila_mariadb(monkeypatch):
    from src.central_red_global.servidor.oficio import agente

    monkeypatch.setattr(
        "src.central_red_global.master_presence.es_pc_maestra_local",
        lambda: False,
    )
    assert agente.oficio() == "esclava"
    assert agente.vigila_mariadb() is False


def test_la_maestra_vigila_mariadb(monkeypatch):
    from src.central_red_global.servidor.oficio import agente

    monkeypatch.setattr(
        "src.central_red_global.master_presence.es_pc_maestra_local",
        lambda: True,
    )
    assert agente.oficio() == "maestra"
    assert agente.vigila_mariadb() is True


def test_una_vuelta_caida_no_sale(monkeypatch):
    from src.central_red_global.servidor.oficio import agente

    def _caer():
        raise RuntimeError("sin red")

    monkeypatch.setattr("src.jefe.nodo_portable.espejo.copia.refrescar", _caer)
    agente._paso_espejo()


def test_la_carteleria_caida_no_sale(monkeypatch):
    from src.central_red_global.servidor.oficio import agente

    def _caer():
        raise RuntimeError("tele sin red")

    monkeypatch.setattr("src.carteleria.vitrina.pulso.pulso_vitrina", _caer)
    agente._paso_carteleria()


def test_el_hilo_esclava_es_uno_solo(monkeypatch):
    import time

    from src.central_red_global.servidor.oficio import agente

    vivo = threading.Event()
    tele = threading.Event()

    def _vuelta():
        vivo.set()
        time.sleep(30)

    def _tele():
        tele.set()
        time.sleep(30)

    monkeypatch.setattr(agente, "_vuelta_espejo", _vuelta)
    monkeypatch.setattr(agente, "_vuelta_carteleria", _tele)
    agente._hilo = None
    agente._hilo_carteleria = None
    agente.cumplir_esclava()
    assert vivo.wait(2)
    assert tele.wait(2)
    hilo = agente._hilo
    hilo_tele = agente._hilo_carteleria
    agente.cumplir_esclava()
    assert agente._hilo is hilo
    assert agente._hilo_carteleria is hilo_tele
    assert hilo.is_alive()
    assert hilo_tele.is_alive()


def test_el_candado_deja_pasar_una_sola_escritura(tmp_path, monkeypatch):
    from src.jefe.nodo_portable.espejo import copia

    monkeypatch.setattr(copia, "carpeta", lambda: str(tmp_path))
    primero = copia._candado_proceso()
    assert primero is not None
    try:
        segundo = copia._candado_proceso()
        assert segundo is None
    finally:
        copia._soltar_candado(primero)
    de_nuevo = copia._candado_proceso()
    assert de_nuevo is not None
    copia._soltar_candado(de_nuevo)
