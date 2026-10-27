"""Oficio del proceso --server. La pantalla no elige la base."""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger("oficio_servidor")

PAUSA_PRIMERA_SEG = 20
PAUSA_VUELTA_SEG = 60
_hilo: threading.Thread | None = None
_hilo_carteleria: threading.Thread | None = None
_hilo_cola: threading.Thread | None = None
_guardia = threading.Lock()
_aviso = threading.Event()
_generacion = 0
_ultimo_reparto = 0.0


def oficio() -> str:
    """maestra: esta PC es la tienda. esclava: esta PC guarda el espejo."""
    from src.central_red_global.master_presence import es_pc_maestra_local

    return "maestra" if es_pc_maestra_local() else "esclava"


def vigila_mariadb() -> bool:
    """Solo la maestra levanta MariaDB. La esclava no abre una segunda tienda."""
    return oficio() == "maestra"


def agente_tiene_el_espejo() -> bool:
    """True si el proceso --server de una esclava ya está refrescando la copia."""
    if oficio() != "esclava":
        return False
    try:
        from src.utils.candados import is_store_server_running

        return bool(is_store_server_running())
    except Exception:
        return False


def _despertar() -> None:
    global _generacion
    with _guardia:
        _generacion += 1
    _aviso.set()


def pedir_reparto() -> None:
    """La maestra avisó. El espejo y la tele se actualizan ya, sin esperar el minuto."""
    global _ultimo_reparto
    ahora = time.time()
    if ahora - _ultimo_reparto < 3:
        return
    _ultimo_reparto = ahora
    _despertar()
    logger.info("reparto  llego de la maestra, actualizo espejo y tele")


def pedir_bajada() -> None:
    """La cola ya está en la maestra. El espejo baja esa vuelta sin esperar el minuto."""
    _despertar()


_nodo_en_linea: bool | None = None


def _bajar_lo_que_falta() -> None:
    """Una vuelta del espejo. Si falla, la copia queda y esta función no levanta error."""
    try:
        from src.jefe.nodo_portable.espejo.copia import refrescar

        res = refrescar()
        estado = res.get("estado") if isinstance(res, dict) else "ok"
        logger.info("espejo  %s", estado or "ok")
        if estado == "ok":
            from src.central_red_global.servidor.pareja.acuse import soltar_propios

            soltar_propios()
    except Exception as e:
        logger.warning("Vuelta del espejo caída. La copia queda: %s", e)


def _paso_nodo() -> None:
    """Sube la cola. Si la maestra contestó, el espejo baja lo que le falta."""
    global _nodo_en_linea
    try:
        from src.base_de_datos.offline_sync import offline_sync_manager
    except Exception as e:
        logger.warning("cola  no se pudo subir: %s", e)
        return
    espera = 0
    subida: dict = {"ok": False, "ocupado": True}
    while espera <= 30:
        try:
            subida = offline_sync_manager.subir_colas()
        except Exception as e:
            logger.warning("cola  no se pudo subir: %s", e)
            return
        if not subida.get("ocupado"):
            break
        time.sleep(2)
        espera += 2
    if not subida.get("ok"):
        if not subida.get("ocupado") and _nodo_en_linea is not False:
            logger.info("nodo  maestra sin respuesta, la cola y el espejo quedan")
            _nodo_en_linea = False
        return
    if _nodo_en_linea is not True:
        logger.info("nodo  maestra en linea, cola subida, bajo el espejo")
        _nodo_en_linea = True
    _bajar_lo_que_falta()


def _esperar_turno(visto: int) -> int:
    if _generacion != visto:
        return _generacion
    _aviso.wait(PAUSA_VUELTA_SEG)
    _aviso.clear()
    return _generacion


def _vuelta_espejo() -> None:
    visto = 0
    time.sleep(PAUSA_PRIMERA_SEG)
    while True:
        _paso_nodo()
        visto = _esperar_turno(visto)


def _paso_carteleria() -> None:
    """Una vuelta de la tele. Si falla, la caché queda y no levanta error."""
    try:
        from src.carteleria.vitrina.pulso import pulso_vitrina

        salida = pulso_vitrina()
        origen = salida[1] if isinstance(salida, tuple) and len(salida) > 1 else "ok"
        logger.info("carteleria  %s", origen or "ok")
    except Exception as e:
        logger.warning("Vuelta de cartelería caída. La caché queda: %s", e)


def _paso_cola() -> None:
    """Sube tickets y cambios. Si salieron, el espejo los baja enseguida. Si la maestra no contesta, no toca la cola."""
    try:
        from src.base_de_datos.offline_sync import offline_sync_manager

        subida = offline_sync_manager.subir_colas()
    except Exception as e:
        logger.warning("cola  no se pudo subir: %s", e)
        return
    ventas = int(subida.get("ventas") or 0)
    stats = subida.get("stats") or {}
    cambios = (
        int(stats.get("productos", 0) or 0)
        + int(stats.get("recepciones", 0) or 0)
        + int(stats.get("clientes", 0) or 0)
    )
    if subida.get("ok") and (ventas or cambios):
        pedir_bajada()


def _vuelta_cola() -> None:
    time.sleep(15)
    while True:
        _paso_cola()
        time.sleep(20)


def _vuelta_carteleria() -> None:
    visto = 0
    time.sleep(PAUSA_PRIMERA_SEG)
    while True:
        _paso_carteleria()
        visto = _esperar_turno(visto)


def _prender(nombre: str, target, actual: threading.Thread | None) -> threading.Thread:
    if actual is not None and actual.is_alive():
        return actual
    hilo = threading.Thread(target=target, name=nombre, daemon=True)
    hilo.start()
    logger.info("hilo %s en marcha", nombre)
    return hilo


def cumplir_esclava() -> None:
    """Prende el espejo, la tele y la subida de la cola. No abre MariaDB."""
    global _hilo, _hilo_carteleria, _hilo_cola
    with _guardia:
        _hilo = _prender("oficio-esclava", _vuelta_espejo, _hilo)
        _hilo_carteleria = _prender("oficio-carteleria", _vuelta_carteleria, _hilo_carteleria)
        _hilo_cola = _prender("oficio-cola", _vuelta_cola, _hilo_cola)
        try:
            from src.central_red_global.servidor.pareja.reserva import prender

            prender()
        except Exception as e:
            logger.warning("pareja  no arranco la reserva: %s", e)


def rearmar_arranque() -> bool:
    """Reescribe el acceso directo de Windows con el programa de ahora."""
    from src.config import config

    if not config.get("auto_start_store_server", True):
        return False
    try:
        from src.central_red_global.servidor.autostart import set_os_autostart

        return bool(set_os_autostart(True))
    except Exception as e:
        logger.warning("No se pudo reescribir el arranque con Windows: %s", e)
        return False


def retomar_oficio() -> None:
    """Cierra el proceso viejo y deja uno con el oficio que dice la config."""
    from src.central_red_global.servidor.rol.apagar import detener_servidor_tienda_local

    detener_servidor_tienda_local()
    if not vigila_mariadb():
        try:
            from src.services.mariadb_controller import mariadb_controller

            mariadb_controller.stop_server()
        except Exception as e:
            logger.warning("MariaDB local sigue. El oficio esclava no lo usa: %s", e)
    rearmar_arranque()
    from src.central_red_global.servidor.arranque.proceso import ensure_store_server_process

    ensure_store_server_process(timeout_sec=40.0)
