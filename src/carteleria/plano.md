# Plano Cartelería


## Arquitectura de Layouts (Vistas Dinámicas)
La vista HTML de TV (la_cara_web) responde a un atributo global en <body> llamado data-wall.
Al mutar este atributo (ej. vía **F9** en pp.js), ase.css modifica el grid-template-columns para transicionar fluidamente entre vistas de 1, 2, 3 o 4 columnas en el centro del display, sin tocar los bordes promocionales (Zócalo / Hero).

## Ciclo de vida Teclado/Monitor
- El cajero pulsa **F10** en la terminal principal -> Interceptado por main_window.py -> Manda el cajero al monitor secundario y entra en fullscreen (o lo devuelve).
- Dentro de la TV (con Kiosk enfocado), **F10** llama al controlador backend para un conmutado de monitor nativo, o **F9** cicla internamente el layout del DOM.
