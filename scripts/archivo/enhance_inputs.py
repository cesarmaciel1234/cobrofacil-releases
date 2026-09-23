import codecs
import re

paths = ['src/ui_components/estilo_dia.qss', 'src/ui_components/estilo_noche.qss']

for path in paths:
    with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
        code = f.read()

    # Premium InputPago
    pattern_pago = r'QFrame#Paso6Main\[theme="[^"]*"\] QLineEdit#InputPago \{.*?\}'
    
    if 'dia' in path:
        replacement = '''QFrame#Paso6Main[theme="light"] QLineEdit#InputPago {
    background-color: #F8FAFC !important;
    border: 2px solid #E2E8F0 !important;
    border-radius: 20px !important;
    padding: 15px 20px !important;
    font-size: 38px !important;
    font-weight: 900 !important;
    color: #0F172A !important;
    font-family: 'Segoe UI', sans-serif !important;
    selection-background-color: #3B82F6 !important;
}

QFrame#Paso6Main[theme="light"] QLineEdit#InputPago:focus {
    background-color: #FFFFFF !important;
    border: 3px solid #3B82F6 !important;
    color: #1E3A8A !important;
}'''
    else:
        replacement = '''QFrame#Paso6Main[theme="dark"] QLineEdit#InputPago {
    background-color: #0F172A !important;
    border: 2px solid #334155 !important;
    border-radius: 20px !important;
    padding: 15px 20px !important;
    font-size: 38px !important;
    font-weight: 900 !important;
    color: #F8FAFC !important;
    font-family: 'Segoe UI', sans-serif !important;
    selection-background-color: #3B82F6 !important;
}

QFrame#Paso6Main[theme="dark"] QLineEdit#InputPago:focus {
    background-color: #1E293B !important;
    border: 3px solid #3B82F6 !important;
    color: #60A5FA !important;
}'''

    # Since the file might have multiple declarations or overriding ones at the bottom, we should replace ALL of them
    code = re.sub(pattern_pago, replacement, code, flags=re.DOTALL)
    
    # Let's also remove any other rogue InputPago:focus blocks just in case
    code = re.sub(r'QFrame#Paso6Main\[theme="[^"]*"\] QLineEdit#InputPago:focus\s*\{.*?\}', '', code, flags=re.DOTALL)

    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)

print("Inputs upgraded!")
