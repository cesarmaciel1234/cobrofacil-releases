def apply_global_premium_css(app):
    css = """
    QScrollBar:vertical {
        border: none;
        background: #F8FAFC;
        width: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical {
        background: #CBD5E1;
        min-height: 30px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical:hover {
        background: #94A3B8;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }
    QScrollBar:horizontal {
        border: none;
        background: #F8FAFC;
        height: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal {
        background: #CBD5E1;
        min-width: 30px;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #94A3B8;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        border: none;
        background: none;
    }
    """
    app.setStyleSheet(css)
