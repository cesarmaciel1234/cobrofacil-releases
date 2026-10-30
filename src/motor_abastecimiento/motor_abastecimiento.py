from src.config import config
from src.logger import logger
from src.motor_abastecimiento.detector import obtener_productos_bajo_minimo
from src.motor_abastecimiento.enlace import (
    asegurar_tabla_enlace,
    asignar_proveedor,
    obtener_mapeos,
    asociar_proveedores_a_productos,
)
from src.motor_abastecimiento.exportador import (
    generar_texto_whatsapp,
    generar_resumen_general
)

class MotorAbastecimiento:
    """
    Orquestador principal de Reabastecimiento Automático por Punto de Pedido.
    Detecta productos bajo stock mínimo, los asocia con sus proveedores
    y genera pedidos listos para WhatsApp sin tocar la lógica del inventario ni del cajero.
    """

    @staticmethod
    def inicializar():
        """Inicializa estructuras auxiliares no destructivas."""
        asegurar_tabla_enlace()

    @staticmethod
    def obtener_resumen_reposicion(nombre_comercio=None):
        """
        Ejecuta el ciclo completo de reposición:
        1. Detecta faltantes bajo stock mínimo.
        2. Agrupa por proveedor según enlaces configurados.
        3. Prepara los textos formateados para WhatsApp.
        4. Retorna el resumen consolidado para la interfaz.
        """
        if not nombre_comercio:
            nombre_comercio = config.get("business_name", "Mi Comercio")

        faltantes = obtener_productos_bajo_minimo()
        agrupados = asociar_proveedores_a_productos(faltantes)

        # Generar texto de WhatsApp para cada proveedor
        for prov_nombre, datos in agrupados.items():
            if datos.get("total_items"):
                datos["texto_whatsapp"] = generar_texto_whatsapp(datos, nombre_comercio)

        return generar_resumen_general(agrupados)

    @staticmethod
    def vincular_proveedor(
        criterio_tipo, criterio_valor, proveedor_nombre,
        telefono="", email="", proveedor_id=None,
    ):
        """
        Vincula un departamento o un producto específico con un proveedor.
        Ejemplo: vincular_proveedor('departamento', 'LACTEOS', 'Distribuidora Láctea', '1123456789')
        """
        return asignar_proveedor(
            criterio_tipo, criterio_valor, proveedor_nombre, telefono, email, proveedor_id
        )

    @staticmethod
    def listar_vinculaciones():
        """Retorna la lista de reglas de vinculación entre catálogo y proveedores."""
        return obtener_mapeos()

    @staticmethod
    def listar_proveedores():
        """Fichas con id y código P00012. En casa también entran las que esperan el id."""
        from src.proveedor_global.backend.ficha import FichaProveedor

        return FichaProveedor.listar()
