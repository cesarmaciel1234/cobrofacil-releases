"""Puente a la consulta del motor de auditoría. La pantalla no lee ventas sola."""

from src.motor_auditoria_digital.consultas.rango import filtro as rango_filtro
from src.motor_auditoria_digital.consultas.tickets import listar

__all__ = ["rango_filtro", "listar"]
