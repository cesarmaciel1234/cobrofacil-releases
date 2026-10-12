"""Perfil de la TV: eco (PC floja) o max (alta gama). El look premium no cambia."""

import ctypes
import logging
import os
import platform

logger = logging.getLogger("PerfilPcTv")

# Cache del perfil para no recalcular
_perfil_cache = None


def _ram_gb():
    if platform.system() != "Windows":
        logger.debug("No es Windows, usando default 8GB RAM")
        return 8.0
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        st = MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            logger.warning("No se pudo obtener RAM, usando default 8GB")
            return 8.0
        ram_gb = st.ullTotalPhys / (1024 ** 3)
        logger.debug(f"RAM detectada: {ram_gb:.1f} GB")
        return ram_gb
    except Exception as e:
        logger.warning(f"Error detectando RAM: {e}, usando default 8GB")
        return 8.0


def detectar_perfil():
    ram = _ram_gb()
    cpu = os.cpu_count() or 2
    if ram < 6.5 or cpu < 4:
        perfil = "eco"
        logger.info("Perfil eco: RAM baja (%.1f GB < 6.5) o CPU baja (%s < 4 núcleos)", ram, cpu)
    elif ram >= 12 and cpu >= 6:
        perfil = "max"
        logger.info("Perfil max: RAM alta (%.1f GB >= 12) y CPU alta (%s >= 6 núcleos)", ram, cpu)
    else:
        perfil = "eco" if ram < 8 else "max"
        logger.info("Perfil %s: RAM media (%.1f GB, %s núcleos)", perfil, ram, cpu)
    return perfil


def perfil_activo():
    global _perfil_cache
    if _perfil_cache is not None:
        return _perfil_cache

    try:
        from src.config import config

        elegido = str(config.get("carteleria_perf") or "auto").strip().lower()
    except Exception as e:
        logger.warning(f"Error leyendo config de perfil: {e}, usando auto")
        elegido = "auto"
    if elegido in ("eco", "bajo", "low"):
        logger.info("Perfil configurado manualmente: eco")
        _perfil_cache = "eco"
        return "eco"
    if elegido in ("max", "alto", "high"):
        logger.info("Perfil configurado manualmente: max")
        _perfil_cache = "max"
        return "max"
    if elegido != "auto":
        logger.warning(f"Perfil desconocido '{elegido}', usando auto-detección")
    perfil = detectar_perfil()
    _perfil_cache = perfil
    return perfil


def limpiar_cache_perfil():
    """Limpia el cache del perfil cuando cambia la configuración."""
    global _perfil_cache
    _perfil_cache = None
    logger.debug("Cache de perfil limpiado")


def flags_chrome_perfil(perfil):
    if perfil == "eco":
        return [
            "--disable-smooth-scrolling",
            "--num-raster-threads=2",
            "--disable-background-networking",
        ]
    return [
        "--enable-gpu-rasterization",
        "--enable-zero-copy",
        "--ignore-gpu-blocklist",
    ]
