"""El kiosk no se mata si Chrome ya está vivo."""

from src.carteleria.lanzador_tv.directo.motores.pulso import MotoresMixin


class _Cuello:
    def __init__(self, vivo):
        self._vivo = vivo
        self.abrio = 0
        self.forzo = 0

    def url_tv(self):
        return "http://127.0.0.1:8765/"

    def navegador_vivo(self):
        return self._vivo

    def asegurar_navegador(self):
        self.abrio += 1

    def _lanzar_navegador(self, forzar=False):
        self.forzo += 1


class _Lanzador(MotoresMixin):
    def __init__(self, vivo):
        self._vivo = True
        self._cuello = _Cuello(vivo)


def test_watchdog_no_reabre_si_el_kiosk_vive():
    tv = _Lanzador(vivo=True)
    tv._vigilar_navegador()
    assert tv._cuello.abrio == 0
    assert tv._cuello.forzo == 0


def test_watchdog_abre_una_si_el_kiosk_no_esta():
    tv = _Lanzador(vivo=False)
    tv._vigilar_navegador()
    assert tv._cuello.abrio == 1
    assert tv._cuello.forzo == 0
