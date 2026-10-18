# Columna 3

Qué hace: arma los slides de «¿Llevás…?» y los intercala con ofertas relámpago.

Qué función: `armar_columna3` en `armar.py`. El relleno por rubro es `cruzadas_desde_catalogo`.

Cómo funciona: primero `VentaCruzadaInteligente.armar_slides` (mismo ticket). Si no hay ningún ticket, completa con productos del mismo rubro. Las ofertas salen de `_ofertas_flash`. Si el motor falla, no inventa pares cuando ya hubo ventas: la columna queda solo con ofertas, o vacía.

Qué no debe cambiar: `estado_tv.armar_columna3` sigue siendo el nombre que llama `armar_paneles`. No usar el rubro si ya hay tickets.
