"""Módulo autónomo de avisos. La interfaz no decide y el motor no pinta."""

from src.notificaciones.interfaz.centro import CentroDeNotificaciones
from src.notificaciones.motor.estado import publicar, retirar
from src.notificaciones.motor.revisar import revisar_notificaciones

__all__ = ["CentroDeNotificaciones", "publicar", "retirar", "revisar_notificaciones"]
