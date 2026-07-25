"""
Paquete de Módulos Independientes para la Cartelería Digital Basada en las Ventas y Tickets de HOY.
Cada módulo se encarga de un cartel o sección específica (Los Más Elegidos Hoy, Más Volumen Hoy, Recomendado Hoy, Ofertas y Destacados Hoy, Venta Cruzada Inteligente).
Al estar 100% divididos y modularizados, ningún cambio en uno afectará a los demás.
"""

from src.carteleria.motor_carteleria.modulos_ventas_hoy.mas_elegidos_hoy import ModuloMasElegidosHoy
from src.carteleria.motor_carteleria.modulos_ventas_hoy.mas_volumen_hoy import ModuloMasVolumenHoy
from src.carteleria.motor_carteleria.modulos_ventas_hoy.recomendados_hoy import ModuloRecomendadoHoy
from src.carteleria.motor_carteleria.modulos_ventas_hoy.ofertas_y_destacados_hoy import ModuloOfertasYDestacadosHoy
from src.carteleria.motor_carteleria.modulos_ventas_hoy.buscador_precios_y_stock import BuscadorDePreciosYStock
from src.carteleria.motor_carteleria.modulos_ventas_hoy.venta_cruzada_inteligente import VentaCruzadaInteligente

__all__ = [
    "ModuloMasElegidosHoy",
    "ModuloMasVolumenHoy",
    "ModuloRecomendadoHoy",
    "ModuloOfertasYDestacadosHoy",
    "BuscadorDePreciosYStock",
    "VentaCruzadaInteligente"
]
