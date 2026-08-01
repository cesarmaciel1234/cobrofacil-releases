"""
inventario_service.py - Servicio simple para manejar los productos y departamentos del almacén (inventario).
Nivel Medio: Encapsula el motor catalogo y la importacion para que la UI no llame directamente a carpetas bajas.
Nombres comprensibles para un niño de 10 años.
"""

from src.motor_inventario.motor_catalogo import MotorCatalogo
from src.motor_inventario.motor_importacion import MotorImportacion

class InventarioService:
    @staticmethod
    def obtener_lista_de_productos(buscar="", depto="", limite=50000, offset=0) -> tuple[list, bool]:
        """Busca productos según un texto o departamento. Devuelve (lista_de_productos, tiene_mas)."""
        motor = MotorCatalogo()
        return motor.obtener_productos(buscar, depto, limite, offset)

    @staticmethod
    def buscar_producto_por_id(producto_id) -> dict | None:
        """Busca y devuelve un producto usando su ID."""
        motor = MotorCatalogo()
        return motor.obtener_producto_por_id(producto_id)

    @staticmethod
    def borrar_producto(producto_id) -> bool:
        """Elimina un producto del inventario de forma permanente."""
        motor = MotorCatalogo()
        return motor.borrar_producto(producto_id)

    @staticmethod
    def guardar_producto(datos_producto: dict, es_nuevo: bool = True, producto_id = None) -> tuple[bool, str]:
        """Crea o actualiza un producto en la base de datos."""
        motor = MotorCatalogo()
        return motor.guardar_producto(datos_producto, is_new=es_nuevo, prod_id=producto_id)

    @staticmethod
    def unificar_duplicados() -> tuple[bool, str]:
        """Busca productos repetidos con el mismo código y los une en uno solo."""
        motor = MotorCatalogo()
        return motor.unificar_duplicados()

    @staticmethod
    def exportar_a_excel(ruta_archivo: str) -> tuple[bool, str]:
        """Exporta todo el inventario a un archivo Excel (.xlsx)."""
        motor_imp = MotorImportacion()
        return motor_imp.exportar_excel(ruta_archivo)

    @staticmethod
    def importar_desde_excel(ruta_archivo: str) -> tuple[bool, str]:
        """Importa productos al inventario desde un archivo Excel (.xlsx)."""
        motor_imp = MotorImportacion()
        return motor_imp.importar_excel(ruta_archivo)

    @staticmethod
    def descargar_productos_nube() -> tuple[bool, str]:
        """Descarga e importa productos pre-cargados desde la nube."""
        motor_imp = MotorImportacion()
        return motor_imp.descargar_precarga()
