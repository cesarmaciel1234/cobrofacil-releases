import json
import os
import time
from src.utils.paths import get_base_path

import socket

class CarteleriaService:
    """
    Capa de Servicios para la comunicación con la Cartelería Inteligente.
    Aísla la lógica de red y archivos temporales (live_scan.json) de la UI.
    Ahora utiliza UDP Broadcast en el puerto 37021 para notificar a todas
    las cartelerías en tiempo real sin requerir archivos temporales.
    """

    @staticmethod
    def _get_live_scan_path():
        from src.utils.paths import get_base_path
        return os.path.join(get_base_path(), "live_scan.json")
        
    @staticmethod
    def _enviar_udp_broadcast(payload: dict):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            mensaje = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            sock.sendto(mensaje, ('255.255.255.255', 37021))
            sock.close()
            return True
        except Exception:
            return False

    @staticmethod
    def limpiar_carteleria():
        """Envía la señal a la Cartelería para que aborte la pantalla espía y vuelva al carrusel."""
        payload = {"carrito": [], "ahorro": 0.0, "timestamp": time.time(), "limpiar": True}
        CarteleriaService._enviar_udp_broadcast(payload)
        
        # Opcional: mantener el archivo por compatibilidad con código antiguo
        path = CarteleriaService._get_live_scan_path()
        for attempt in range(2):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False)
                break
            except Exception:
                time.sleep(0.05)
        return True

    @staticmethod
    def notificar_escaneo(carrito: list, ahorro_total: float, ultimo_producto: str):
        """Envía el estado actual del carrito a la Cartelería para que evalúe si debe mostrar recomendaciones."""
        payload = {
            "carrito": carrito,
            "ahorro": ahorro_total,
            "timestamp": time.time(),
            "limpiar": False,
            "ultimo_escaneado": ultimo_producto
        }
        CarteleriaService._enviar_udp_broadcast(payload)
        
        # Opcional: mantener el archivo por compatibilidad
        path = CarteleriaService._get_live_scan_path()
        for attempt in range(2):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False)
                break
            except Exception:
                time.sleep(0.05)
        return True