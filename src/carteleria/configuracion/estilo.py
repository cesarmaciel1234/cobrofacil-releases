QSS_PANEL = "QWidget#CarteleriaConfigPanel { background: #F8FAFC; }"
QSS_HEADER = (
    "QFrame { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; border-radius: 0px; }"
)
QSS_BTN_VOLVER = """
QPushButton {
    background: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1;
    border-radius: 8px; padding: 10px 20px; font-size: 14px;
}
QPushButton:hover { background: #F1F5F9; border-color: #94A3B8; }
"""
QSS_TITULO_PANTALLA = "color: #1E293B; border: none;"
QSS_FONDO = "background: #F8FAFC;"
QSS_TARJETA = (
    "QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; }"
)
QSS_SECCION = "color: #3B82F6; border: none; margin-bottom: 10px; font-size: 20px;"
QSS_ROTULO_CAMPO = "color: #64748B; border: none; margin-bottom: 6px; font-size: 14px;"
QSS_LISTA_TEMAS = """
QListWidget#ListaTemasTv {
    background: #FFFFFF; color: #1E293B; border: 1px solid #0F172A;
    border-radius: 4px; font-size: 15px; padding: 4px;
}
QListWidget#ListaTemasTv::item { padding: 10px 8px; border-bottom: 1px solid #E2E8F0; }
QListWidget#ListaTemasTv::item:selected { background: #DBEAFE; color: #1E293B; }
"""
QSS_COMBO = """
QComboBox {
    padding: 12px 16px; border: 2px solid #CBD5E1; border-radius: 8px;
    font-size: 15px; background: #FFFFFF; color: #1E293B;
}
QComboBox:hover { border-color: #94A3B8; background: #F8FAFC; }
"""
QSS_TEXTO = """
QTextEdit {
    padding: 12px 16px; border: 2px solid #CBD5E1; border-radius: 8px;
    font-size: 14px; background: #FFFFFF; color: #1E293B;
}
QTextEdit:focus { border-color: #3B82F6; background: #F8FAFC; }
"""
QSS_GUARDAR = """
QPushButton {
    background: #2563EB; color: white; padding: 12px 24px;
    border-radius: 6px; border: none; font-size: 15px;
}
QPushButton:hover { background: #1D4ED8; }
QPushButton:pressed { background: #1E40AF; }
QPushButton:disabled { background: #94A3B8; }
"""
QSS_SCROLL = """
QScrollArea { border: none; background: #F8FAFC; }
QScrollBar:vertical { background: #E2E8F0; width: 12px; border-radius: 6px; }
QScrollBar::handle:vertical { background: #94A3B8; border-radius: 6px; min-height: 30px; }
"""
