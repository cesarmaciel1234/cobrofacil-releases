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
    from src.admin.mercadopago.historial.cuentas import (
        asegurar_inicializacion,
        es_pago_valido_en_periodo,
        nombre_cuenta_para_pago,
        rango_activo_token_actual,
    )
    from src.admin.mercadopago.historial.archivo import _fecha_ar

    asegurar_inicializacion()
    activo_desde, activo_hasta = rango_activo_token_actual()

    primer_dia_mes = datetime.now().strftime("%Y-%m-01 00:00:00")
    inicio_busqueda = primer_dia_mes
    if activo_desde and activo_desde > primer_dia_mes:
        inicio_busqueda = activo_desde

    try:
        dt_ini = datetime.strptime(inicio_busqueda[:19], "%Y-%m-%d %H:%M:%S")
        comienzo = quote(dt_ini.strftime("%Y-%m-%dT%H:%M:%S.000-03:00"), safe="")
    except Exception:
        comienzo = quote(datetime.now().strftime("%Y-%m-01T00:00:00.000-03:00"), safe="")

    if activo_hasta:
        try:
            dt_fin = datetime.strptime(activo_hasta[:19], "%Y-%m-%d %H:%M:%S")
            fin = quote(dt_fin.strftime("%Y-%m-%dT%H:%M:%S.000-03:00"), safe="")
        except Exception:
            fin = fecha_busqueda_mp()
    else:
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
        cid = str(pago.get("collector_id") or mi_id or "")
        if mi_id and cid and str(pago.get("collector_id")) != str(mi_id):
            continue
        f_pago = _fecha_ar(pago.get("date_approved") or pago.get("date_created"))
        if not es_pago_valido_en_periodo(f_pago, cid):
            continue
        pago["cuenta_nombre"] = nombre_cuenta_para_pago(cid, f_pago)
        propios.append(pago)
    faltan = [
        pago for pago in propios
        if str(pago.get("id", "")).strip() and str(pago.get("id", "")).strip() not in vistos
    ]
    guardados = guardar(propios)
    if faltan and guardados == 0:
        return -1
    return guardados
