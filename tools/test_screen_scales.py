"""Simula escalado de UI en 14", 19", 24" y 32" — ejecutar: python tools/test_screen_scales.py"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.qt_dpi import (
    compute_layout_scale,
    compute_profile_selector_size,
    scale_px,
    screen_info,
    configure_process_dpi,
    configure_qt_application_attributes,
)

CASES = [
    ("14p laptop FHD 100%", 14, 1920, 1080),
    ("14p laptop Win 150%", 14, 1280, 720),
    ("14p laptop Win 200%", 14, 960, 504),
    ("14p laptop HD", 14, 1366, 768),
    ("19p monitor", 19, 1440, 900),
    ("19p 1280x1024", 19, 1280, 1024),
    ("24p POS Full HD", 24, 1920, 1080),
    ("24p POS 1366", 24, 1366, 768),
    ("32p 2K", 32, 2560, 1440),
    ("32p FHD", 32, 1920, 1080),
]


def main():
    print("=" * 90)
    hdr = f"{'ESCENARIO':<24} {'RES':>11} {'PULG':>5} {'SCALE':>6} {'PERFIL':>12} {'TARJETA':>10} {'TOTAL':>6} {'F-KEY':>6}"
    print(hdr)
    print("=" * 90)

    for name, diag, w, h in CASES:
        ls = compute_layout_scale(w, h, diag)
        dlg_w, dlg_h, cw, ch = compute_profile_selector_size(w, h, diag)
        total_px = scale_px(75, ls)
        fkey = scale_px(45, ls)
        res = f"{w}x{h}"
        perfil = f"{dlg_w}x{dlg_h}"
        tarjeta = f"{cw}x{ch}"
        print(
            f"{name:<24} {res:>11} {diag:>4}\" {ls:>5.2f} {perfil:>12} {tarjeta:>10} "
            f"{total_px:>5}px {fkey:>5}px"
        )

    print("=" * 90)
    print()
    print("--- PANTALLA REAL (Qt) ---")
    configure_process_dpi()
    configure_qt_application_attributes()
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    info = screen_info(app)
    ls = info["layout_scale"]
    dlg_w, dlg_h, cw, ch = compute_profile_selector_size(
        info["width"], info["height"], info.get("diagonal_in")
    )
    print(f"Detectado: {info['label']}")
    print(
        f"Perfil: {dlg_w}x{dlg_h}  Tarjetas: {cw}x{ch}  "
        f"Total cajero: {scale_px(75, ls)}px  F-keys: {scale_px(45, ls)}px"
    )


if __name__ == "__main__":
    main()
