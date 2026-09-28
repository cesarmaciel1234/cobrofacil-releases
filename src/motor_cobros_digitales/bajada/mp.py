"""Baja de MP todo lo que cambió desde la última marca. Si la PC estuvo apagada, recupera lo que entró."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from urllib.parse import quote

import requests

from src.logger import logger
from src.motor_cobros_digitales.libro import tabla

MARCA_DESDE = "mp_historial_desde"
MARCA_HASTA = "mp_historial_hasta"
FORMATO = "%Y-%m-%d %H:%M:%S"
VENTANA = timedelta(days=1)
SOLAPE = timedelta(hours=2)

_corriendo = threading.Lock()
_cuentas = {}


def _mp(momento: datetime) -> str:
    return quote(momento.strftime("%Y-%m-%dT%H:%M:%S.000-03:00"), safe="")


def _ahora() -> datetime:
    return datetime.now().replace(microsecond=0)


def _cuenta(token, headers):
    if token in _cuentas:
        return _cuentas[token]
    try:
        respuesta = requests.get("https://api.mercadopago.com/users/me", headers=headers, timeout=6, verify=False)
        if respuesta.status_code == 200:
            _cuentas[token] = (respuesta.json() or {}).get("id")
            return _cuentas[token]
    except Exception:
        pass
    return None


def _pagina(url, headers):
    for intento in range(3):
        try:
            respuesta = requests.get(url, headers=headers, timeout=15, verify=False)
        except Exception:
            respuesta = None
        if respuesta is not None and respuesta.status_code == 200:
            return (respuesta.json() or {}).get("results") or []
        if intento < 2:
            time.sleep(0.5)
    return None


def _ventana(headers, desde, hasta):
    """Pagos creados o modificados en la ventana (alta, aprobación, devolución). None si falló."""
    juntos = []
    for pagina_n in range(10):
        url = (
            "https://api.mercadopago.com/v1/payments/search"
            f"?sort=date_last_updated&criteria=asc&limit=100&offset={pagina_n * 100}"
            f"&range=date_last_updated&begin_date={_mp(desde)}&end_date={_mp(hasta)}"
        )
        pagina = _pagina(url, headers)
        if pagina is None:
            return None
        juntos.extend(pagina)
        if len(pagina) < 100:
            return juntos
    logger.warning(f"[Cobros digitales] Ventana {desde}–{hasta} con más de 1000 pagos: se guardan los primeros.")
    return juntos


def _marca(clave) -> datetime | None:
    try:
        return datetime.strptime(tabla.leer_marca(clave), FORMATO)
    except ValueError:
        return None


def _inicio() -> datetime:
    hasta = _marca(MARCA_HASTA)
    if hasta:
        return hasta - SOLAPE
    desde = _marca(MARCA_DESDE)
    if desde:
        return desde
    comienzo = _ahora().replace(day=1, hour=0, minute=0, second=0)
    tabla.poner_marca(MARCA_DESDE, comienzo.strftime(FORMATO))
    return comienzo


def ponerse_al_dia(token, desde: datetime | None = None) -> int:
    """
    Baja de MP todo lo que cambió desde la marca hasta ahora, por días, y lo guarda en `mp_pagos`.
    Corre la marca después de cada día guardado: si se corta, sigue desde ahí la próxima vez.
    `desde` fuerza un arranque anterior (recuperar meses viejos). Devuelve pagos guardados, -1 si no pudo.
    """
    token = str(token or "").strip()
    if not token:
        return 0
    if not _corriendo.acquire(blocking=False):
        return 0
    try:
        if not tabla.crear():
            return -1
        headers = {"Authorization": f"Bearer {token}"}
        mi_id = _cuenta(token, headers)
        inicio = desde or _inicio()
        fin = _ahora()
        total = 0
        mes_actual = fin.strftime("%Y-%m")
        while inicio < fin:
            tope = min(inicio + VENTANA, fin)
            pagos = _ventana(headers, inicio, tope)
            if pagos is None:
                return total if total else -1
            propios = [
                p for p in pagos
                if float(p.get("transaction_amount") or 0) > 0
                and (not mi_id or str(p.get("collector_id")) == str(mi_id))
            ]
            if tabla.guardar(propios) < 0:
                return total if total else -1
            total += len(propios)
            _al_monitor(propios, mes_actual)
            if desde is None or tope > (_marca(MARCA_HASTA) or datetime.min):
                tabla.poner_marca(MARCA_HASTA, tope.strftime(FORMATO))
            inicio = tope
        return total
    finally:
        _corriendo.release()


def _al_monitor(pagos, mes):
    """Los aprobados del mes también van al CSV de la grilla del monitor."""
    del_mes = [
        p for p in pagos
        if str(p.get("status") or "").lower() == "approved"
        and str(p.get("date_approved") or p.get("date_created") or "").startswith(mes)
    ]
    if not del_mes:
        return
    try:
        from src.admin.mercadopago.historial.archivo import guardar

        guardar(del_mes)
    except Exception:
        pass
