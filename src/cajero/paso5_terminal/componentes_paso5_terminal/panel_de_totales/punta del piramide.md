# Punta de la pirámide — panel de totales

La barra de abajo del cajero. Cada bloque es un contenedor propio. Esta carpeta es la punta: arma la barra y no calcula el cobro.

```
panel_de_totales/
  punta del piramide.md
  panel.py                 arma la barra
  estilos.py               colores de la barra en reposo
  entrada_codigo/          buscador F1
  total_grande/            importe verde
  ahorro_banner/           "AHORRAS" naranja
  resumen/                 caja de la derecha
    fila.py                contenedor de una fila
    articulos.py
    total.py
    ahorro.py
    pagos.py
    cambio.py
```

- El terminal sigue leyendo los mismos nombres: `entrada_codigo`, `etiqueta_total_grande`, `etiqueta_ahorro`, `titulo_*`, `valor_*`.
- Ahorro del resumen nace oculto. Se muestra solo si hay descuento.
- Cambio en rojo. Si el vuelto se resalta, el valor pasa a verde.
- El marco verde o rojo de un cobro no se define acá. Está en `apariencia/aviso`.
