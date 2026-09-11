"""Combina ranking/publicidad HTTP sobre el catálogo de MariaDB (no pisa PNG)."""

from __future__ import annotations


def aplicar_publicidad(data: dict) -> None:
    try:
        from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad

        pub = (data or {}).get("publicidad")
        if pub:
            motor_publicidad.aplicar_remoto(pub)
        else:
            motor_publicidad.cargar_configuracion(forzar=True)
            if data is not None:
                data["publicidad"] = motor_publicidad.as_dict()
    except Exception:
        pass


def fusionar_http(data_db: dict, http_data: dict | None, master_ip: str) -> dict:
    data = data_db or {}
    if http_data:
        if http_data.get("ranking"):
            data["ranking"] = http_data.get("ranking")
        if http_data.get("top10"):
            data["top10"] = http_data.get("top10")
        if http_data.get("publicidad"):
            data["publicidad"] = http_data.get("publicidad")
        try:
            from src.central_red_global.sync_tienda.ranking.desde_payload import asegurar_ranking

            data = asegurar_ranking(data, master_ip)
        except Exception:
            pass
    aplicar_publicidad(data)
    return data
