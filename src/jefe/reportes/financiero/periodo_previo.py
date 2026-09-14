"""Misma duración, inmediatamente antes (Hoy → ayer, no el año pasado)."""

from __future__ import annotations

import datetime


def rango_igual_anterior(start_str: str, end_str: str) -> tuple[str, str]:
    s = datetime.datetime.strptime(start_str[:19], "%Y-%m-%d %H:%M:%S")
    e = datetime.datetime.strptime(end_str[:19], "%Y-%m-%d %H:%M:%S")
    dur = e - s
    e_prev = s - datetime.timedelta(seconds=1)
    s_prev = e_prev - dur
    return (
        s_prev.strftime("%Y-%m-%d %H:%M:%S"),
        e_prev.strftime("%Y-%m-%d %H:%M:%S"),
    )
