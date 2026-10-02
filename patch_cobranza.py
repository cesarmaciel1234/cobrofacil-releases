import re
with open('src/cajero/paso6_cobro/fiado_en_cobro/cobranza.py', 'r', encoding='utf8') as f:
    text = f.read()

text = text.replace(
    'from src.cajero.ingresar_efectivo import DialogoIngresoEfectivo',
    'from src.cajero.paso6_cobro.fiado_en_cobro.nativo import DialogoAbonoNativo'
)
text = text.replace(
    'dlg = DialogoIngresoEfectivo(parent=parent)\n    dlg.abrir_para_cliente(cliente, monto_sugerido)',
    'dlg = DialogoAbonoNativo(cliente, monto_sugerido, parent=parent)'
)

with open('src/cajero/paso6_cobro/fiado_en_cobro/cobranza.py', 'w', encoding='utf8') as f:
    f.write(text)
print('Patched cobranza.py')