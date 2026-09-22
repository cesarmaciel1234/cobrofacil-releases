import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

class CyberFeedItem(QFrame):
    def __init__(self, pc, fecha, tipo, usuario, obs, is_dark=False):
        super().__init__()

        icon = "\U0001F539"
        color = "#38BDF8"
        if "SEGURIDAD" in tipo.upper() or "ALERTA" in tipo.upper() or "CRITICO" in obs.upper():
            icon = "\U0001F6A8"
            color = "#EF4444"
        elif "INTERVENCION" in tipo.upper() or "INTERVENCIÓN" in tipo.upper():
            icon = "\U0001F511"
            color = "#F59E0B"
        elif "APERTURA" in tipo.upper():
            icon = "\U0001F4B0"
            color = "#8B5CF6"
        elif "CIERRE" in tipo.upper():
            icon = "\U0001F3C1"
            color = "#10B981"
        elif "VENTA" in tipo.upper():
            icon = "\U0001F4B5"
            color = "#10B981"

        bg_color = "#1E293B" if is_dark else "#FFFFFF"
        hover_color = "#283548" if is_dark else "#F8FAFC"
        border_color = "#0F172A" if is_dark else "#E2E8F0"
        hover_border = "#334155" if is_dark else "#CBD5E1"
        text_desc = "#94A3B8" if is_dark else "#64748B"
        pill_bg = "#0F172A" if is_dark else "#F1F5F9"
        pill_text = "#94A3B8" if is_dark else "#475569"

        self.setStyleSheet(f"""
            CyberFeedItem {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-left: 4px solid {color};
                border-radius: 6px;
                margin-bottom: 4px;
            }}
            CyberFeedItem:hover {{
                background-color: {hover_color};
                border: 1px solid {hover_border};
                border-left: 6px solid {color};
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)

        t_lay = QHBoxLayout()
        t_lay.setContentsMargins(0,0,0,0)

        lbl_title = QLabel(f"<b><span style='color: {color}; font-size: 13px;'>{icon} [{pc}] {tipo}</span></b>")
        lbl_title.setTextFormat(Qt.TextFormat.RichText)

        try: time_str = str(fecha)[5:16]
        except: time_str = str(fecha)

        lbl_time = QLabel(f"<span style='background-color: {pill_bg}; color: {pill_text}; font-size: 10px; padding: 2px 6px; border-radius: 4px;'>&nbsp;{time_str}&nbsp;</span>")
        lbl_time.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        t_lay.addWidget(lbl_title)
        t_lay.addStretch()
        t_lay.addWidget(lbl_time)

        lbl_desc = QLabel(f"<span style='color: {text_desc}; font-size: 11px; font-style: italic;'><b>Usuario:</b> {usuario} &nbsp;//&nbsp; <b>Detalle:</b> {obs}</span>")
        lbl_desc.setWordWrap(True)
        lbl_desc.setTextFormat(Qt.TextFormat.RichText)
        lbl_desc.setContentsMargins(22, 0, 0, 0)

        lay.addLayout(t_lay)
        lay.addWidget(lbl_desc)
