"""El empleado: un solo hilo por PC que baja MP, sube firmas de caja, enlaza lo seguro y deja el veredicto listo."""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime

from src.logger import logger
from src.utils.paths import get_base_path

CADA = 300
DESPUES_DE_COBRO = 90

_arrancado = False
_candado_pc = None
_despertar = threading.Event()
_estado = {"ultimo_turno": "", "bajados": 0, "firmas_caja": False, "enlazados": 0, "error": ""}


def _fallo(etapa: str, error) -> None:
    mensaje = f"{etapa}: {error}"
    _estado["error"] = "; ".join(filter(None, (_estado["error"], mensaje)))
    logger.warning(f"[Cobros digitales] {mensaje}")


def estado() -> dict:
    """Cómo terminó el último turno. Solo memoria: no toca red ni base."""
    return dict(_estado)


def turno() -> dict:
    """Una vuelta completa, en este orden: bajar de MP, subir firmas de caja, enlazar automático."""
    from src.motor_cobros_digitales.bajada.mp import ponerse_al_dia
    from src.motor_cobros_digitales.enlace.automatico import enlazar
    from src.motor_cobros_digitales.enlace.caja import subir_vinculos

    _estado.update({"bajados": 0, "firmas_caja": False, "enlazados": 0, "error": ""})
    token = ""
    try:
        from src.services.mp_escucha import EscuchaMP

        token = EscuchaMP.token()
    except Exception as error:
        _fallo("token MP", error)

    if token:
        try:
            _estado["bajados"] = ponerse_al_dia(token)
            if _estado["bajados"] < 0:
                _fallo("bajada MP", "no se pudo completar; se reintentará")
        except Exception as error:
            _estado["bajados"] = -1
            _fallo("bajada MP", error)
    elif not _estado["error"]:
        _fallo("token MP", "sin token; se omite la bajada y el enlace automático")

    try:
        _estado["firmas_caja"] = subir_vinculos()
        if not _estado["firmas_caja"]:
            _fallo("firmas de caja", "no se pudieron subir; se reintentará")
    except Exception as error:
        _fallo("firmas de caja", error)

    if token and _estado["bajados"] >= 0 and _estado["firmas_caja"]:
        try:
            _estado["enlazados"] = enlazar()
            if _estado["enlazados"] < 0:
                _fallo("enlace automático", "no se pudo completar; se reintentará")
        except Exception as error:
            _fallo("enlace automático", error)
    _estado["ultimo_turno"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if _estado["bajados"] or _estado["enlazados"]:
        logger.info(
            f"[Cobros digitales] bajados={_estado['bajados']} enlazados={_estado['enlazados']}"
        )
    return estado()


def anotar_llegada(pago):
    """Lo llama la escucha MP al detectar un pago. Lo guarda en otro hilo y pide un turno en 90 s."""
    def _tarea():
        try:
            from src.motor_cobros_digitales.libro.tabla import guardar

            guardar([pago])
        except Exception:
            pass
        time.sleep(DESPUES_DE_COBRO)
        _despertar.set()

    threading.Thread(target=_tarea, daemon=True).start()


def despertar():
    _despertar.set()


def _una_por_pc() -> bool:
    """Varias ventanas del TPV en la misma PC: solo una trabaja."""
    global _candado_pc
    if os.name != "nt":
        return True
    try:
        import msvcrt

        ruta_lock = os.path.join(get_base_path(), "locks", "cobros_digitales.lock")
        os.makedirs(os.path.dirname(ruta_lock), exist_ok=True)
        archivo = open(ruta_lock, "a+")
        msvcrt.locking(archivo.fileno(), msvcrt.LK_NBLCK, 1)
        _candado_pc = archivo
        return True
    except Exception:
        return False


def _jornada():
    time.sleep(20)
    if not _una_por_pc():
        return
    while True:
        turno()
        _despertar.wait(CADA)
        _despertar.clear()


def arrancar():
    """Al iniciar el TPV. No bloquea: todo corre en su hilo."""
    global _arrancado
    if _arrancado:
        return
    _arrancado = True
    threading.Thread(target=_jornada, daemon=True, name="cobros_digitales").start()
