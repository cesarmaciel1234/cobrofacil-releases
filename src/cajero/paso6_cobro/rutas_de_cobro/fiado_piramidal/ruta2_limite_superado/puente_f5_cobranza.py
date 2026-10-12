# -*- coding: utf-8 -*-
"""
Puente de retrocompatibilidad:
El módulo de cobranza ahora se encuentra independizado en:
src.cajero.paso6_cobro.rutas_de_cobro.fiado_piramidal.modulo_cobranza.panel_cobranza
"""
from ..modulo_cobranza.panel_cobranza import PanelCobranza, PuenteF5Cobranza

__all__ = ["PanelCobranza", "PuenteF5Cobranza"]
