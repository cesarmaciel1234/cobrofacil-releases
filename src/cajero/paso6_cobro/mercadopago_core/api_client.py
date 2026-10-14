import datetime
import threading
from urllib.parse import quote

import requests


def fecha_busqueda_mp(resta=None):
    """Formato de /v1/payments/search: 2026-09-24T12:35:50.000-03:00."""
    zona = datetime.timezone(datetime.timedelta(hours=-3))
    momento = datetime.datetime.now(zona)
    if resta:
        momento = momento - resta
    return quote(momento.strftime("%Y-%m-%dT%H:%M:%S.000-03:00"), safe="")


class MPApiClient:
    _sesion = None
    _lock = threading.Lock()

    @classmethod
    def sesion(cls):
        if cls._sesion is None:
            cls._sesion = requests.Session()
        return cls._sesion

    @staticmethod
    def get_headers(token, json_content=True):
        headers = {"Authorization": f"Bearer {token}"}
        if json_content:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def post(url, payload, token, timeout=10, extra_headers=None):
        headers = MPApiClient.get_headers(token)
        if extra_headers:
            headers.update(extra_headers)
        with MPApiClient._lock:
            return MPApiClient.sesion().post(url, json=payload, headers=headers, timeout=timeout)

    @staticmethod
    def put(url, payload, token, timeout=10):
        with MPApiClient._lock:
            return MPApiClient.sesion().put(url, json=payload, headers=MPApiClient.get_headers(token), timeout=timeout)

    @staticmethod
    def get(url, token, timeout=10):
        with MPApiClient._lock:
            return MPApiClient.sesion().get(url, headers=MPApiClient.get_headers(token, False), timeout=timeout)

    @staticmethod
    def delete(url, token, timeout=5):
        with MPApiClient._lock:
            return MPApiClient.sesion().delete(url, headers=MPApiClient.get_headers(token, False), timeout=timeout)
