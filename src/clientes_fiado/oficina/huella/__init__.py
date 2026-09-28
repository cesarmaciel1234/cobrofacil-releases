"""Huella de clientes: ID único, quién/dónde/cuándo, y la tienda que chupa lo hecho sin red."""

from src.clientes_fiado.oficina.huella.absorber import arrancar, despertar, estado, turno
from src.clientes_fiado.oficina.huella.eventos import alta, editar, movimiento_en
from src.clientes_fiado.oficina.huella.pc import pc_id

__all__ = ["alta", "arrancar", "despertar", "editar", "estado", "movimiento_en", "pc_id", "turno"]
