with open('src/cajero/paso6_cobro/fiado_en_cobro/README.md', 'r', encoding='utf8') as f:
    text = f.read()

text = text.replace(
    'El motor abre el Centro de Cobranza (F6) directamente en ese cliente',
    'El sistema ahora abre una interfaz nativa exclusiva para el Paso 6 (DialogoAbonoNativo en nativo.py)'
)
text = text.replace(
    'El motor de cobranza (DialogoIngresoEfectivo) maneja su propio asentamiento de pagos.',
    'El dialogo nativo (DialogoAbonoNativo) delega el asentamiento al motor de pagos de Fiado (asentar, puerta.py).'
)

with open('src/cajero/paso6_cobro/fiado_en_cobro/README.md', 'w', encoding='utf8') as f:
    f.write(text)