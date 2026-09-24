# Aviso en la pantalla de cobro

Cartel grande sobre la hoja. No abre una ventana y no hay que apretar OK.

`toast.py`, clase `AvisoCobro`. `mostrar(mensaje)` lo pinta sobre la fila de redondeo y a los pocos segundos se va solo. El mouse lo atraviesa: el cajero sigue escribiendo.

Lo usa el efectivo si cobran sin monto, el mixto si cargan un tercer medio, y la tarjeta si la terminal no toma el importe.
