from src.repositories.producto_repository import ProductoRepository

class VentasService:
    """
    Capa de Servicios para Ventas.
    Contiene la Lógica de Negocio pura (matemáticas, reglas de negocio),
    desacoplada de la interfaz gráfica y de la base de datos directa.
    """

    @staticmethod
    def procesar_escaneo(codigo_barras: str) -> dict:
        """
        Lógica que se ejecuta cuando el cajero escanea un producto.
        Retorna un diccionario con el estado y los datos procesados.
        """
        # 1. Obtenemos el producto de la capa de datos
        producto = ProductoRepository.obtener_por_id(codigo_barras)
        
        if not producto:
            return {"status": "error", "message": "Producto no encontrado"}
            
        # 2. Aplicamos reglas de negocio (Matemáticas, descuentos)
        precio_base = float(producto.get('precio', 0.0))
        precio_final = precio_base
        es_oferta_relampago = False
        
        # Evaluamos Oferta Relámpago
        precio_relampago = float(producto.get('precio_oferta_relampago', 0.0))
        if precio_relampago > 0 and precio_relampago < precio_base:
            precio_final = precio_relampago
            es_oferta_relampago = True

        return {
            "status": "success",
            "producto": producto,
            "precio_final": precio_final,
            "es_oferta_relampago": es_oferta_relampago
        }
