import codecs
import re

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

# 1. Fix procesar_click_metodo
pattern1 = r'def procesar_click_metodo\(self, key\):\s*self\.stack\.setCurrentIndex\(1\).*?self\.txt_pago\.setFocus\(\)'
repl1 = '''def procesar_click_metodo(self, key):
        if key not in ("Mixto", "Fiado", "Clientes"):
            # Solo los métodos simples (Efectivo, Tarjeta, QR) pasan a la Pantalla 1
            self.stack.setCurrentIndex(1)
            self.txt_pago.setFocus()'''
code = re.sub(pattern1, repl1, code, flags=re.DOTALL)

# 2. Fix finalizar early return
pattern2 = r'def finalizar\(self, imprimir=True, force_fiscal=False\):\s*if getattr\(self, \'stack\', None\) and self\.stack\.currentIndex\(\) == 0:\s*return'
repl2 = '''def finalizar(self, imprimir=True, force_fiscal=False):
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0:
            if self.current_metodo not in ("Mixto", "Fiado", "Clientes"):
                return'''
code = re.sub(pattern2, repl2, code, flags=re.DOTALL)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Fixed using regex!")
