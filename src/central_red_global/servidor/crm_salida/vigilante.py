"""Módulo aparte del servidor. Si falla, la tienda sigue.

Por ahora la esclava también envía: trae los datos de la maestra
y con eso se trabaja en la web. Más adelante, SOLO_MAESTRA = True.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time

from src.central_red_global.servidor.crm_salida.proceso import comando, ruta_punpro

logger = logging.getLogger("crm_salida")

# Plan gratis. Neon se duerme a los 5 min y Render a los 15.
# La tienda hace unos 70 tickets por día (pico 89). El libro completo
# tarda cerca de una hora, así que no se manda en cada venta.
# Se mira cada 15 min. Si cambió, sale como mucho una vez cada 3 horas.
PAUSA_PRIMERA_SEG = 60.0
PAUSA_VUELTA_SEG = 15 * 60.0
MINIMO_ENTRE_ENVIOS_SEG = 3 * 60 * 60.0
TOPE_ENVIO_SEG = 2 * 60 * 60
# Más adelante queda en True: solo la maestra manda el dato centralizado.
SOLO_MAESTRA = False

_guardia = threading.Lock()
_hilo: threading.Thread | None = None
_parar = threading.Event()
_despertar = threading.Event()
_ultimo_aviso = ""


def leer_credenciales(origen: dict | None = None) -> dict | None:
    """URL, clave, empresa y sucursal. Sin eso no hay envío."""
    if origen is None:
        try:
            from src.config import config

            origen = {
                "crm_url": config.get("crm_url"),
                "crm_api_key": config.get("crm_api_key"),
                "crm_usuario": config.get("crm_usuario"),
                "crm_password": config.get("crm_password"),
                "crm_empresa": config.get("crm_empresa"),
                "crm_empresa_id": config.get("crm_empresa_id"),
                "crm_sucursal_id": config.get("crm_sucursal_id") or config.get("sucursal_id"),
                "crm_sucursal": config.get("crm_sucursal"),
            }
        except Exception:
            return None
    url = str(origen.get("crm_url") or "").strip().rstrip("/")
    clave = str(origen.get("crm_api_key") or "").strip()
    usuario = str(origen.get("crm_usuario") or "").strip()
    password = str(origen.get("crm_password") or "")
    empresa = str(origen.get("crm_empresa") or usuario).strip()
    empresa_id = str(origen.get("crm_empresa_id") or "").strip()
    sucursal_id = str(origen.get("crm_sucursal_id") or "").strip() or "1"
    sucursal = str(origen.get("crm_sucursal") or "").strip() or empresa
    if not url or not (clave or (usuario and password)) or not (empresa or empresa_id):
        return None
    return {
        "url": url,
        "clave": clave,
        "usuario": usuario,
        "password": password,
        "empresa": empresa,
        "empresa_id": empresa_id,
        "sucursal_id": sucursal_id,
        "sucursal": sucursal,
    }


def turno(rol: str, credenciales: dict | None, lanzar, *, solo_maestra: bool = SOLO_MAESTRA) -> str:
    """Una vuelta. Un fallo vuelve como texto y el servidor sigue."""
    if solo_maestra and rol != "maestra":
        return "esclava"
    if not credenciales:
        return "sin_datos"
    try:
        lanzar(credenciales)
    except Exception:
        logger.exception("CRM  el envío falló y el servidor sigue")
        return "fallo"
    return "enviado"


def lanzar(credenciales: dict) -> None:
    """Otro proceso lee punpro.db y hace el POST. La clave no va en el comando."""
    from src.central_red_global.servidor.crm_salida.motor import huella, leer_clientes, manifiesto

    ruta_db = ruta_punpro()
    clientes = leer_clientes(ruta_db)
    marca = "|".join(
        [
            credenciales.get("url") or "",
            credenciales.get("empresa") or "",
            credenciales.get("empresa_id") or "",
            str(credenciales.get("sucursal_id") or ""),
            credenciales.get("sucursal") or "",
            manifiesto(ruta_db),
        ]
    )
    firma = huella(clientes, marca)
    carpeta = os.path.join(os.path.dirname(ruta_db) or ".", "locks")
    ruta_firma = os.path.join(carpeta, "crm_cartera_huella.txt")
    ruta_cuando = os.path.join(carpeta, "crm_cartera_cuando.txt")
    try:
        with open(ruta_firma, encoding="utf-8") as archivo:
            previa = archivo.read().strip()
    except OSError:
        previa = ""
    if previa == firma:
        logger.info("CRM  la base sigue igual. No se reenvía.")
        return
    try:
        with open(ruta_cuando, encoding="utf-8") as archivo:
            ultimo = float(archivo.read().strip() or 0)
    except (OSError, ValueError):
        ultimo = 0.0
    falta = MINIMO_ENTRE_ENVIOS_SEG - (time.time() - ultimo)
    if ultimo and falta > 0:
        logger.info("CRM  hay cambios. El turno gratis abre en %s min.", int(falta // 60) + 1)
        return

    programa, args = comando()
    entorno = os.environ.copy()
    entorno["CRM_URL"] = credenciales["url"]
    entorno["CRM_API_KEY"] = credenciales.get("clave") or ""
    entorno["CRM_USER"] = credenciales.get("usuario") or ""
    entorno["CRM_PASSWORD"] = credenciales.get("password") or ""
    entorno["CRM_EMPRESA"] = credenciales.get("empresa") or ""
    entorno["CRM_EMPRESA_ID"] = credenciales.get("empresa_id") or ""
    entorno["CRM_SUCURSAL_ID"] = str(credenciales.get("sucursal_id") or "")
    entorno["CRM_SUCURSAL"] = credenciales.get("sucursal") or ""
    entorno["PUNPRO_DB"] = ruta_punpro()
    proc = subprocess.Popen(
        [programa, *args],
        env=entorno,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=os.path.dirname(ruta_punpro()) or None,
    )
    try:
        crudo, _ = proc.communicate(timeout=TOPE_ENVIO_SEG)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise RuntimeError("el envío tardó demasiado")
    texto = (crudo or b"").decode("utf-8", errors="replace")
    dato = {}
    for candidato in reversed(texto.splitlines()):
        candidato = candidato.strip()
        if candidato.startswith("{"):
            try:
                dato = json.loads(candidato)
            except json.JSONDecodeError:
                dato = {}
            break
    if proc.returncode != 0 or dato.get("ok") is False:
        detalle = str(dato.get("error") or texto or f"código {proc.returncode}")
        raise RuntimeError(detalle[:180])
    logger.info(
        "CRM  cartera enviada  %s leídos, %s nuevos, %s actualizados",
        dato.get("leidos", dato.get("total", "")),
        dato.get("creados", 0),
        dato.get("actualizados", 0),
    )
    try:
        os.makedirs(os.path.dirname(ruta_firma), exist_ok=True)
        with open(ruta_firma, "w", encoding="utf-8") as archivo:
            archivo.write(firma)
        with open(ruta_cuando, "w", encoding="utf-8") as archivo:
            archivo.write(str(time.time()))
    except OSError:
        logger.warning("CRM  se envió, pero no pude anotar que la cartera ya está al día")


def _rol() -> str:
    from src.central_red_global.servidor.oficio.agente import oficio

    return oficio()


def _vuelta() -> None:
    global _ultimo_aviso
    try:
        rol = _rol()
    except Exception as exc:
        if SOLO_MAESTRA:
            logger.error("CRM  no pude leer si esta PC es maestra: %s", exc)
            return
        rol = "esclava"
    credenciales = leer_credenciales()
    resultado = turno(rol, credenciales, lanzar)
    if resultado == "esclava":
        if _ultimo_aviso != "esclava":
            logger.info("CRM  esta PC es esclava. No envía. La maestra manda el dato centralizado.")
            _ultimo_aviso = "esclava"
        return
    if resultado == "sin_datos":
        if _ultimo_aviso != "sin_datos":
            logger.info("CRM  falta el nombre de la empresa. El servidor sigue.")
            _ultimo_aviso = "sin_datos"
        return
    _ultimo_aviso = "maestra"
    if resultado == "fallo":
        logger.error("CRM  esta vuelta no salió. La próxima vuelve a intentar. El servidor sigue.")


def _ciclo() -> None:
    pausa = PAUSA_PRIMERA_SEG
    logger.info("CRM  módulo aparte en marcha. La esclava también envía los datos de la maestra.")
    while not _parar.is_set():
        _despertar.wait(pausa)
        _despertar.clear()
        if _parar.is_set():
            break
        pausa = PAUSA_VUELTA_SEG
        try:
            _vuelta()
        except Exception as exc:
            logger.error("CRM  el módulo falló una vuelta y el servidor sigue: %s", exc)


def prender() -> None:
    """Arranca el hilo una sola vez. No toca MariaDB ni el espejo."""
    global _hilo
    with _guardia:
        if _hilo is not None and _hilo.is_alive():
            return
        _parar.clear()
        _hilo = threading.Thread(target=_ciclo, name="crm-salida", daemon=True)
        _hilo.start()


def pedir_vuelta() -> None:
    """La ventana guardó la empresa. La próxima vuelta no espera los dos minutos."""
    _despertar.set()


def apagar() -> None:
    _parar.set()
    _despertar.set()
