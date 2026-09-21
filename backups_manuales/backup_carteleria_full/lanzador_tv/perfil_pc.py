"""Perfil de la TV: eco (PC floja) o max (alta gama). El look premium no cambia."""

import ctypes
import logging
import os
import platform

logger = logging.getLogger("PerfilPcTv")


def _ram_gb():
    if platform.system() != "Windows":
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
            return 8.0
        return st.ullTotalPhys / (1024 ** 3)
    except Exception:
        return 8.0


def detectar_perfil():
    ram = _ram_gb()
    cpu = os.cpu_count() or 2
    if ram < 6.5 or cpu < 4:
        perfil = "eco"
    elif ram >= 12 and cpu >= 6:
        perfil = "max"
    else:
        perfil = "eco" if ram < 8 else "max"
    logger.info("TV perfil %s (RAM %.1f GB, %s núcleos)", perfil, ram, cpu)
    return perfil


def perfil_activo():
    try:
        from src.config import config

        elegido = str(config.get("carteleria_perf") or "auto").strip().lower()
    except Exception:
        elegido = "auto"
    if elegido in ("eco", "bajo", "low"):
        return "eco"
    if elegido in ("max", "alto", "high"):
        return "max"
    return detectar_perfil()


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
