import codecs
import re

path = 'src/cajero/paso6_cobro/componentes_paso6_cobro/selector_metodo_pago.py'
with codecs.open(path, 'r', 'utf-8') as f:
    code = f.read()

pattern = r'self\.metodos = \[.*?\]'
replacement = '''self.metodos = [
            ("💰", "Efectivo", "Efectivo"), 
            ("💳", "Crédito", "Tarjeta"), 
            ("🏦", "Transf.", "Transferencia"),
            ("📱", "QR", "QR"),
            ("🔀", "Mixto", "Mixto")
        ]'''

code = re.sub(pattern, replacement, code, flags=re.DOTALL)

code = code.replace('if col > 3:', 'if col > 4:')

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Selector cleaned!")
