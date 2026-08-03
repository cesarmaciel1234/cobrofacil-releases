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
        """Busca PCs maestras: heartbeats + radar UDP PUNPRO_DISCOVER.

        Una entrada por IP. Retorna: [{'ip': '192.168.0.5', 'nombre': 'DESKTOP-XXX'}]
        """
        import json
        import time

        por_ip: dict[str, str] = {}
        engine = get_network_engine()
        mi_host = ""
        if engine:
            mi_origen = getattr(engine, "_origen", "") or ""
            mi_host = mi_origen.split("|")[0].lower() if mi_origen else ""

        # 1) Presencia por heartbeats (NetworkEngine)
        if engine and hasattr(engine, "_active_ips"):
            roles_ok = {"admin", "jefe", "maestra", "server", "cajero"}
            for origen, ip in engine._active_ips.items():
                if not ip:
                    continue
                partes = str(origen).split("|")
                nombre_host = partes[0] if partes else str(origen)
                rol = partes[1].lower() if len(partes) > 1 else ""
                if rol and rol not in roles_ok:
                    continue
                if not rol and "maestra" not in str(origen).lower():
                    continue
                if mi_host and nombre_host.lower() == mi_host:
                    continue
                if ip not in por_ip or rol in ("admin", "maestra"):
                    por_ip[ip] = nombre_host

        # 2) Radar UDP: responde el lanzador/maestro aunque no haya cajero
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1.2)
            sock.sendto(b"PUNPRO_DISCOVER", ("255.255.255.255", 37020))
            t_end = time.time() + 1.2
            while time.time() < t_end:
                try:
                    data, addr = sock.recvfrom(2048)
                    info = json.loads(data.decode("utf-8"))
                    if str(info.get("mode", "")).upper() != "MAESTRA":
                        continue
                    ip = info.get("server_ip") or addr[0]
                    hostname = str(info.get("hostname") or ip)
                    if mi_host and hostname.lower() == mi_host:
                        continue
                    # Preferir nombre del discovery si no había heartbeat
                    if ip not in por_ip:
                        por_ip[ip] = hostname
                except socket.timeout:
                    break
                except Exception:
                    break
            sock.close()
        except Exception as e:
            logger.debug(f"Discovery UDP maestras: {e}")

        return [{"ip": ip, "nombre": nombre} for ip, nombre in sorted(por_ip.items())]

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
