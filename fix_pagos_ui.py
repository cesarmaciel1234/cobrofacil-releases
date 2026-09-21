import codecs
import re

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

# 1. Fix procesar_click_metodo
from_procesar = '''    def procesar_click_metodo(self, key):
        self.stack.setCurrentIndex(1)
        # Dar foco al campo de pago al entrar a la página 1
        self.txt_pago.setFocus()
        
        if key == "Clientes":
            self._activar_cliente_express()
            return
        elif key == "Fiado":
            self._activar_fiado_express()
            return
        else:
            self.set_metodo(key)'''

to_procesar = '''    def procesar_click_metodo(self, key):
        if key not in ("Mixto", "Fiado", "Clientes"):
            # Solo los métodos simples (Efectivo, Tarjeta, QR) pasan a la Pantalla 1
            self.stack.setCurrentIndex(1)
            self.txt_pago.setFocus()
            
        if key == "Clientes":
            self._activar_cliente_express()
            return
        elif key == "Fiado":
            self._activar_fiado_express()
            return
        else:
            self.set_metodo(key)'''
code = code.replace(from_procesar, to_procesar)

# 2. Fix finalizar early return
from_finalizar = '''    def finalizar(self, imprimir=True, force_fiscal=False):
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0:
            return'''
to_finalizar = '''    def finalizar(self, imprimir=True, force_fiscal=False):
        if getattr(self, 'stack', None) and self.stack.currentIndex() == 0:
            # Permitir finalizar desde la pantalla 0 si es un método con popup propio
            if self.current_metodo not in ("Mixto", "Fiado", "Clientes"):
                return'''
code = code.replace(from_finalizar, to_finalizar)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("UI state leakage fixed!")
