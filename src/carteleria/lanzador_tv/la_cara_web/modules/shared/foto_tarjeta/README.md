# Foto de tarjeta

Qué hace: arma el recuadro PNG de la TV, precarga lo visible y no deja el hueco vacío.

Qué función:
- `urlsFotoProducto` / `urlIcono` / `FOTO_SISTEMA` en `urls.js`
- `revelarFoto` / `revelarFotosEn` en `revelar.js`
- `precargarFotosEstado` en `precargar.js`
- `htmlDealStage` en `stage.js`

Cómo funciona: el JSON trae `icono_url` (`/iconos/asado.png`). `precargarFotosEstado` pide hasta 24 PNG de hero, ranking, col 3/4. `htmlDealStage` pinta `<img>` + letra. Hasta `.is-ready` la letra tapa; al `load` se muestra el PNG. Si el archivo mide menos de 360 px de ancho, pone `is-chica` para agrandarlo en el ranking. Si falla, prueba fallbacks y luego `assets/logo_sistema.svg`.

Qué devuelve cuando falla: logo de sistema; la clase `is-ready` igual, para no dejar el recuadro en blanco.

Qué no debe cambiar: el nombre canónico `asado.png`. Las filas de precio (`fila_precio.js`) no usan esta carpeta. No tocar cajero ni `qt_dpi`.
