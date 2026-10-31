import logging

from src.central_red_global.servidor.ventana.vigia import linea_consola


def test_timeout_de_red_no_sale_como_error():
    linea = linea_consola(
        logging.ERROR,
        "Fallo al conectar a MariaDB en 192.168.0.7:3306 - timed out",
    )
    assert linea is not None
    nivel, texto = linea
    assert nivel < logging.ERROR
    assert "maestra sin respuesta" in texto


def test_traceback_no_entra():
    assert linea_consola(logging.ERROR, "Traceback (most recent call last):") is None


def test_aviso_ok_sigue_info():
    linea = linea_consola(logging.INFO, "carteleria  online")
    assert linea == (logging.INFO, "carteleria online")
