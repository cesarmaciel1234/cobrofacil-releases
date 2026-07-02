STYLE = """
QWidget {
    font-family: 'Inter', 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
    font-size: 13px;
    background-color: #F8FAFC;
    color: #334155;
}
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F1F5F9, stop:1 #E2E8F0);
    border-bottom: 2px solid #CBD5E1;
    border-radius: 12px;
}
QLabel#titulo {
    color: #0F172A;
    background: transparent;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 1px;
}
QPushButton {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #F1F5F9;
    border-color: #94A3B8;
    color: #0F172A;
}
QPushButton#blue {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
}
QPushButton#blue:hover {
    background-color: #1D4ED8;
    color: #FFFFFF;
}
QPushButton#danger {
    background-color: #FFFFFF;
    color: #DC2626;
    border: 1px solid #FECACA;
}
QPushButton#danger:hover {
    background-color: #FEF2F2;
    color: #B91C1C;
    border: 1px solid #FCA5A5;
}
QPushButton#gray {
    background-color: #FFFFFF;
    color: #475569;
    border: 1px solid #E2E8F0;
}
QPushButton#gray:hover {
    background-color: #F1F5F9;
}
QLineEdit, QComboBox {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #3B82F6;
    background-color: #FFFFFF;
}
QTreeWidget, QTableWidget {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    gridline-color: #F1F5F9;
    selection-background-color: #EFF6FF;
    selection-color: #1D4ED8;
    border-radius: 12px;
    alternate-background-color: #F8FAFC;
}
QHeaderView::section {
    background-color: #F8FAFC;
    color: #64748B;
    font-weight: 800;
    padding: 15px 12px;
    border: none;
    border-bottom: 2px solid #E2E8F0;
    font-size: 11px;
    text-transform: uppercase;
}
QScrollBar:vertical {
    border: none;
    background: #F1F5F9;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""


# ── Diálogo Producto 2026 ──────────────────────────────────
