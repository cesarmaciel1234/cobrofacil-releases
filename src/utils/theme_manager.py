import json
import os
from PyQt5.QtCore import QObject, pyqtSignal

THEME_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "theme_prefs.json")

class ThemeManager(QObject):
    theme_changed = pyqtSignal(str) # "light" o "dark"

    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self._load_theme()

    def _load_theme(self):
        if os.path.exists(THEME_FILE):
            try:
                with open(THEME_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_theme = data.get("theme", "light")
            except Exception:
                pass

    def _load_prefs(self):
        # Modo oscuro deshabilitado globalmente en perfil admin
        pass

    def _save_theme(self):
        try:
            with open(THEME_FILE, "w", encoding="utf-8") as f:
                json.dump({"theme": self.current_theme}, f)
        except Exception:
            pass

    def toggle_theme(self):
        # Deshabilitado
        pass

    def set_theme(self, theme):
        if theme in ["light", "dark"]:
            self.current_theme = theme
            self._save_theme()
            self.theme_changed.emit(self.current_theme)

    def is_dark(self):
        return self.current_theme == "dark"

    def get_color(self, element):
        palettes = {
            "light": {
                "nav_bg": "#FFFFFF",
                "nav_border": "#E2E8F0",
                "nav_brand": "#0F172A",
                "nav_text": "#64748B",
                "app_bg": "#F4F6F8", # Gris-azulado muy sutil, estilo macOS
                "text_title": "#0F172A", # Azul medianoche
                "text_desc": "#64748B", # Gris pizarra
                "btn_bg": "#FFFFFF",
                "btn_text": "#334155",
                "btn_border": "#CBD5E1",
                "btn_hover": "#F8FAFC",
                "footer": "#94A3B8",
            },
            "dark": {
                "nav_bg": "#020617",
                "nav_border": "#1E293B",
                "nav_brand": "#F8FAFC",
                "nav_text": "#94A3B8",
                "app_bg": "#0B0E14",
                "text_title": "#F8FAFC",
                "text_desc": "#94A3B8",
                "btn_bg": "#1E293B",
                "btn_text": "#F8FAFC",
                "btn_border": "#334155",
                "btn_hover": "#334155",
                "footer": "#334155",
            }
        }
        return palettes[self.current_theme].get(element, "#FF00FF")

    def apply_to_admin(self, widget):
        bg = self.get_color("app_bg")
        fg = self.get_color("text_title")
        btn = self.get_color("btn_bg")
        btn_txt = self.get_color("btn_text")
        brd = self.get_color("btn_border")
        
        # Un stylesheet ultra-limpio 2026 que sobrescribe elementos genéricos
        widget.setStyleSheet(f"""
            QWidget {{ background-color: {bg}; color: {fg}; font-family: 'Segoe UI', sans-serif; }}
            QFrame {{ background: transparent; border: none; }}
            QFrame#card {{ background: {btn}; border: 1px solid {brd}; border-radius: 8px; }}
            QLabel {{ background: transparent; color: {fg}; border: none; }}
            QPushButton {{ background-color: {btn}; color: {btn_txt}; border: 1px solid {brd}; border-radius: 6px; padding: 8px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {brd}; }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ background-color: white; color: black; border: 1px solid {brd}; border-radius: 6px; padding: 6px; }}
            QTableWidget, QTreeWidget {{ background-color: white; color: black; border: 1px solid {brd}; border-radius: 8px; gridline-color: {brd}; }}
            QHeaderView::section {{ background-color: {btn}; color: {fg}; font-weight: bold; border: none; border-bottom: 2px solid {brd}; padding: 8px; }}
            QScrollBar:vertical {{ background: transparent; width: 8px; }}
            QScrollBar::handle:vertical {{ background: {brd}; border-radius: 4px; }}
        """)

# Instancia global
theme_manager = ThemeManager()
