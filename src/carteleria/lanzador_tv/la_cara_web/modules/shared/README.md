# Shared cara TV

Qué hace: piezas que usan varias columnas.

Qué función:
- `plata_y_texto.js` — nombre, `$`, oferta, `escapeHtml`
- `foto_tarjeta/` — PNG de tarjeta
- `precio_tv.js` — bloque de precio
- `cinta_infinita.js` / `publicidad_tv.js` / `vfx.js`

Cómo funciona: las columnas importan; no hay estado global acá.

Qué no debe cambiar: no volver a meter la foto dentro de `plata_y_texto.js`.
