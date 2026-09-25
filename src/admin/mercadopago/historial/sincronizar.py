import time

import requests
from datetime import datetime
from urllib.parse import quote

from src.admin.mercadopago.historial.archivo import _ids, guardar
from src.cajero.paso6_cobro.mercadopago_core.api_client import fecha_busqueda_mp


def _pagina(url, headers):
    """Una página del mes. None si las tres veces falló."""
    for intento in range(3):
        try:
            respuesta = requests.get(url, headers=headers, timeout=12, verify=False)
        except Exception:
            respuesta = None
        if respuesta is not None and respuesta.status_code == 200:
            return (respuesta.json() or {}).get("results") or []
        if intento < 2:
            time.sleep(0.4)
    return None


def bajar_mes(token):
    """Baja los cobros aprobados del mes con el token de la config. Devuelve cuántos guardó. -1 si no pudo leer la primera página."""
    token = str(token or "").strip()
    if not token:
        return 0
    headers = {"Authorization": f"Bearer {token}"}
    mi_id = None
    try:
        respuesta = requests.get(
            "https://api.mercadopago.com/users/me",
            headers=headers,
            timeout=5,
            verify=False,
        )
        if respuesta.status_code == 200:
            mi_id = (respuesta.json() or {}).get("id")
    except Exception:
        pass
    comienzo = quote(datetime.now().strftime("%Y-%m-01T00:00:00.000-03:00"), safe="")
    fin = fecha_busqueda_mp()
    vistos = _ids()
    acumulados = []
    offset = 0
    hubo_pagina = False
    for _ in range(20):
        url = (
            "https://api.mercadopago.com/v1/payments/search"
            f"?sort=date_created&criteria=desc&limit=100&offset={offset}"
            f"&status=approved&range=date_created&begin_date={comienzo}&end_date={fin}"
        )
        pagina = _pagina(url, headers)
        if pagina is None:
            if not hubo_pagina:
                return -1
            break
        hubo_pagina = True
        if not pagina:
            break
        acumulados.extend(pagina)
        if len(pagina) < 100:
            break
        offset += 100
    propios = []
    for pago in acumulados:
        if float(pago.get("transaction_amount") or 0) <= 0:
            continue
        if mi_id and str(pago.get("collector_id")) != str(mi_id):
            continue
        propios.append(pago)
    faltan = [
        pago for pago in propios
        if str(pago.get("id", "")).strip() and str(pago.get("id", "")).strip() not in vistos
    ]
    guardados = guardar(propios)
    if faltan and guardados == 0:
        return -1
    return guardados
