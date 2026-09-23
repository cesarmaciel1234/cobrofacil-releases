ESTILO_BARRA = """
QFrame#PanelTotales {
    background: #FFFFFF;
    border: none; border-top: 2px solid #E2E8F0;
    border-radius: 0px;
}
QLineEdit#TerminalScan {
    background: #FFFFFF;
    border: 2px solid #475569;
    border-radius: 16px;
    padding: 12px 20px;
    font-size: 22px;
    font-weight: 800;
    color: #0F172A;
    min-height: 0px;
}
QLineEdit#TerminalScan:focus {
    border: 2px solid #15293C;
    background: #FFFFFF;
}
QFrame#CajaResumen {
    background: #FFFFFF;
    border: 2px solid #475569;
    border-radius: 14px;
}
QFrame#FilaResumen {
    background: transparent;
    border: none;
    border-bottom: 1px solid #E2E8F0;
}
QFrame#FilaResumen QLabel[tipo="titulo"] {
    color: #475569;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.4px;
    border: none;
    background: transparent;
}
QFrame#FilaResumen QLabel[tipo="valor"] {
    color: #0F172A;
    font-weight: 800;
    font-size: 15px;
    border: none;
    background: transparent;
}
QFrame#FilaResumen QLabel#TituloCambio { color: #EF4444; }
QFrame#FilaResumen QLabel[tipo="valor"][resaltado="true"] {
    color: #15803D;
    font-size: 15px;
    font-weight: 800;
}
QLabel#TotalGrande {
    background: transparent;
    color: #15803D;
    border: none;
    padding: 0 8px;
}
"""
