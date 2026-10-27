"""
Re-export para compatibilidad histórica con módulos que importan desde src.services.facturacion_service.
El núcleo modularizado en pirámide vive en src/afip/.
"""
from src.afip.facturacion_service import FacturacionService

__all__ = ["FacturacionService"]
