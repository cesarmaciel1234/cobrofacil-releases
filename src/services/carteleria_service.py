import json
import os
import time
from src.utils.paths import get_base_path

class CarteleriaService:
    """
    Capa de Servicios para la comunicación con la Cartelería Inteligente.
    Aísla la lógica de red y archivos temporales (live_scan.json) de la UI.
    """

    @staticmethod
    def _get_live_scan_path():
        return os.path.join(get_base_path(), "live_scan.json")

    @staticmethod
    def limpiar_carteleria():
        """Envía la señal a la Cartelería para que aborte la pantalla espía y vuelva al carrusel."""
        path = CarteleriaService._get_live_scan_path()
        for attempt in range(5):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"carrito": [], "ahorro": 0.0, "timestamp": time.time(), "limpiar": True}, f, ensure_ascii=False)
                return True
            except PermissionError:
                time.sleep(0.05)
            except Exception:
                return False
        return False

    @staticmethod
    def notificar_escaneo(carrito: list, ahorro_total: float, ultimo_producto: str, total_carrito: float = 0.0):
        """Envía el estado actual del carrito a la Cartelería para que evalúe combos / recomendaciones."""
        path = CarteleriaService._get_live_scan_path()
        for attempt in range(5):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({
                        "carrito": carrito,
                        "ahorro": ahorro_total,
                        "total": total_carrito,
                        "timestamp": time.time(),
                        "limpiar": False,
                        "ultimo_escaneado": ultimo_producto
                    }, f, ensure_ascii=False)
                return True
            except PermissionError:
                time.sleep(0.05)
            except Exception:
                return False
        return False
