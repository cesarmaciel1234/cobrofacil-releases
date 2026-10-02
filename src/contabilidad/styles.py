STYLE_SHEET = """
QMainWindow {
    background-color: #050a18;
}

QWidget {
    color: #e2e8f0;
    font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 16px;
}

QTabWidget::pane {
    border: none;
    background: transparent;
}

QTabBar::tab {
    background: #111827;
    padding: 12px 30px;
    margin-right: 4px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    color: #94a3b8;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
    color: white;
}

QFrame#Card {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 20px;
}

QFrame#StatCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #111827, stop:1 #0f172a);
    border: 1px solid #1e293b;
    border-radius: 24px;
}

QFrame#StatCard:hover {
    border: 1px solid #6366f1;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1b4b, stop:1 #0f172a);
}

QLabel#StatLabel {
    color: #64748b;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

QLabel#StatValue {
    font-size: 34px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -1px;
}

QLineEdit, QComboBox, QTextEdit, QDateEdit, QSpinBox {
    background-color: #020617;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 12px 16px;
    color: #f9fafb;
}

QLineEdit:focus, QComboBox:focus {
    border: 2px solid #6366f1;
}

QPushButton {
    background-color: #6366f1;
    color: white;
    border-radius: 12px;
    padding: 14px 28px;
    font-weight: 700;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #4f46e5;
}

QTableWidget {
    background-color: transparent;
    border: none;
    gridline-color: #1e293b;
    selection-background-color: rgba(99, 102, 241, 0.1);
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #0f172a;
    color: #6366f1;
    padding: 16px;
    border: none;
    border-bottom: 2px solid #1e293b;
    font-weight: 900;
    font-size: 12px;
}

QProgressBar {
    background-color: #1e293b;
    border-radius: 10px;
    text-align: center;
    height: 12px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399);
    border-radius: 10px;
}
"""

