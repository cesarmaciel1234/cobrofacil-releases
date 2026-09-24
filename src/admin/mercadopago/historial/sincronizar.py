import requests

from src.admin.mercadopago.historial.archivo import _ids, guardar


def bajar_mes(token):
    """Baja los cobros aprobados del mes con el token de la config. Devuelve cuántos guardó."""
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
    from datetime import datetime

    comienzo = datetime.now().strftime("%Y-%m") + "-01T00:00:00.000-03:00"
    vistos = _ids()
    acumulados = []
    offset = 0
    for _ in range(100):
        url = (
            "https://api.mercadopago.com/v1/payments/search"
            f"?sort=date_created&criteria=desc&limit=100&offset={offset}"
            f"&status=approved&range=date_created&begin_date={comienzo}"
        )
        try:
            respuesta = requests.get(url, headers=headers, timeout=12, verify=False)
        except Exception:
            break
        if respuesta.status_code != 200:
            break
        pagina = (respuesta.json() or {}).get("results") or []
        if not pagina:
            break
        acumulados.extend(pagina)
        if vistos and all(str(pago.get("id", "")).strip() in vistos for pago in pagina):
            break
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
    return guardar(propios)
