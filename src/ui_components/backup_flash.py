"""Flash de cierre: ventana corta mientras se finaliza la copia del día.

El motor ya actualizó el backup_diario en segundo plano durante el día;
esta UI solo confirma el sello final (estilo enterprise).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication,
)

from src.utils.qt_compat import qt_exec


def mostrar_flash_backup_dia(parent=None, engine_type: str = "mariadb", host: str = "127.0.0.1") -> bool:
    """Muestra ventana 'Guardando copia…' y ejecuta finalizar_backup_del_dia."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Copia de seguridad")
    dlg.setFixedSize(440, 170)
    dlg.setWindowFlags(
        Qt.WindowType.Dialog
        | Qt.WindowType.CustomizeWindowHint
        | Qt.WindowType.WindowTitleHint
    )
    dlg.setStyleSheet(
        "QDialog { background: #F8FAFC; }"
        "QLabel { color: #0F172A; border: none; }"
    )

    lay = QVBoxLayout(dlg)
    lay.setContentsMargins(28, 24, 28, 24)
    lay.setSpacing(14)

    title = QLabel("Guardando copia de seguridad del día")
    title.setStyleSheet("font-size: 16px; font-weight: 800;")
    lay.addWidget(title)

    subtitle = QLabel(
        "El motor ya respaldó en segundo plano durante el día.\n"
        "Finalizando el sello de cierre…"
    )
    subtitle.setWordWrap(True)
    subtitle.setStyleSheet("font-size: 12px; color: #475569;")
    lay.addWidget(subtitle)

    bar = QProgressBar()
    bar.setRange(0, 0)  # indeterminado
    bar.setTextVisible(False)
    bar.setFixedHeight(10)
    bar.setStyleSheet(
        "QProgressBar { background: #E2E8F0; border: none; border-radius: 5px; }"
        "QProgressBar::chunk { background: #2563EB; border-radius: 5px; }"
    )
    lay.addWidget(bar)

    result = {"ok": False}

    def _run():
        app = QApplication.instance()
        try:
            from src.base_de_datos.autoblindaje_db import AutoBlindajeDB
            if app:
                app.processEvents()
            # El cerebro ya trabajó todo el día; forzar un full final + sello
            try:
                from src.cerebro_global.backup_cerebro import cerebro_backup
                cerebro_backup.tick_now(force_full=True)
            except Exception:
                pass
            result["ok"] = bool(
                AutoBlindajeDB.finalizar_backup_del_dia(engine_type, host)
            )
            # Sello zip del diario externo (AppData), independiente del mysqldump
            try:
                from src.base_de_datos.diario_ventas_externo import sellar_dia

                sellar_dia()
            except Exception:
                pass
        except Exception:
            result["ok"] = False
        bar.setRange(0, 100)
        bar.setValue(100)
        if result["ok"]:
            subtitle.setText("Copia de seguridad del día lista.")
            title.setText("Respaldo completado")
        else:
            subtitle.setText(
                "No se pudo finalizar el sello. Revisá los logs; "
                "los respaldos periódicos del día pueden seguir disponibles."
            )
            title.setText("Respaldo con aviso")
        if app:
            app.processEvents()
        QTimer.singleShot(1100, dlg.accept)

    QTimer.singleShot(80, _run)
    qt_exec(dlg)
    return result["ok"]
