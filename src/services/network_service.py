"""
network_service.py - Servicio simple y limpio para manejar la red LAN, buscar PCs maestras y cambiar modos.
Nivel Medio: Encapsula el motor de red y base de datos para que la UI no acceda a sockets o configs crudas.
Nombres sencillos y comprensibles para que los entienda un niño.
"""

import socket
import re
import logging
from src.config import config
from src.central_red_global.network_engine import get_network_engine
from src.central_red_global.motor_red import MotorRed

logger = logging.getLogger(__name__)

class RedLanService:
    @staticmethod
    def obtener_estado_red() -> dict:
        """Devuelve un resumen simple del estado de la red actual."""
        motor = MotorRed()
        estado = motor.obtener_estado_red()
        
        # Obtener IP local de forma simple
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = "127.0.0.1"
            
        return {
            "es_maestra": estado["is_master"],
            "ip_local": local_ip,
            "ip_maestra_conectada": estado["db_host"],
            "caja_id": estado["caja_id"],
            "motor_datos": estado["db_engine"]
        }

    @staticmethod
    def buscar_computadoras_maestras() -> list[dict]:
        """Busca y devuelve una lista de PCs Maestras activas en la red local.
        Retorna: [{'ip': '192.168.0.5', 'nombre': 'DESKTOP-XXX'}]
        """
        engine = get_network_engine()
        maestras = []
        if engine and hasattr(engine, '_active_ips'):
            for origen, ip in engine._active_ips.items():
                origen_lower = origen.lower()
                # Filtrar PCs que actúan como servidor/maestra/admin
                if any(x in origen_lower for x in ("admin", "caja", "maestra", "server")):
                    nombre_host = origen.split('|')[0]
                    maestras.append({
                        "ip": ip,
                        "nombre": nombre_host
                    })
        return maestras

    @staticmethod
    def probar_conexion_a_ip(ip: str, puerto: int = 3306) -> bool:
        """Prueba si el puerto de datos está abierto en una dirección IP (retorna True o False)."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            resultado = s.connect_ex((ip, puerto))
            s.close()
            return resultado == 0
        except Exception:
            return False

    @staticmethod
    def cambiar_a_modo_maestra() -> tuple[bool, str]:
        """Configura esta computadora para trabajar como MAESTRA (servidor local)."""
        motor = MotorRed()
        return motor.convertir_en_maestra()

    @staticmethod
    def cambiar_a_modo_esclava(ip_maestra: str) -> tuple[bool, str]:
        """Configura esta computadora para trabajar como ESCLAVA de otra dirección IP."""
        # Limpiar la IP por si tiene texto extra o paréntesis
        if ip_maestra:
            match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', ip_maestra)
            if match:
                ip_maestra = match.group(0)
                
        motor = MotorRed()
        return motor.convertir_en_esclava(ip_maestra)
