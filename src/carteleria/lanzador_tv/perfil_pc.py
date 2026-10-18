"""TV Chromium: el motor pinta en GPU (D3D11). Sin zero-copy y sin Vulkan."""

import ctypes
import logging
import platform

logger = logging.getLogger("PerfilPcTv")

_perfil_cache = None


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
    return "max"


def perfil_activo():
    global _perfil_cache
    if _perfil_cache is not None:
        return _perfil_cache
    _perfil_cache = "max"
    logger.info("TV Chromium: premium estable")
    return _perfil_cache


def limpiar_cache_perfil():
    global _perfil_cache
    _perfil_cache = None


def flags_chrome_perfil(perfil=None):
    """Motor Chromium al máximo estable.

    Prendido (lo que el motor ya trae):
    - ANGLE D3D11: el compositor de Windows.
    - Raster en GPU y raster fuera del hilo de la página.
    - Canvas 2D acelerado.
    - Color sRGB, para que el televisor no corra los precios.
    - Letras en gris: con zoom los subpíxeles no coinciden y se ven colores.

    Apagado a propósito:
    - zero-copy (en Intel se congelaba la ventana).
    - Vulkan y más de 2 hilos de raster.
    - Traductor, sync y red de fondo: no aportan a la cara.
    """
    del perfil
    return [
        "--use-angle=d3d11",
        "--enable-gpu-rasterization",
        "--enable-oop-rasterization",
        "--enable-accelerated-2d-canvas",
        "--ignore-gpu-blocklist",
        "--num-raster-threads=2",
        "--disable-lcd-text",
        "--force-color-profile=srgb",
        "--disable-background-networking",
        "--disable-sync",
        "--disable-features=Translate,MediaRouter,OptimizationHints,BackForwardCache,InfiniteSessionRestore",
    ]
