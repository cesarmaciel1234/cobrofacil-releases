"""Combina ranking/publicidad HTTP sobre el catálogo de MariaDB (no pisa PNG)."""

from __future__ import annotations


def aplicar_publicidad(data: dict) -> None:
    try:
        from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad

        pub = (data or {}).get("publicidad")
        if pub is not None:
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
        try:
            from src.central_red_global.sync_tienda.ranking.desde_payload import asegurar_ranking

            data = asegurar_ranking(data, master_ip)
        except Exception:
            pass
    pub = None
    if master_ip:
        try:
            from src.carteleria.vitrina.red.http_maestra import leer_publicidad_maestra

            pub = leer_publicidad_maestra(master_ip)
        except Exception:
            pub = None
    if pub is None and http_data and http_data.get("publicidad") is not None:
        pub = http_data.get("publicidad")
    if pub is not None:
        data["publicidad"] = pub
    aplicar_publicidad(data)
    reporte = None
    if master_ip:
        try:
            from src.carteleria.vitrina.red.http_maestra import leer_reporte_maestra

            reporte = leer_reporte_maestra(master_ip)
        except Exception:
            reporte = None
    if reporte is None and http_data and isinstance(http_data.get("reporte"), dict):
        reporte = http_data.get("reporte")
    if reporte is None:
        try:
            from src.jefe.reportes.financiero.consulta import payload_reporte_global

            reporte = payload_reporte_global()
        except Exception:
            reporte = None
    if reporte is not None:
        data["reporte"] = reporte
    return data
