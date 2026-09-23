ESTILO_BARRA = """
QFrame#PanelTotales {
    background: #FFFFFF;
    border-top: 1px solid #E2E8F0;
}
QLineEdit#TerminalScan {
    background: #F8FAFC;
    border: 2px solid #CBD5E1;
    border-radius: 12px;
    padding: 12px 18px;
    font-size: 26px;
    font-weight: 800;
    color: #0F172A;
    min-height: 60px;
}
QLineEdit#TerminalScan:focus {
    border: 2px solid #3B82F6;
    background: #FFFFFF;
}
QFrame#CajaResumen {
    background: transparent;
    border: none;
}
QFrame#FilaResumen {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}
QFrame#FilaResumen QLabel[tipo="titulo"] {
    color: #64748B;
    font-weight: 800;
    font-size: 12px;
    border: none;
    background: transparent;
}
QFrame#FilaResumen QLabel[tipo="valor"] {
    color: #0F172A;
    font-weight: 900;
    font-size: 13px;
    border: none;
    background: transparent;
}
QFrame#FilaResumen QLabel#TituloCambio { color: #EF4444; }
QFrame#FilaResumen QLabel[tipo="valor"][resaltado="true"] {
    color: #059669;
    font-size: 14px;
}
QLabel#TotalGrande {
    background-color: #FFFFFF;
    color: #16A34A;
    border: 2px solid #DCFCE7;
    border-radius: 12px;
    font-size: 52px;
    font-weight: 900;
    padding: 6px 28px;
}
"""
