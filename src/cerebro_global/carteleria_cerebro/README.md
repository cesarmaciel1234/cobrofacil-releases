# Cartelería en la maestra

`sincronizador_carteleria` lee `productos` y reescribe `carteleria_global` para la grilla de precios. Corre solo en el proceso `--server` de la maestra, cada 30 segundos.

Si la grilla no cambió, no vuelve a borrarla. Si cambió, la deja escrita y `repartir_desde_maestra` avisa a teles y esclavas. La esclava no usa esta clase: un `DELETE` desde ahí pisaría la grilla de la tienda.
