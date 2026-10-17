# Paneles

Qué hace: arma rotación, destacados y columnas en un hilo Qt.

Qué función: `PanelesWorker.run`, `PanelesMixin._refrescar_paneles`.

Cómo funciona: `enriquecer_iconos` + `armar_paneles`. Si falla o no hay rotación, `paneles_fallback` con los mismos precios. Publica `/api/state` enseguida (precios) y otra vez cuando el hilo termina.

Qué no debe cambiar: no emitir `{}` si hay productos.
