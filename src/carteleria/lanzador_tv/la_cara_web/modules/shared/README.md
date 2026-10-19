# Shared cara TV

Qué hace: piezas que usan varias columnas.

Qué función:
- `plata_y_texto.js` — nombre, `$`, oferta, `escapeHtml`
- `foto_tarjeta/` — PNG de tarjeta
- `precio_tv.js` — bloque de precio
- `cinta_infinita.js` / `publicidad_tv.js` / `vfx.js`
- `plantilla.js` — guarda la forma pintada y la vuelve a mostrar al abrir, antes del dato vivo

Cómo funciona: las columnas importan; no hay estado global acá.

Qué no debe cambiar: no volver a meter la foto dentro de `plata_y_texto.js`.
