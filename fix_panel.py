import os

file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. In activar_cobranza, save _deuda_actual
old_activar = '''    def activar_cobranza(self, monto_sugerido, deuda_actual):
        self._modo = "cobranza"
        nombre = getattr(self, "_cliente_nombre", "Cliente")
        self.estado.setText(f"Hola {nombre}")'''
new_activar = '''    def activar_cobranza(self, monto_sugerido, deuda_actual):
        self._modo = "cobranza"
        self._deuda_actual = deuda_actual
        nombre = getattr(self, "_cliente_nombre", "Cliente")
        self.estado.setText(f"Hola {nombre}")'''
text = text.replace(old_activar, new_activar)

# 2. Add actualizar_monto
import re
text = text + '''
    def actualizar_monto(self, nuevo_monto_venta):
        self._monto = nuevo_monto_venta
        if getattr(self, "_modo", "") in ("cobranza", "cobrando_lienzo"):
            deuda = getattr(self, "_deuda_actual", 0.0)
            monto_sugerido = nuevo_monto_venta + deuda
            self.detalle.setText(f"Saldo anterior: ${deuda:,.2f}\\nVenta actual: ${self._monto:,.2f}")
            if getattr(self, "_modo", "") == "cobranza":
                self.txt_monto_abono.setText(f"{monto_sugerido:.2f}".replace('.', ','))
'''

# 3. Remove hide() for estado and detalle
old_iniciar = '''        self._modo = "cobrando_lienzo"
        self.estado.hide()
        self.detalle.hide()'''
new_iniciar = '''        self._modo = "cobrando_lienzo"
        # Mantenemos estado y detalle visibles como pidio el usuario'''
text = text.replace(old_iniciar, new_iniciar)

# 4. Remove show() for estado and detalle since they were never hidden
old_volver = '''    def _volver_de_lienzo(self):
        self._modo = "cobranza"
        self._cerrar_lienzos()
        self.estado.show()
        self.detalle.show()'''
new_volver = '''    def _volver_de_lienzo(self):
        self._modo = "cobranza"
        self._cerrar_lienzos()'''
text = text.replace(old_volver, new_volver)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
