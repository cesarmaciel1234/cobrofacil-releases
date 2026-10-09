from .traductor_comandos import generador_escpos
from .conexion_puerto import enviador_datos

class ImpresoraGlobal:
    """
    Motor global principal de impresión.
    Es un actor 'tonto': sólo recibe un paquete de datos e instrucciones,
    no sabe de dónde viene ni quién lo generó, y lo ejecuta en el hardware.
    """

    @classmethod
    def procesar_paquete(cls, paquete: dict) -> bool:
        """
        Punto de entrada principal.
        :param paquete: Diccionario con la estructura de lo que se debe imprimir.
                        Ej: {"lineas": [...], "cortar": True, "abrir_cajon": False}
        :return: bool indicando éxito o fracaso.
        """
        # 1. Convertir el paquete a comandos nativos de la impresora (ej. ESC/POS)
        datos_crudos = generador_escpos.traducir(paquete)
        
        # 2. Enviar la ráfaga de bytes al puerto configurado
        resultado = enviador_datos.enviar(datos_crudos)
        
        return resultado
