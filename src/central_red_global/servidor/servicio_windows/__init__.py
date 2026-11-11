"""Servicio nativo de Windows (Session 0) para `--server`."""

from src.central_red_global.servidor.servicio_windows.gestor import (
    SERVICE_DESCRIPTION,
    SERVICE_DISPLAY_NAME,
    SERVICE_NAME,
    build_service_binpath,
    desinstalar_servicio_windows,
    detener_servicio_windows,
    es_administrador,
    estado_servicio_windows,
    iniciar_servicio_windows,
    instalar_servicio_con_uac,
    instalar_servicio_windows,
    servicio_en_ejecucion,
    servicio_instalado,
)
from src.central_red_global.servidor.servicio_windows.servicio import run_windows_service

__all__ = [
    "SERVICE_NAME",
    "SERVICE_DISPLAY_NAME",
    "SERVICE_DESCRIPTION",
    "build_service_binpath",
    "estado_servicio_windows",
    "servicio_instalado",
    "servicio_en_ejecucion",
    "es_administrador",
    "iniciar_servicio_windows",
    "detener_servicio_windows",
    "instalar_servicio_windows",
    "desinstalar_servicio_windows",
    "instalar_servicio_con_uac",
    "run_windows_service",
]
