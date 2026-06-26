"""
Escalado de pantalla — Cobro Fácil POS.

Diseño de referencia: monitor POS ~24" @ 1920×1080.
Laptops 14" con la misma resolución necesitan layout más compacto.

Reglas:
- Se apaga el auto-escalado de Windows/Qt para evitar doble escalado.
- NO usar SetProcessDpiAwareness (provoca doble escalado con Qt).
- layout_scale() achica UI en pantallas físicamente chicas (<17").
- Soporte Multi-Monitor integrado para Pantalla de Cajero y Pantalla de Cliente.
"""

from __future__ import annotations

import os

REF_WIDTH = 1920
REF_HEIGHT = 1080
REF_DIAGONAL_IN = 24.0  # monitor POS de caja
LAPTOP_MAX_IN = 16.5    # por debajo → modo compacto

PROFILE_CARD_GAP = 20
PROFILE_CARD_COUNT = 4
PROFILE_CARD_W_MAX = 230
PROFILE_CARD_W_MIN = 140

# Terminal cajero @ 1920×1080 (monitor POS 24")
TERMINAL_HEADER_H = 130
TERMINAL_DASHBOARD_H = 230
TERMINAL_STATUS_H = 68
TERMINAL_STATUS_CTRL_H = 46
TERMINAL_STATUS_ICON_H = 44
TERMINAL_SHORTCUTS_H = 50
TERMINAL_SCAN_MIN_H = 80
TERMINAL_SCAN_FONT = 24
TERMINAL_TOTAL_FONT = 75
TERMINAL_TITLE_FONT = 26
TERMINAL_SIDE_FONT = 17
TERMINAL_TABLE_ROW = 40
TERMINAL_MAIN_MARGIN = 10
TERMINAL_CENTRAL_STRETCH = 2


def configure_process_dpi() -> None:
    # Apaga el auto-escalado de Windows para que Qt no herede el zoom del sistema (125%, 150%)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    
    scale_factor = 1.0
    try:
        import ctypes
        hdc = ctypes.windll.user32.GetDC(0)
        width_px = ctypes.windll.user32.GetSystemMetrics(0)
        height_px = ctypes.windll.user32.GetSystemMetrics(1)
        width_mm = ctypes.windll.gdi32.GetDeviceCaps(hdc, 4)
        height_mm = ctypes.windll.gdi32.GetDeviceCaps(hdc, 6)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        
        diag_in = ((width_mm**2 + height_mm**2)**0.5) / 25.4
        
        # En caso de que se necesite, un pequeño bump para que no sea excesivamente diminuto
        # pero que permita encajar en pantallas chicas
        scale_factor = compute_layout_scale(width_px, height_px, diag_in)
        # Limitar el scale_factor a un mínimo razonable para no achicar demasiado
        scale_factor = max(0.70, scale_factor)
    except Exception:
        pass

    # Fuerza la escala base, aplicando el factor de achique global para laptops
    os.environ["QT_SCALE_FACTOR"] = str(scale_factor)
    os.environ.pop("QT_SCREEN_SCALE_FACTORS", None)


def configure_qt_application_attributes() -> None:
    from src.utils.qt_compat import configure_qt_application_attributes as _configure

    _configure()


# --- UTILIDADES DE PANTALLA ---

def primary_screen(app=None):
    from PyQt6.QtWidgets import QApplication
    app = app or QApplication.instance()
    return app.primaryScreen() if app else None


def _resolve_screen_app(screen=None, app=None):
    """Si llaman foo(app) por posición, no confundir QApplication con QScreen."""
    from PyQt6.QtWidgets import QApplication

    if screen is not None and app is None and isinstance(screen, QApplication):
        app = screen
        screen = None
    if screen is None:
        screen = primary_screen(app)
    return screen, app


def secondary_screen(app=None):
    from PyQt6.QtWidgets import QApplication
    app = app or QApplication.instance()
    if app and len(app.screens()) > 1:
        return app.screens()[1]
    return None


def screen_geometry(screen=None, app=None):
    screen, app = _resolve_screen_app(screen, app)
    return screen.availableGeometry() if screen else None


def physical_diagonal_inches(screen) -> float | None:
    if screen is None:
        return None
    try:
        ps = screen.physicalSize()
        if ps.width() < 10 or ps.height() < 10:
            return None
        diag_mm = (ps.width() ** 2 + ps.height() ** 2) ** 0.5
        return diag_mm / 25.4
    except Exception:
        return None


# --- LÓGICA MATEMÁTICA PURA ---

def compute_layout_scale(width: int, height: int, diagonal_in: float | None = None) -> float:
    """Cálculo puro de escala (útil para pruebas y simulación)."""
    factors: list[float] = []
    if diagonal_in is not None:
        if diagonal_in <= LAPTOP_MAX_IN:
            factors.append(max(0.62, min(1.0, diagonal_in / REF_DIAGONAL_IN)))
        else:
            factors.append(min(1.0, diagonal_in / REF_DIAGONAL_IN))
    factors.append(max(0.68, min(1.0, width / REF_WIDTH)))
    factors.append(max(0.68, min(1.0, height / REF_HEIGHT)))
    return round(min(factors), 2)


def compute_profile_selector_size(
    width: int, height: int, diagonal_in: float | None = None,
) -> tuple[int, int, int, int]:
    """Tamaño del diálogo de perfiles — tarjetas por ancho útil, sin achicar por layout_scale."""
    outer_margin = 12
    dlg_w = min(width - outer_margin * 2, max(860, int(width * 0.97)))
    dlg_h = min(height - outer_margin * 2, max(480, int(height * 0.90)))

    root_margin = 40
    content_margin = 80
    gaps = PROFILE_CARD_GAP * (PROFILE_CARD_COUNT - 1)
    cards_row_w = dlg_w - root_margin - content_margin
    card_w = min(
        PROFILE_CARD_W_MAX,
        max(PROFILE_CARD_W_MIN, (cards_row_w - gaps) // PROFILE_CARD_COUNT),
    )
    card_h = max(158, int(card_w * 215 / PROFILE_CARD_W_MAX))

    need_h = card_h + 270 + root_margin
    dlg_h = min(max(need_h, dlg_h), height - outer_margin * 2)
    return dlg_w, dlg_h, card_w, card_h


# --- FUNCIONES DE ADAPTACIÓN (SOPORTAN MULTI-MONITOR) ---

def layout_scale(screen=None, app=None) -> float:
    """
    Calcula la escala para una pantalla específica (por defecto, la principal).
    1.0 = monitor POS 24"+. ~0.65–0.85 en laptop 14".
    """
    screen, app = _resolve_screen_app(screen, app)
    geo = screen_geometry(screen, app)
    if geo is None:
        return 1.0
    return compute_layout_scale(
        geo.width(), geo.height(), physical_diagonal_inches(screen)
    )


def scale_px(value: int, factor: float | None = None, screen=None, app=None) -> int:
    if factor is None:
        factor = layout_scale(screen, app)
    return max(1, int(round(value * factor)))


def scaled_size(width: int, height: int, screen=None, app=None) -> tuple[int, int]:
    """Compatibilidad con ventanas que usan tamaño de diseño escalado."""
    ls = layout_scale(screen, app)
    return scale_px(width, ls), scale_px(height, ls)


def screen_info(screen=None, app=None) -> dict:
    screen, app = _resolve_screen_app(screen, app)
    geo = screen_geometry(screen, app)
    ls = layout_scale(screen, app)
    diag = physical_diagonal_inches(screen)
    
    if geo is None:
        return {
            "width": REF_WIDTH,
            "height": REF_HEIGHT,
            "layout_scale": ls,
            "diagonal_in": diag,
            "label": f"default layout {ls}x",
        }
    diag_txt = f"{diag:.1f}\"" if diag else "?"
    return {
        "width": geo.width(),
        "height": geo.height(),
        "layout_scale": ls,
        "diagonal_in": diag,
        "label": f"{geo.width()}x{geo.height()} {diag_txt} layout {ls}x",
    }


def terminal_layout_metrics(screen=None, app=None) -> dict:
    """
    Dimensiones del terminal de caja escaladas al monitor real.
    Referencia: POS 24\" @ 1920×1080 con panel inferior amplio y barra superior alta.
    """
    ls = layout_scale(screen, app)
    geo = screen_geometry(screen, app)
    screen_h = geo.height() if geo else REF_HEIGHT

    dash_base = TERMINAL_DASHBOARD_H
    header_base = TERMINAL_HEADER_H
    if screen_h < 768:
        dash_base, header_base = 170, 95
    elif screen_h < 900:
        dash_base, header_base = 200, 110

    font_scale = max(0.85, ls)
    return {
        "layout_scale": ls,
        "screen_width": geo.width() if geo else REF_WIDTH,
        "screen_height": screen_h,
        "header_height": scale_px(header_base, ls),
        "dashboard_height": scale_px(dash_base, ls),
        "status_height": scale_px(TERMINAL_STATUS_H, ls),
        "status_control_height": scale_px(TERMINAL_STATUS_CTRL_H, ls),
        "status_icon_size": scale_px(TERMINAL_STATUS_ICON_H, ls),
        "shortcuts_height": scale_px(TERMINAL_SHORTCUTS_H, ls),
        "scan_min_height": scale_px(TERMINAL_SCAN_MIN_H, ls),
        "scan_font": max(18, int(TERMINAL_SCAN_FONT * font_scale)),
        "total_font": max(42, int(TERMINAL_TOTAL_FONT * font_scale)),
        "title_font": max(18, int(TERMINAL_TITLE_FONT * font_scale)),
        "side_font": max(12, int(TERMINAL_SIDE_FONT * font_scale)),
        "table_row": max(32, scale_px(TERMINAL_TABLE_ROW, ls)),
        "main_margin": scale_px(TERMINAL_MAIN_MARGIN, ls),
        "central_stretch": TERMINAL_CENTRAL_STRETCH,
        "list_results_h": scale_px(350, ls),
        "list_results_w": min(900, scale_px(900, ls)),
    }


def profile_selector_size(screen=None, app=None) -> tuple[int, int, int, int]:
    screen, app = _resolve_screen_app(screen, app)
    geo = screen_geometry(screen, app)
    
    if geo is None:
        return 1100, 500, PROFILE_CARD_W_MAX, 215

    return compute_profile_selector_size(
        geo.width(), 
        geo.height(), 
        physical_diagonal_inches(screen)
    )


# --- CONTROL DE VENTANAS ---

def center_on_screen(widget, screen=None, app=None) -> None:
    screen, app = _resolve_screen_app(screen, app)
    geo = screen_geometry(screen, app)
    if geo is None:
        return
    frame = widget.frameGeometry()
    frame.moveCenter(geo.center())
    widget.move(frame.topLeft())


def adapt_main_window(window, screen=None, app=None) -> None:
    screen, app = _resolve_screen_app(screen, app)
    geo = screen_geometry(screen, app)
    if geo is None:
        return
    ls = layout_scale(screen, app)
    min_w = max(scale_px(1024, ls), min(scale_px(1280, ls), geo.width()))
    min_h = max(scale_px(600, ls), min(scale_px(720, ls), geo.height()))
    window.setMinimumSize(min(min_w, geo.width()), min(min_h, geo.height()))


def present_main_window(window) -> None:
    """Muestra la ventana principal del cajero."""
    adapt_main_window(window)
    if window.isFullScreen() or getattr(window, "_kiosk_mode", False):
        window.showFullScreen()
    else:
        window.showMaximized()
    window.raise_()
    window.activateWindow()


def present_client_window(window, app=None) -> bool:
    """
    Busca un segundo monitor y envía la ventana del cliente allí.
    Devuelve True si encontró el monitor secundario, False si no hay.
    """
    sec_screen = secondary_screen(app)
    if sec_screen:
        geo = screen_geometry(sec_screen)
        if geo:
            # Movemos la ventana a la esquina superior izquierda del monitor 2
            window.move(geo.topLeft())
            
            # Aplicamos la escala correspondiente a ese monitor específico
            ls = layout_scale(sec_screen, app)
            min_w = max(scale_px(800, ls), min(scale_px(1024, ls), geo.width()))
            min_h = max(scale_px(600, ls), min(scale_px(720, ls), geo.height()))
            window.setMinimumSize(min(min_w, geo.width()), min(min_h, geo.height()))
            
            if getattr(window, "_kiosk_mode", False):
                window.showFullScreen()
            else:
                window.showMaximized()
            return True
    return False


def apply_app_screen_adaptation(app=None, screen=None) -> dict:
    screen, app = _resolve_screen_app(screen, app)
    info = screen_info(screen, app)
    try:
        from src.logger import logger
        logger.info(f"DPI/Pantalla: {info['label']}")
    except Exception:
        pass
    return info


def center_on_primary_screen(widget, app=None) -> None:
    """Alias: centra en el monitor principal."""
    center_on_screen(widget, app=app)