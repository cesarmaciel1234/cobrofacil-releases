from .condiciones_credito import generador_credito
from .condiciones_venta import generador_venta
from .condiciones_cierre import generador_cierre

class MotorCondiciones:
    """
    Fachada orquestadora para la generación de condiciones y mensajes extra
    en los diferentes documentos del sistema.
    """

    @classmethod
    def obtener_condiciones(cls, contexto: str, subcontexto: str = "", **kwargs) -> str:
        """
        Rutea la petición al submotor adecuado según el contexto.
        Contextos soportados: 'credito', 'venta', 'cierre'
        """
        if contexto == "credito":
            return generador_credito.generar_texto(subcontexto=subcontexto, **kwargs)
        elif contexto == "venta":
            return generador_venta.generar_texto(subcontexto=subcontexto, **kwargs)
        elif contexto == "cierre":
            return generador_cierre.generar_texto(subcontexto=subcontexto, **kwargs)
        else:
            return f"--- Fin del documento ({contexto}) ---"
