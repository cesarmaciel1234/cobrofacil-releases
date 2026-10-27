"""El .sql se lee en UTF-8. Un rechazo de volcado no se cura como caída de red."""

from src.base_de_datos.autoblindaje.grabar.diario import Grabar
from src.services.auto_heal import _es_fallo_de_volcado, _heal_mariadb


def test_byte_9d_dentro_de_utf8_no_corta_el_volcado():
    # e2 80 9d es la comilla ”. cp1252 no tiene el byte 0x9d y cortaba el .sql ahí.
    crudo = "INSERT INTO productos VALUES (1,'Pan ”');\nDump completed\n".encode("utf-8")
    assert b"\x9d" in crudo
    assert Grabar._decodificar_utf8(crudo) == crudo.decode("utf-8")


def test_volcado_que_no_es_utf8_no_se_guarda():
    assert Grabar._decodificar_utf8(b"abc\x9d") is None


def test_rechazo_de_volcado_no_reconecta():
    assert _es_fallo_de_volcado("volcado rechazado: sin detalle")
    assert _heal_mariadb("volcado rechazado: sin detalle") is None


def test_restaurar_manda_el_sql_en_utf8(tmp_path, monkeypatch):
    sql = tmp_path / "backup.sql"
    sql.write_bytes("INSERT INTO t VALUES ('Pan ”');\n".encode("utf-8"))
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["stdin"] = kwargs["stdin"].read()
        captured["text"] = kwargs.get("text")

        class R:
            returncode = 0
            stderr = b""

        return R()

    monkeypatch.setattr(
        "src.base_de_datos.autoblindaje.sanar.integridad.subprocess.run", fake_run
    )
    monkeypatch.setattr(
        "src.base_de_datos.autoblindaje.sanar.integridad.os.path.isfile", lambda _p: True
    )
    from src.base_de_datos.autoblindaje.puerta import AutoBlindajeDB

    assert AutoBlindajeDB._aplicar_archivo_restore(str(sql), "mariadb", "127.0.0.1")
    assert "--default-character-set=utf8mb4" in captured["cmd"]
    assert captured["text"] is None
    assert "”" in captured["stdin"].decode("utf-8")


def test_caida_real_no_se_confunde_con_el_volcado():
    assert not _es_fallo_de_volcado(
        "can't connect to mysql server on '192.168.0.13' (2003, timed out)"
    )
