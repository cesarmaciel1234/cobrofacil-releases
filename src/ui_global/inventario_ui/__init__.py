# Capa de compatibilidad: re-exporta desde nuevas ubicaciones piramidales
# Garantiza que imports externos como `from src.ui_global.inventario_ui.inventario_main import ...` sigan funcionando
from src.ui_global.inventario_ui.vistas.inventario_main import Admin1Inventario

__all__ = ["Admin1Inventario"]
