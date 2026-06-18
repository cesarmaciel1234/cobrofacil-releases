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
        self.current_theme = "light" # FORZAR MODO CLARO SIEMPRE

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
                "nav_bg": "rgba(255, 255, 255, 0.85)",
                "nav_border": "#E5E5EA",
                "nav_brand": "#1D1D1F",
                "nav_text": "#86868B",
                "app_bg": "#F5F5F7",
                "text_title": "#1D1D1F",
                "text_desc": "#86868B",
                "btn_bg": "#FFFFFF",
                "btn_text": "#007AFF",
                "btn_border": "#E5E5EA",
                "btn_hover": "#F2F2F7",
                "footer": "#86868B",
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
        bg      = self.get_color("app_bg")
        fg      = self.get_color("text_title")
        fg2     = self.get_color("text_desc")
        btn     = self.get_color("btn_bg")
        btn_txt = self.get_color("btn_text")
        brd     = self.get_color("btn_border")
        nav     = self.get_color("nav_bg")

        # Inputs: blanco/negro en light — oscuro/claro en dark
        inp_bg = "#FFFFFF" if self.current_theme == "light" else "#1E293B"
        inp_fg = "#0F172A" if self.current_theme == "light" else "#F1F5F9"
        tbl_bg = "#FFFFFF" if self.current_theme == "light" else "#0F172A"
        tbl_fg = "#0F172A" if self.current_theme == "light" else "#F1F5F9"
        hdr_bg = "#F1F5F9" if self.current_theme == "light" else "#1E293B"

        widget.setStyleSheet(f"""
            QWidget                     {{ background-color: {bg}; color: {fg}; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
            QFrame                      {{ background: transparent; border: none; color: {fg}; }}
            QFrame#card                 {{ background: {btn}; border: 1px solid {brd}; border-radius: 8px; }}
            QLabel                      {{ background: transparent; color: {fg}; border: none; }}
            QPushButton                 {{ background-color: {btn}; color: {btn_txt}; border: 1px solid {brd}; border-radius: 6px; padding: 8px 14px; font-weight: bold; }}
            QPushButton:hover           {{ background-color: {brd}; }}
            QPushButton:pressed         {{ background-color: {fg2}; color: {btn}; }}
            QPushButton:disabled        {{ color: {brd}; background-color: {bg}; }}
            QLineEdit                   {{ background-color: {inp_bg}; color: {inp_fg}; border: 1px solid {brd}; border-radius: 6px; padding: 6px; }}
            QTextEdit                   {{ background-color: {inp_bg}; color: {inp_fg}; border: 1px solid {brd}; border-radius: 6px; padding: 6px; }}
            QPlainTextEdit              {{ background-color: {inp_bg}; color: {inp_fg}; border: 1px solid {brd}; border-radius: 6px; padding: 6px; }}
            QComboBox                   {{ background-color: {inp_bg}; color: {inp_fg}; border: 1px solid {brd}; border-radius: 6px; padding: 6px; }}
            QComboBox QAbstractItemView {{ background-color: {inp_bg}; color: {inp_fg}; selection-background-color: {brd}; }}
            QSpinBox, QDoubleSpinBox    {{ background-color: {inp_bg}; color: {inp_fg}; border: 1px solid {brd}; border-radius: 6px; padding: 6px; }}
            QTableWidget                {{ background-color: {tbl_bg}; color: {tbl_fg}; border: 1px solid {brd}; border-radius: 8px; gridline-color: {brd}; }}
            QTableWidget QTableCornerButton::section {{ background: {hdr_bg}; }}
            QTableWidget::item:selected {{ background-color: {brd}; color: {fg}; }}
            QTreeWidget                 {{ background-color: {tbl_bg}; color: {tbl_fg}; border: 1px solid {brd}; border-radius: 8px; }}
            QListWidget                 {{ background-color: {tbl_bg}; color: {tbl_fg}; border: 1px solid {brd}; border-radius: 8px; }}
            QListWidget::item:selected  {{ background-color: {brd}; color: {fg}; }}
            QHeaderView::section        {{ background-color: {hdr_bg}; color: {fg}; font-weight: bold; border: none; border-bottom: 2px solid {brd}; padding: 8px; }}
            QTabWidget::pane            {{ background: {bg}; border: 1px solid {brd}; border-radius: 8px; }}
            QTabBar::tab                {{ background: {btn}; color: {fg}; border: 1px solid {brd}; border-bottom: none; border-radius: 6px 6px 0 0; padding: 8px 18px; margin-right: 2px; }}
            QTabBar::tab:selected       {{ background: {bg}; color: {fg}; font-weight: bold; }}
            QTabBar::tab:hover          {{ background: {brd}; }}
            QGroupBox                   {{ color: {fg}; border: 1px solid {brd}; border-radius: 8px; margin-top: 12px; padding-top: 8px; }}
            QGroupBox::title            {{ color: {fg}; subcontrol-origin: margin; left: 12px; padding: 0 4px; font-weight: bold; }}
            QCheckBox                   {{ color: {fg}; background: transparent; spacing: 6px; }}
            QCheckBox::indicator        {{ width: 16px; height: 16px; border: 1px solid {brd}; border-radius: 3px; background: {inp_bg}; }}
            QCheckBox::indicator:checked {{ background: #3B82F6; border-color: #3B82F6; }}
            QRadioButton                {{ color: {fg}; background: transparent; spacing: 6px; }}
            QScrollBar:vertical         {{ background: transparent; width: 8px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {brd}; border-radius: 4px; min-height: 30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal       {{ background: transparent; height: 8px; margin: 0; }}
            QScrollBar::handle:horizontal {{ background: {brd}; border-radius: 4px; min-width: 30px; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
            QToolTip                    {{ background: {nav}; color: {fg}; border: 1px solid {brd}; border-radius: 4px; padding: 4px 8px; }}
            QSplitter::handle           {{ background: {brd}; }}
            QStatusBar                  {{ background: {btn}; color: {fg2}; }}
        """)

# Instancia global
theme_manager = ThemeManager()
