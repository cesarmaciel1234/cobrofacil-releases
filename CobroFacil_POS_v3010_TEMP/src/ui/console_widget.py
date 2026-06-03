# src/ui/console_widget.py

"""Console widget that shows live installer messages and a progress bar.
It is a lightweight, dark‑theme widget suitable for embedding at the bottom
of the main window.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QProgressBar
from PyQt5.QtCore import Qt


class ConsoleWidget(QWidget):
    """Widget with a read‑only console area and a progress bar.

    Usage:
        console = ConsoleWidget(parent)
        console.append_message("Instalando...")
        console.update_progress(25, "Paso 1")
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(180)  # keep it compact
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        # Console area
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            "background-color: #0f172a; color: #34d399; font-family: Consolas, Monospace; font-size: 12px;"
        )
        layout.addWidget(self.text_edit)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(
            "QProgressBar {background-color: #1e293b; color: #fff; border: 1px solid #334155; height: 14px; border-radius: 4px;}"
            "QProgressBar::chunk {background-color: #34d399; border-radius: 3px;}"
        )
        layout.addWidget(self.progress_bar)

    def append_message(self, msg: str):
        """Add a new line to the console area and ensure the view stays at the bottom."""
        self.text_edit.appendPlainText(msg)
        # Auto‑scroll to the bottom
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

    def update_progress(self, percent: int, msg: str):
        """Update the progress bar and optionally add a message to the console."""
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(f"{percent}% – {msg}")
        self.append_message(msg)

