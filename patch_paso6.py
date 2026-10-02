import re
with open('src/cajero/paso6_cobro/paso6_cobro.py', 'r', encoding='utf8') as f:
    text = f.read()

text = text.replace(
    'hoja._abrir_dialogo_cobranza(monto_sugerido)',
    'self.panel_fiado.activar_cobranza(monto_sugerido, deuda_actual)'
)

with open('src/cajero/paso6_cobro/paso6_cobro.py', 'w', encoding='utf8') as f:
    f.write(text)