# Widgets de la cara (legado)

Qué hace: reloj, datos de negocio e indicador de red pensados para la TV PyQt vieja.

Qué función: `reloj_widget.py`, `info_negocio.py`, `indicador_red_widget.py`.

Cómo funciona: no es la pantalla Admin → Configuración. Esa está en `../configuracion/`. Estos widgets no hablan con MariaDB.

Qué no debe cambiar: no mezclarlos con `configuracion/panel.py`. No usarlos para guardar tema.
