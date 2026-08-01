# motor_catalogo.py - Wrapper de compatibilidad hacia atras para el Catalogo.
import logging
from src.motor_inventario.base import productos_db
from src.motor_inventario.procesos import buscador_productos, editor_productos

class MotorCatalogo:
    def __init__(self):
        self.logger = logging.getLogger("MotorCatalogo")

    def obtener_productos(self, buscar="", depto="", limite=50, offset=0):
        # Devuelve (filas_dict, tiene_mas)
        return buscador_productos.buscar_productos_en_db(buscar, depto, limite, offset)

    def obtener_producto_por_id(self, id_producto):
        return buscador_productos.buscar_producto_por_id(id_producto)

    def obtener_producto_por_codigo(self, codigo):
        return buscador_productos.buscar_producto_por_codigo(codigo)

    def obtener_total_productos(self):
        return productos_db.contar_todos_los_productos()

    def obtener_total_sin_stock(self):
        return productos_db.contar_productos_sin_stock()

    def borrar_producto(self, _id):
        return productos_db.eliminar_producto_de_db(_id)

    def actualizar_precio_por_nombre(self, nombre, precio):
        return productos_db.actualizar_precio_por_nombre(nombre, precio)

    def unificar_duplicados(self):
        return editor_productos.unificar_productos_duplicados()

    def guardar_producto(self, params_dict, is_new=True, prod_id=None):
        return editor_productos.guardar_producto_en_db(params_dict, is_new, prod_id)

    def verificar_codigo_existe(self, codigo, id_excluir=None):
        return editor_productos.comprobar_si_codigo_existe(codigo, id_excluir)

    def verificar_nombre_existe(self, nombre, id_excluir=None):
        return editor_productos.comprobar_si_nombre_existe(nombre, id_excluir)
