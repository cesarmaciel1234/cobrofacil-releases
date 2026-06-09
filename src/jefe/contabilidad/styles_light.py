"""
styles_light.py — Tema claro profesional para PUNPRO ERP (Perfil Jefe)
Estándar empresarial: fondo blanco, textos oscuros, acentos color verde/violeta.
"""

STYLE_SHEET = """
QMainWindow, QWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: 'Segoe UI', 'Inter', Roboto, Helvetica, Arial, sans-serif;
    font-size: 14px;
}

/* ── Sidebar ───────────────────────────────────────────── */
QFrame#Sidebar {
    background: #f1f5f9;
    border-right: 1px solid #e2e8f0;
}

QListWidget {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 10px 14px;
    color: #475569;
    font-size: 12px;
    font-weight: 600;
    border-radius: 8px;
    margin: 1px 0;
}
QListWidget::item:selected {
    background: #6366f1;
    color: #ffffff;
}
QListWidget::item:hover:!selected {
    background: #e2e8f0;
    color: #0f172a;
}
QScrollBar:vertical {
    width: 4px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 2px;
}

/* ── Header ────────────────────────────────────────────── */
QFrame#Header {
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}

/* ── Cards ─────────────────────────────────────────────── */
QFrame#Card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
}

QFrame#StatCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #ffffff, stop:1 #f8fafc);
    border: 1px solid #e2e8f0;
    border-radius: 20px;
}

QFrame#StatCard:hover {
    border: 1px solid #6366f1;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #eef2ff, stop:1 #f8fafc);
}

/* ── Labels ────────────────────────────────────────────── */
QLabel#StatLabel {
    color: #64748b;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
}

QLabel#StatValue {
    font-size: 30px;
    font-weight: 900;
    color: #0f172a;
    letter-spacing: -1px;
}

/* ── Inputs ────────────────────────────────────────────── */
QLineEdit, QComboBox, QTextEdit, QDateEdit, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 14px;
    color: #0f172a;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
    border: 2px solid #6366f1;
    background-color: #fafafa;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
    border-radius: 8px;
}

/* ── Buttons ───────────────────────────────────────────── */
QPushButton {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #4f46e5;
}

QPushButton:pressed {
    background-color: #4338ca;
}

QPushButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
}

/* ── Table ─────────────────────────────────────────────── */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    gridline-color: #f1f5f9;
    selection-background-color: #eef2ff;
    selection-color: #0f172a;
    alternate-background-color: #f8fafc;
}

QTableWidget::item {
    padding: 8px 12px;
    color: #1e293b;
    border: none;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #6366f1;
    padding: 12px 16px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    font-weight: 900;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* ── Tabs ──────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background: transparent;
}

QTabBar::tab {
    background: #f1f5f9;
    padding: 10px 24px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    color: #64748b;
    font-weight: 600;
    font-size: 12px;
}

QTabBar::tab:selected {
    background: #6366f1;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background: #e2e8f0;
    color: #0f172a;
}

/* ── ProgressBar ───────────────────────────────────────── */
QProgressBar {
    background-color: #f1f5f9;
    border: none;
    border-radius: 8px;
    text-align: center;
    color: #0f172a;
    font-weight: 700;
    font-size: 11px;
    height: 12px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #10b981, stop:1 #34d399);
    border-radius: 8px;
}

/* ── ScrollArea ────────────────────────────────────────── */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #f1f5f9;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }

/* ── StatusBar ─────────────────────────────────────────── */
QStatusBar {
    background: #f1f5f9;
    border-top: 1px solid #e2e8f0;
    color: #475569;
    font-size: 11px;
}

/* ── MessageBox ────────────────────────────────────────── */
QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #0f172a;
    font-size: 13px;
}
"""
