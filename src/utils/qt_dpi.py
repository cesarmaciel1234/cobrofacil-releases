"""
Estándar global de pantalla — Cobro Fácil POS (modo blindado).

PASO 1 — Antes de importar QApplication:
  configure_process_dpi()  → escala fija 100 %, sin zoom de Windows

PASO 2 — Antes del primer QApplication():
  configure_qt_application_attributes()  → sin AA_EnableHighDpiScaling

PASO 3 — Ventanas:
  adapt_main_window() / scaled_dialog_size() / profile_selector_size()

PASO 4 — Mostrar:
  present_main_window()  → maximizado o pantalla completa (cajero)

El layout responsive del cajero (stretch, resizeEvent) compensa resoluciones
1024–1920 en píxeles lógicos 1:1.
"""

from __future__ import annotations

import os

REF_WIDTH = 1366
REF_HEIGHT = 768

PROFILE_CARD_GAP = 20
PROFILE_CARD_COUNT = 4
PROFILE_CARD_W_MAX = 230
PROFILE_CARD_W_MIN = 158


def configure_process_dpi() -> None:
    """Escudo anti-Windows: rechaza el zoom del SO y fija escala 1.0."""
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ.pop("QT_SCREEN_SCALE_FACTORS", None)


def configure_qt_application_attributes() -> None:
    """Sin HighDpiScaling: la app no escucha la escala de Windows."""
    pass


def _app_and_screen(app=None):
    from PyQt5.QtWidgets import QApplication

    app = app or QApplication.instance()
    if app is None:
        return app, None
    return app, app.primaryScreen()


def screen_geometry(app=None):
    _, screen = _app_and_screen(app)
    return screen.availableGeometry() if screen else None


def screen_info(app=None) -> dict:
    geo = screen_geometry(app)
    _, screen = _app_and_screen(app)
    if geo is None or screen is None:
        return {
            "width": REF_WIDTH,
            "height": REF_HEIGHT,
            "dpi_scale": 1.0,
            "device_pixel_ratio": 1.0,
            "label": "default 1.0x",
        }
    return {
        "width": geo.width(),
        "height": geo.height(),
        "dpi_scale": 1.0,
        "device_pixel_ratio": 1.0,
        "label": f"{geo.width()}x{geo.height()} escala 1.0x (blindado)",
    }


def scaled_dialog_size(
    design_width: int,
    design_height: int,
    margin: int = 32,
    app=None,
) -> tuple[int, int]:
    geo = screen_geometry(app)
    if geo is None:
        return design_width, design_height
    max_w = max(360, geo.width() - margin * 2)
    max_h = max(280, geo.height() - margin * 2)
    return min(design_width, max_w), min(design_height, max_h)


def profile_selector_size(app=None) -> tuple[int, int, int, int]:
    geo = screen_geometry(app)
    if geo is None:
        return 1100, 500, PROFILE_CARD_W_MAX, 215

    outer_margin = 12
    dlg_w = min(
        geo.width() - outer_margin * 2,
        max(920, int(geo.width() * 0.97)),
    )
    dlg_h = min(
        geo.height() - outer_margin * 2,
        max(480, int(geo.height() * 0.90)),
    )

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
    dlg_h = min(max(need_h, dlg_h), geo.height() - outer_margin * 2)
    return dlg_w, dlg_h, card_w, card_h


def center_on_primary_screen(widget, app=None) -> None:
    geo = screen_geometry(app)
    if geo is None:
        return
    frame = widget.frameGeometry()
    frame.moveCenter(geo.center())
    widget.move(frame.topLeft())


def adapt_main_window(window, app=None) -> None:
    geo = screen_geometry(app)
    if geo is None:
        return
    min_w = max(1024, min(1280, geo.width()))
    min_h = max(600, min(720, geo.height()))
    window.setMinimumSize(min(min_w, geo.width()), min(min_h, geo.height()))
    window.setGeometry(geo)


def present_main_window(window) -> None:
    if window.isFullScreen() or getattr(window, "_kiosk_mode", False):
        window.showFullScreen()
    else:
        window.showMaximized()
    window.raise_()
    window.activateWindow()


def apply_app_screen_adaptation(app=None) -> dict:
    info = screen_info(app)
    try:
        from src.logger import logger

        logger.info(f"DPI/Pantalla: {info['label']}")
    except Exception:
        pass
    return info
