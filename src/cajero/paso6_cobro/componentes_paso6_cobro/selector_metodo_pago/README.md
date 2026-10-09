# Selector de método

Tres tarjetas arriba y dos abajo. Las flechas marcan, no cobran.

La punta de esta rama es `punta del piramide.md`.

## Optimización Visual
Al usar las flechas del teclado, `marcar_tarjeta` (en `marco/marcar.py`) implementa un sistema de caché de memoria para las imágenes (`pix_activa`, `pix_inactiva`) y esquiva la reescritura visual de aquellas tarjetas que no cambiaron de estado. Esto evita leer de disco la imagen PNG en cada milisegundo de navegación, resolviendo cuellos de botella ("trabas") de interfaz al navegar rápido entre opciones de cobro.
